"""
Ten Tusscher-Panfilov 2006 Human Ventricular Model

Modern human ventricular action potential model with detailed ionic currents.
One of the most widely used models for human cardiac electrophysiology.

References:
- ten Tusscher, K. H., & Panfilov, A. V. (2006). "Alternans and spiral breakup
  in a human ventricular tissue model." American Journal of Physiology-Heart
  and Circulatory Physiology, 291(3), H1088-H1100.

- ten Tusscher, K. H., Noble, D., Noble, P. J., & Panfilov, A. V. (2004).
  "A model for human ventricular tissue." American Journal of Physiology-Heart
  and Circulatory Physiology, 286(4), H1573-H1589.

Features:
- 17 state variables
- Detailed ionic currents (INa, ICaL, IKr, IKs, IK1, Ito, etc.)
- Calcium dynamics with SR
- Suitable for arrhythmia studies
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class TenTusscherParameters:
    """Parameters for Ten Tusscher-Panfilov 2006 model"""

    # Physical constants
    R: float = 8314.472  # Gas constant (J/kmol/K)
    T: float = 310.0  # Temperature (K)
    F: float = 96485.3415  # Faraday constant (C/mol)

    # Cell geometry
    V_c: float = 0.016404  # Cytoplasmic volume (μm³)
    V_sr: float = 0.001094  # SR volume (μm³)

    # Capacitance
    C_m: float = 0.185  # Cell capacitance (μF)

    # External concentrations (mM)
    Na_o: float = 140.0
    K_o: float = 5.4
    Ca_o: float = 2.0

    # Cell type (0=endo, 1=epi, 2=M cell)
    cell_type: int = 0  # Endocardial by default


class TenTusscherModel:
    """
    Ten Tusscher-Panfilov 2006 human ventricular model

    State variables (17):
    0: V - Membrane potential (mV)
    1: m - Fast Na+ activation
    2: h - Fast Na+ fast inactivation
    3: j - Fast Na+ slow inactivation
    4: r - Ito activation
    5: s - Ito inactivation
    6: d - ICaL activation
    7: f - ICaL voltage-dependent inactivation
    8: f2 - ICaL calcium-dependent inactivation
    9: fCass - ICaL calcium-dependent inactivation (subspace)
    10: xr1 - IKr activation
    11: xr2 - IKr inactivation
    12: xs - IKs activation
    13: Ca_i - Intracellular Ca2+ (mM)
    14: Ca_sr - SR Ca2+ (mM)
    15: Ca_ss - Subspace Ca2+ (mM)
    16: Na_i - Intracellular Na+ (mM)
    17: K_i - Intracellular K+ (mM)

    Example:
        >>> model = TenTusscherModel()
        >>> state = model.get_initial_state()
        >>> state = model.step(0.0, state, 0.01, stimulus=-52.0)
    """

    def __init__(self, params: Optional[TenTusscherParameters] = None):
        self.params = params if params is not None else TenTusscherParameters()
        self._setup_conductances()

    def _setup_conductances(self):
        """Setup conductances based on cell type"""
        p = self.params

        # Adjust for cell type
        if p.cell_type == 0:  # Endocardial
            self.g_to = 0.073
        elif p.cell_type == 1:  # Epicardial
            self.g_to = 0.294
        else:  # M cell
            self.g_to = 0.073

        # Standard conductances
        self.g_Na = 14.838  # Fast sodium (nS/pF)
        self.g_CaL = 0.0000398  # L-type calcium (cm³/μF/ms)
        self.g_Kr = 0.153  # Rapid delayed rectifier (nS/pF)
        self.g_Ks = 0.392  # Slow delayed rectifier (nS/pF)
        self.g_K1 = 5.405  # Inward rectifier (nS/pF)
        self.g_bNa = 0.00029  # Background Na (nS/pF)
        self.g_bCa = 0.000592  # Background Ca (nS/pF)
        self.p_KNa = 0.03  # Na/K permeability ratio

    def get_initial_state(self) -> np.ndarray:
        """Get resting state"""
        return np.array([
            -86.2,  # V
            0.0,    # m
            0.75,   # h
            0.75,   # j
            0.0,    # r
            1.0,    # s
            0.0,    # d
            1.0,    # f
            1.0,    # f2
            1.0,    # fCass
            0.0,    # xr1
            1.0,    # xr2
            0.0,    # xs
            0.0002, # Ca_i (mM)
            0.2,    # Ca_sr (mM)
            0.0002, # Ca_ss (mM)
            11.6,   # Na_i (mM)
            138.3,  # K_i (mM)
        ])

    def derivatives(self, t: float, state: np.ndarray, stimulus: float = 0.0) -> np.ndarray:
        """Compute derivatives"""
        V, m, h, j, r, s, d, f, f2, fCass, xr1, xr2, xs, Ca_i, Ca_sr, Ca_ss, Na_i, K_i = state
        p = self.params

        # Reversal potentials
        E_Na = (p.R * p.T / p.F) * np.log(p.Na_o / Na_i)
        E_K = (p.R * p.T / p.F) * np.log(p.K_o / K_i)
        E_Ks = (p.R * p.T / p.F) * np.log((p.K_o + self.p_KNa * p.Na_o) / (K_i + self.p_KNa * Na_i))
        E_Ca = 0.5 * (p.R * p.T / p.F) * np.log(p.Ca_o / Ca_i)

        # Fast sodium current (INa)
        I_Na = self.g_Na * m**3 * h * j * (V - E_Na)

        # Gating variables for INa
        alpha_m = 1.0 / (1.0 + np.exp((-60.0 - V) / 5.0))
        beta_m = 0.1 / (1.0 + np.exp((V + 35.0) / 5.0)) + 0.10 / (1.0 + np.exp((V - 50.0) / 200.0))
        tau_m = alpha_m * beta_m
        m_inf = 1.0 / ((1.0 + np.exp((-56.86 - V) / 9.03))**2)
        dm_dt = (m_inf - m) / tau_m

        alpha_h = 0.0 if V >= -40.0 else 0.057 * np.exp(-(V + 80.0) / 6.8)
        beta_h = 0.77 / (0.13 * (1.0 + np.exp(-(V + 10.66) / 11.1))) if V >= -40.0 else \
                 2.7 * np.exp(0.079 * V) + 3.1e5 * np.exp(0.3485 * V)
        tau_h = 1.0 / (alpha_h + beta_h)
        h_inf = 1.0 / ((1.0 + np.exp((V + 71.55) / 7.43))**2)
        dh_dt = (h_inf - h) / tau_h

        alpha_j = 0.0 if V >= -40.0 else \
                  (-2.5428e4 * np.exp(0.2444 * V) - 6.948e-6 * np.exp(-0.04391 * V)) * (V + 37.78) / \
                  (1.0 + np.exp(0.311 * (V + 79.23)))
        beta_j = 0.6 * np.exp(0.057 * V) / (1.0 + np.exp(-0.1 * (V + 32.0))) if V >= -40.0 else \
                 0.02424 * np.exp(-0.01052 * V) / (1.0 + np.exp(-0.1378 * (V + 40.14)))
        tau_j = 1.0 / (alpha_j + beta_j)
        j_inf = h_inf
        dj_dt = (j_inf - j) / tau_j

        # Transient outward current (Ito)
        I_to = self.g_to * r * s * (V - E_K)

        r_inf = 1.0 / (1.0 + np.exp((20.0 - V) / 6.0))
        tau_r = 9.5 * np.exp(-(V + 40.0)**2 / 1800.0) + 0.8
        dr_dt = (r_inf - r) / tau_r

        s_inf = 1.0 / (1.0 + np.exp((V + 20.0) / 5.0)) if p.cell_type == 0 else \
                1.0 / (1.0 + np.exp((V + 28.0) / 5.0))
        tau_s = 85.0 * np.exp(-(V + 45.0)**2 / 320.0) + 5.0 / (1.0 + np.exp((V - 20.0) / 5.0)) + 3.0
        ds_dt = (s_inf - s) / tau_s

        # L-type calcium current (ICaL) - simplified
        I_CaL = self.g_CaL * d * f * f2 * fCass * 4.0 * (V - 15.0) * (p.F**2 / (p.R * p.T)) * \
                (0.25 * Ca_ss * np.exp(2.0 * (V - 15.0) * p.F / (p.R * p.T)) - p.Ca_o) / \
                (np.exp(2.0 * (V - 15.0) * p.F / (p.R * p.T)) - 1.0)

        d_inf = 1.0 / (1.0 + np.exp((-8.0 - V) / 7.5))
        alpha_d = 1.4 / (1.0 + np.exp((-35.0 - V) / 13.0)) + 0.25
        beta_d = 1.4 / (1.0 + np.exp((V + 5.0) / 5.0))
        gamma_d = 1.0 / (1.0 + np.exp((50.0 - V) / 20.0))
        tau_d = alpha_d * beta_d + gamma_d
        dd_dt = (d_inf - d) / tau_d

        f_inf = 1.0 / (1.0 + np.exp((V + 20.0) / 7.0))
        tau_f = 1102.5 * np.exp(-(V + 27.0)**2 / 225.0) + 200.0 / (1.0 + np.exp((13.0 - V) / 10.0)) + \
                180.0 / (1.0 + np.exp((V + 30.0) / 10.0)) + 20.0
        df_dt = (f_inf - f) / tau_f

        f2_inf = 0.67 / (1.0 + np.exp((V + 35.0) / 7.0)) + 0.33
        tau_f2 = 562.0 * np.exp(-(V + 27.0)**2 / 240.0) + 31.0 / (1.0 + np.exp((25.0 - V) / 10.0)) + \
                 80.0 / (1.0 + np.exp((V + 30.0) / 10.0))
        df2_dt = (f2_inf - f2) / tau_f2

        fCass_inf = 0.6 / (1.0 + (Ca_ss / 0.05)**2) + 0.4
        tau_fCass = 80.0 / (1.0 + (Ca_ss / 0.05)**2) + 2.0
        dfCass_dt = (fCass_inf - fCass) / tau_fCass

        # Rapid delayed rectifier (IKr)
        I_Kr = self.g_Kr * np.sqrt(p.K_o / 5.4) * xr1 * xr2 * (V - E_K)

        xr1_inf = 1.0 / (1.0 + np.exp((-26.0 - V) / 7.0))
        alpha_xr1 = 450.0 / (1.0 + np.exp((-45.0 - V) / 10.0))
        beta_xr1 = 6.0 / (1.0 + np.exp((V + 30.0) / 11.5))
        tau_xr1 = alpha_xr1 * beta_xr1
        dxr1_dt = (xr1_inf - xr1) / tau_xr1

        xr2_inf = 1.0 / (1.0 + np.exp((V + 88.0) / 24.0))
        alpha_xr2 = 3.0 / (1.0 + np.exp((-60.0 - V) / 20.0))
        beta_xr2 = 1.12 / (1.0 + np.exp((V - 60.0) / 20.0))
        tau_xr2 = alpha_xr2 * beta_xr2
        dxr2_dt = (xr2_inf - xr2) / tau_xr2

        # Slow delayed rectifier (IKs)
        I_Ks = self.g_Ks * xs**2 * (V - E_Ks)

        xs_inf = 1.0 / (1.0 + np.exp((-5.0 - V) / 14.0))
        alpha_xs = 1400.0 / np.sqrt(1.0 + np.exp((5.0 - V) / 6.0))
        beta_xs = 1.0 / (1.0 + np.exp((V - 35.0) / 15.0))
        tau_xs = alpha_xs * beta_xs + 80.0
        dxs_dt = (xs_inf - xs) / tau_xs

        # Inward rectifier (IK1)
        alpha_K1 = 0.1 / (1.0 + np.exp(0.06 * (V - E_K - 200.0)))
        beta_K1 = (3.0 * np.exp(0.0002 * (V - E_K + 100.0)) + np.exp(0.1 * (V - E_K - 10.0))) / \
                  (1.0 + np.exp(-0.5 * (V - E_K)))
        xK1_inf = alpha_K1 / (alpha_K1 + beta_K1)
        I_K1 = self.g_K1 * xK1_inf * (V - E_K)

        # Background currents
        I_bNa = self.g_bNa * (V - E_Na)
        I_bCa = self.g_bCa * (V - E_Ca)

        # Pumps and exchangers (simplified)
        I_NaK = 2.724 * (p.K_o / (p.K_o + 1.0)) * (Na_i / (Na_i + 40.0)) / \
                (1.0 + 0.1245 * np.exp(-0.1 * V * p.F / (p.R * p.T)) + \
                 0.0353 * np.exp(-V * p.F / (p.R * p.T)))

        I_NaCa = 1000.0 * (np.exp(0.35 * V * p.F / (p.R * p.T)) * Na_i**3 * p.Ca_o - \
                           np.exp((0.35 - 1.0) * V * p.F / (p.R * p.T)) * p.Na_o**3 * Ca_i * 2.5) / \
                 ((87.5**3 + p.Na_o**3) * (1.38 + p.Ca_o) * (1.0 + 0.1 * np.exp((0.35 - 1.0) * V * p.F / (p.R * p.T))))

        # Calcium dynamics (simplified)
        I_leak = 0.00036 * (Ca_sr - Ca_i)
        I_up = 0.006375 * Ca_i / (Ca_i + 0.00092)
        I_rel = (0.102 / (1.0 + 0.13**2 / Ca_ss**2)) * d * f * (Ca_sr - Ca_ss)

        dCa_i_dt = -((I_bCa + I_CaL - 2.0 * I_NaCa) / (2.0 * p.V_c * p.F) + I_leak - I_up)
        dCa_sr_dt = I_up - (I_rel + I_leak)
        dCa_ss_dt = I_rel - I_CaL / (2.0 * p.V_c * p.F)

        # Ion concentrations
        dNa_i_dt = -(I_Na + I_bNa + 3.0 * I_NaK + 3.0 * I_NaCa) / (p.V_c * p.F)
        dK_i_dt = -(I_K1 + I_to + I_Kr + I_Ks - 2.0 * I_NaK + stimulus) / (p.V_c * p.F)

        # Membrane potential
        I_total = I_Na + I_CaL + I_to + I_Kr + I_Ks + I_K1 + I_NaCa + I_NaK + I_bNa + I_bCa
        dV_dt = -(I_total + stimulus) / p.C_m

        return np.array([dV_dt, dm_dt, dh_dt, dj_dt, dr_dt, ds_dt, dd_dt, df_dt, df2_dt,
                        dfCass_dt, dxr1_dt, dxr2_dt, dxs_dt, dCa_i_dt, dCa_sr_dt, dCa_ss_dt,
                        dNa_i_dt, dK_i_dt])

    def step(self, t: float, state: np.ndarray, dt: float, stimulus: float = 0.0) -> np.ndarray:
        """Forward Euler step"""
        derivs = self.derivatives(t, state, stimulus)
        return state + dt * derivs


if __name__ == '__main__':
    print("=" * 60)
    print("Ten Tusscher-Panfilov 2006 Human Ventricular Model")
    print("=" * 60)

    model = TenTusscherModel()
    state = model.get_initial_state()

    print(f"\nInitial state:")
    print(f"  V = {state[0]:.1f} mV")
    print(f"  Ca_i = {state[13]:.6f} mM")
    print(f"  Na_i = {state[16]:.1f} mM")

    print("\nSimulating action potential...")
    t, dt = 0.0, 0.01
    for step in range(50000):
        stim = -52.0 if (10 <= t < 11) else 0.0
        state = model.step(t, state, dt, stimulus=stim)
        t += dt

        if step % 5000 == 0:
            print(f"  t={t:.1f}ms: V={state[0]:.1f}mV, Ca={state[13]:.6f}mM")

    print("\n" + "=" * 60)
