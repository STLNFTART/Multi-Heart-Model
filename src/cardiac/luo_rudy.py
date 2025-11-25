"""
Luo-Rudy Dynamic (LRd) Cardiac Ventricular Model

The Luo-Rudy Dynamic model is one of the most comprehensive cardiac action
potential models, incorporating detailed ionic mechanisms for guinea pig
ventricular myocytes.

References:
- Luo, C. H., & Rudy, Y. (1994). "A dynamic model of the cardiac ventricular
  action potential. I. Simulations of ionic currents and concentration changes."
  Circulation Research, 74(6), 1071-1096.

- Luo, C. H., & Rudy, Y. (1994). "A dynamic model of the cardiac ventricular
  action potential. II. Afterdepolarizations, triggered activity, and
  potentiation." Circulation Research, 74(6), 1097-1113.

This implementation includes:
- Fast sodium current (INa)
- L-type calcium current (ICaL)
- Time-dependent potassium current (IK)
- Time-independent potassium current (IK1)
- Plateau potassium current (IKp)
- Background currents
- Sodium-potassium pump
- Sodium-calcium exchanger
- Intracellular calcium dynamics
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class LuoRudyParameters:
    """
    Parameters for Luo-Rudy Dynamic model

    All parameters from original 1994 paper
    """
    # Cell geometry (guinea pig ventricular myocyte)
    cell_capacitance: float = 1.0  # μF/cm²
    cell_volume: float = 38000.0  # μm³

    # Reversal potentials
    R: float = 8314.0  # Gas constant (J/kmol/K)
    T: float = 310.0  # Temperature (K)
    F: float = 96485.0  # Faraday constant (C/mol)

    # External concentrations (mM)
    Na_o: float = 140.0  # Extracellular sodium
    K_o: float = 5.4  # Extracellular potassium
    Ca_o: float = 1.8  # Extracellular calcium

    # Maximum conductances
    g_Na: float = 16.0  # Fast sodium (mS/μF)
    g_Ca: float = 0.09  # L-type calcium (mS/μF)
    g_K: float = 0.282  # Time-dependent K+ (mS/μF)
    g_K1: float = 0.6047  # Inward rectifier K+ (mS/μF)
    g_Kp: float = 0.0183  # Plateau K+ (mS/μF)
    g_b_Na: float = 0.0006  # Background Na+ (mS/μF)
    g_b_Ca: float = 0.001  # Background Ca2+ (mS/μF)

    # Pump and exchanger parameters
    I_NaK_max: float = 0.693  # Na-K pump max current (μA/μF)
    K_m_Na: float = 10.0  # Na-K pump Na affinity (mM)
    K_m_K: float = 1.5  # Na-K pump K affinity (mM)
    k_NaCa: float = 2000.0  # Na-Ca exchanger (μA/μF)
    K_mNa: float = 87.5  # Na-Ca exchanger Na affinity (mM)
    K_mCa: float = 1.38  # Na-Ca exchanger Ca affinity (mM)
    k_sat: float = 0.1  # Na-Ca exchanger saturation
    gamma: float = 0.35  # Na-Ca exchanger voltage dependence

    # Calcium dynamics
    Ca_up_max: float = 0.0005  # SR Ca uptake max (mM/ms)
    K_up: float = 0.00092  # SR Ca uptake affinity (mM)
    Ca_rel_max: float = 0.18  # SR Ca release max (mM/ms)

    # Buffering
    CMDN_max: float = 0.05  # Calmodulin max (mM)
    TRPN_max: float = 0.07  # Troponin max (mM)
    CSQN_max: float = 10.0  # Calsequestrin max (mM)
    K_mCMDN: float = 0.00238  # Calmodulin affinity (mM)
    K_mTRPN: float = 0.0005  # Troponin affinity (mM)
    K_mCSQN: float = 0.8  # Calsequestrin affinity (mM)


class LuoRudyModel:
    """
    Luo-Rudy Dynamic cardiac action potential model

    State variables (8):
    0: V - Membrane voltage (mV)
    1: m - Fast Na activation gate
    2: h - Fast Na inactivation gate
    3: j - Fast Na slow inactivation gate
    4: d - L-type Ca activation gate
    5: f - L-type Ca inactivation gate
    6: X - Delayed rectifier K+ activation gate
    7: Ca_i - Intracellular Ca2+ concentration (mM)

    Extended state (11 total):
    8: Ca_up - SR Ca2+ concentration (mM)
    9: Na_i - Intracellular Na+ concentration (mM)
    10: K_i - Intracellular K+ concentration (mM)

    Example usage:
        >>> model = LuoRudyModel()
        >>> state = model.get_initial_state()
        >>>
        >>> # Simulate action potential
        >>> t = 0.0
        >>> dt = 0.01  # ms
        >>> for step in range(30000):  # 300 ms
        ...     state = model.step(t, state, dt, stimulus=0.0)
        ...     t += dt
        >>>
        >>> # Apply stimulus
        >>> state = model.step(t, state, dt, stimulus=-80.0)  # μA/μF
    """

    def __init__(self, params: Optional[LuoRudyParameters] = None):
        self.params = params if params is not None else LuoRudyParameters()

    def get_initial_state(self) -> np.ndarray:
        """
        Get physiological resting state

        Returns:
            State vector [V, m, h, j, d, f, X, Ca_i, Ca_up, Na_i, K_i]
        """
        return np.array([
            -84.7,  # V (mV) - resting potential
            0.0011,  # m
            0.9825,  # h
            0.9750,  # j
            0.000003,  # d
            1.0,  # f
            0.0001,  # X
            0.0002,  # Ca_i (mM)
            2.0,  # Ca_up (mM)
            10.0,  # Na_i (mM)
            145.0,  # K_i (mM)
        ])

    def derivatives(
        self,
        t: float,
        state: np.ndarray,
        stimulus: float = 0.0
    ) -> np.ndarray:
        """
        Compute state derivatives

        Args:
            t: Time (ms)
            state: State vector
            stimulus: External stimulus current (μA/μF, negative for depolarization)

        Returns:
            Derivative vector dstate/dt
        """
        # Unpack state
        V, m, h, j, d, f, X, Ca_i, Ca_up, Na_i, K_i = state

        p = self.params

        # Reversal potentials
        E_Na = (p.R * p.T / p.F) * np.log(p.Na_o / Na_i)
        E_K = (p.R * p.T / p.F) * np.log(p.K_o / K_i)
        E_Ca = (p.R * p.T / (2 * p.F)) * np.log(p.Ca_o / Ca_i)

        # === Fast Sodium Current (INa) ===
        I_Na = p.g_Na * m**3 * h * j * (V - E_Na)

        # m gate (activation)
        alpha_m = 0.32 * (V + 47.13) / (1 - np.exp(-0.1 * (V + 47.13)))
        beta_m = 0.08 * np.exp(-V / 11.0)
        dm_dt = alpha_m * (1 - m) - beta_m * m

        # h gate (fast inactivation)
        if V < -40:
            alpha_h = 0.135 * np.exp(-(V + 80) / 6.8)
            beta_h = 3.56 * np.exp(0.079 * V) + 3.1e5 * np.exp(0.35 * V)
        else:
            alpha_h = 0
            beta_h = 1.0 / (0.13 * (1 + np.exp(-(V + 10.66) / 11.1)))
        dh_dt = alpha_h * (1 - h) - beta_h * h

        # j gate (slow inactivation)
        if V < -40:
            alpha_j = (-1.2714e5 * np.exp(0.2444 * V) - 3.474e-5 * np.exp(-0.04391 * V)) * \
                      (V + 37.78) / (1 + np.exp(0.311 * (V + 79.23)))
            beta_j = 0.1212 * np.exp(-0.01052 * V) / (1 + np.exp(-0.1378 * (V + 40.14)))
        else:
            alpha_j = 0
            beta_j = 0.3 * np.exp(-2.535e-7 * V) / (1 + np.exp(-0.1 * (V + 32)))
        dj_dt = alpha_j * (1 - j) - beta_j * j

        # === L-type Calcium Current (ICaL) ===
        I_CaL = p.g_Ca * d * f * (V - 65)  # Simplified

        # d gate (activation)
        alpha_d = 0.095 * np.exp(-0.01 * (V - 5)) / (1 + np.exp(-0.072 * (V - 5)))
        beta_d = 0.07 * np.exp(-0.017 * (V + 44)) / (1 + np.exp(0.05 * (V + 44)))
        dd_dt = alpha_d * (1 - d) - beta_d * d

        # f gate (inactivation)
        alpha_f = 0.012 * np.exp(-0.008 * (V + 28)) / (1 + np.exp(0.15 * (V + 28)))
        beta_f = 0.0065 * np.exp(-0.02 * (V + 30)) / (1 + np.exp(-0.2 * (V + 30)))
        df_dt = alpha_f * (1 - f) - beta_f * f

        # === Time-Dependent Potassium Current (IK) ===
        Xi = np.where(V < -100, 1.0, 2.837 * (np.exp(0.04 * (V + 77)) - 1) / ((V + 77) * np.exp(0.04 * (V + 35))))
        I_K = p.g_K * X * Xi * (V - E_K)

        # X gate
        alpha_X = 0.0005 * np.exp(0.083 * (V + 50)) / (1 + np.exp(0.057 * (V + 50)))
        beta_X = 0.0013 * np.exp(-0.06 * (V + 20)) / (1 + np.exp(-0.04 * (V + 20)))
        dX_dt = alpha_X * (1 - X) - beta_X * X

        # === Inward Rectifier Potassium Current (IK1) ===
        alpha_K1 = 1.02 / (1 + np.exp(0.2385 * (V - E_K - 59.215)))
        beta_K1 = (0.49124 * np.exp(0.08032 * (V - E_K + 5.476)) + \
                   np.exp(0.06175 * (V - E_K - 594.31))) / \
                  (1 + np.exp(-0.5143 * (V - E_K + 4.753)))
        K1_inf = alpha_K1 / (alpha_K1 + beta_K1)
        I_K1 = p.g_K1 * K1_inf * (V - E_K)

        # === Plateau Potassium Current (IKp) ===
        Kp = 1.0 / (1 + np.exp((7.488 - V) / 5.98))
        I_Kp = p.g_Kp * Kp * (V - E_K)

        # === Background Currents ===
        I_b_Na = p.g_b_Na * (V - E_Na)
        I_b_Ca = p.g_b_Ca * (V - E_Ca)

        # === Sodium-Potassium Pump ===
        f_NaK = 1.0 / (1 + 0.1245 * np.exp(-0.1 * V * p.F / (p.R * p.T)) + \
                       0.0365 * np.exp(-V * p.F / (p.R * p.T)))
        I_NaK = p.I_NaK_max * f_NaK * (p.K_o / (p.K_o + p.K_m_K)) * \
                (Na_i / (Na_i + p.K_m_Na))

        # === Sodium-Calcium Exchanger ===
        I_NaCa = p.k_NaCa * (np.exp(p.gamma * V * p.F / (p.R * p.T)) * Na_i**3 * p.Ca_o - \
                              np.exp((p.gamma - 1) * V * p.F / (p.R * p.T)) * p.Na_o**3 * Ca_i) / \
                 ((p.K_mNa**3 + p.Na_o**3) * (p.K_mCa + p.Ca_o) * \
                  (1 + p.k_sat * np.exp((p.gamma - 1) * V * p.F / (p.R * p.T))))

        # === Calcium Dynamics ===
        # SR uptake
        I_up = p.Ca_up_max * Ca_i / (Ca_i + p.K_up)

        # SR release (simplified - full model includes CICR)
        I_rel = p.Ca_rel_max * d * f * (Ca_up - Ca_i)

        # Buffering
        CMDN = p.CMDN_max * Ca_i / (Ca_i + p.K_mCMDN)
        TRPN = p.TRPN_max * Ca_i / (Ca_i + p.K_mTRPN)
        beta_i = 1.0 / (1 + CMDN + TRPN)

        # Calcium concentration change
        dCa_i_dt = beta_i * (I_rel - I_up - (I_CaL + I_b_Ca - 2 * I_NaCa) / (2 * p.F * p.cell_volume))

        # SR calcium
        dCa_up_dt = I_up - I_rel

        # === Ion Concentration Changes ===
        dNa_i_dt = -(I_Na + I_b_Na + 3 * I_NaK + 3 * I_NaCa) / (p.F * p.cell_volume)
        dK_i_dt = -(I_K + I_K1 + I_Kp - 2 * I_NaK + stimulus) / (p.F * p.cell_volume)

        # === Membrane Voltage ===
        I_total = I_Na + I_CaL + I_K + I_K1 + I_Kp + I_b_Na + I_b_Ca + I_NaK + I_NaCa
        dV_dt = -(I_total + stimulus) / p.cell_capacitance

        return np.array([dV_dt, dm_dt, dh_dt, dj_dt, dd_dt, df_dt, dX_dt,
                        dCa_i_dt, dCa_up_dt, dNa_i_dt, dK_i_dt])

    def step(
        self,
        t: float,
        state: np.ndarray,
        dt: float,
        stimulus: float = 0.0
    ) -> np.ndarray:
        """
        Forward Euler integration step

        Args:
            t: Current time (ms)
            state: Current state
            dt: Time step (ms)
            stimulus: Stimulus current (μA/μF)

        Returns:
            New state at t + dt
        """
        derivs = self.derivatives(t, state, stimulus)
        return state + dt * derivs

    def get_action_potential_duration(
        self,
        state_trajectory: list,
        times: np.ndarray,
        repol_percent: float = 90.0
    ) -> Optional[float]:
        """
        Calculate action potential duration

        Args:
            state_trajectory: List of state vectors
            times: Time points
            repol_percent: Repolarization percentage (90 for APD90)

        Returns:
            APD in ms, or None if not found
        """
        voltages = np.array([s[0] for s in state_trajectory])

        # Find peak
        peak_idx = np.argmax(voltages)
        if peak_idx == 0 or peak_idx == len(voltages) - 1:
            return None

        V_rest = voltages[0]
        V_peak = voltages[peak_idx]
        V_target = V_rest + (V_peak - V_rest) * (1 - repol_percent / 100.0)

        # Find repolarization time
        for i in range(peak_idx, len(voltages)):
            if voltages[i] <= V_target:
                return times[i] - times[0]

        return None


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("Luo-Rudy Dynamic Cardiac Action Potential Model")
    print("=" * 60)

    model = LuoRudyModel()
    state = model.get_initial_state()

    print(f"\nInitial state:")
    print(f"  V = {state[0]:.1f} mV")
    print(f"  Ca_i = {state[7]:.6f} mM")
    print(f"  Na_i = {state[9]:.1f} mM")
    print(f"  K_i = {state[10]:.1f} mM")

    # Simulate action potential
    print("\nSimulating action potential...")
    t = 0.0
    dt = 0.01  # ms
    duration = 400.0  # ms

    trajectory = []
    times = []

    for step in range(int(duration / dt)):
        # Apply stimulus at t=10ms for 1ms
        stim = -80.0 if (10 <= t < 11) else 0.0

        state = model.step(t, state, dt, stimulus=stim)

        if step % 100 == 0:  # Record every 1ms
            trajectory.append(state.copy())
            times.append(t)

        t += dt

    # Analyze results
    voltages = np.array([s[0] for s in trajectory])
    calcium = np.array([s[7] for s in trajectory])

    print(f"\nAction potential characteristics:")
    print(f"  Peak voltage: {np.max(voltages):.1f} mV")
    print(f"  Resting potential: {voltages[0]:.1f} mV")
    print(f"  Peak Ca2+: {np.max(calcium):.6f} mM")
    print(f"  Diastolic Ca2+: {calcium[0]:.6f} mM")

    # Calculate APD90
    apd90 = model.get_action_potential_duration(trajectory, np.array(times), 90.0)
    if apd90:
        print(f"  APD90: {apd90:.1f} ms")

    print("\n" + "=" * 60)
    print("Luo-Rudy model demonstration complete!")
    print("=" * 60)
