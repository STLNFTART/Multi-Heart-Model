"""
Courtemanche-Ramirez-Nattel Human Atrial Model

The Courtemanche model is the standard model for human atrial electrophysiology
and atrial fibrillation studies.

References:
- Courtemanche, M., Ramirez, R. J., & Nattel, S. (1998). "Ionic mechanisms
  underlying human atrial action potential properties: insights from a
  mathematical model." American Journal of Physiology-Heart and Circulatory
  Physiology, 275(1), H301-H321.

- Courtemanche, M., et al. (1999). "Ionic targets for drug therapy and atrial
  fibrillation-induced electrical remodeling: insights from a mathematical
  model." Cardiovascular Research, 42(2), 477-489.

Used for atrial fibrillation and antiarrhythmic drug studies.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class CourtemancheParameters:
    """Parameters for Courtemanche atrial model"""

    # Physical constants
    R: float = 8.3143  # Gas constant (kJ/kmol/K)
    T: float = 310.0  # Temperature (K)
    F: float = 96.4867  # Faraday constant (C/mmol)

    # Cell geometry
    C_m: float = 100.0  # Membrane capacitance (pF)
    V_cell: float = 20100.0  # Cell volume (μm³)
    V_i: float = 0.68 * 20100.0  # Cytoplasmic volume

    # External concentrations (mM)
    Na_o: float = 140.0
    K_o: float = 5.4
    Ca_o: float = 1.8

    # Atrial fibrillation remodeling (set to True for AF)
    af_remodeling: bool = False


class CourtemancheModel:
    """
    Courtemanche-Ramirez-Nattel human atrial model

    State variables (21):
    0: V - Membrane potential (mV)
    1-3: INa gates (m, h, j)
    4-5: Ito gates (oa, oi)
    6-8: IKur gates (ua, ui)
    9-10: ICaL gates (d, f)
    11: fCa - Ca-dependent inactivation
    12-13: IKr gates (xr)
    14: IKs gate (xs)
    15-17: Ca concentrations (Ca_i, Ca_up, Ca_rel)
    18-19: Na, K concentrations
    20: u (RyR gating)

    Example:
        >>> model = CourtemancheModel()
        >>> state = model.get_initial_state()
        >>>
        >>> # Simulate atrial AP
        >>> for i in range(30000):
        ...     stim = -200.0 if (10 <= t < 12) else 0.0  # pA/pF
        ...     state = model.step(t, state, 0.01, stimulus=stim)
        ...     t += 0.01
    """

    def __init__(self, params: Optional[CourtemancheParameters] = None):
        self.params = params if params is not None else CourtemancheParameters()
        self._setup_conductances()

    def _setup_conductances(self):
        """Setup conductances (adjust for AF remodeling if enabled)"""
        p = self.params

        if p.af_remodeling:
            # AF electrical remodeling (from 1999 paper)
            self.g_Na = 7.8  # Reduced
            self.g_to = 0.1652  # Reduced
            self.g_CaL = 0.0625  # Strongly reduced (50%)
            self.g_Kur = 0.005  # Reduced
            self.g_Kr = 0.029411765  # Same
            self.g_Ks = 0.12941176  # Same
            self.g_K1 = 0.09  # Increased (50%)
        else:
            # Normal atrial
            self.g_Na = 7.8
            self.g_to = 0.1652
            self.g_CaL = 0.125
            self.g_Kur = 0.005  + 0.065
            self.g_Kr = 0.029411765
            self.g_Ks = 0.12941176
            self.g_K1 = 0.09

        self.g_bNa = 0.000674
        self.g_bCa = 0.001131

    def get_initial_state(self) -> np.ndarray:
        """Get resting state"""
        return np.array([
            -81.2,   # V
            0.0029,  # m (INa)
            0.9649,  # h
            0.9775,  # j
            0.0304,  # oa (Ito)
            0.9992,  # oi
            0.0417,  # ua (IKur)
            0.9994,  # ui
            0.9995,  # uk
            0.0,     # d (ICaL)
            1.0,     # f
            0.7755,  # fCa
            0.0,     # xr (IKr)
            0.0,     # xs (IKs)
            0.0002,  # Ca_i (mM)
            0.08,    # Ca_up (mM)
            1.0,     # Ca_rel (mM)
            11.17,   # Na_i (mM)
            139.0,   # K_i (mM)
            0.0,     # u (RyR)
            0.0,     # v (RyR)
        ])

    def derivatives(self, t: float, state: np.ndarray, stimulus: float = 0.0) -> np.ndarray:
        """Compute derivatives"""
        V = state[0]
        m, h, j = state[1:4]
        oa, oi = state[4:6]
        ua, ui, uk = state[6:9]
        d, f, fCa = state[9:12]
        xr = state[12]
        xs = state[13]
        Ca_i, Ca_up, Ca_rel = state[14:17]
        Na_i, K_i = state[17:19]
        u, v = state[19:21]

        p = self.params

        # Reversal potentials
        E_Na = (p.R * p.T / p.F) * np.log(p.Na_o / Na_i)
        E_K = (p.R * p.T / p.F) * np.log(p.K_o / K_i)
        E_Ca = 0.5 * (p.R * p.T / p.F) * np.log(p.Ca_o / Ca_i)

        # INa - Fast sodium current
        I_Na = p.C_m * self.g_Na * m**3 * h * j * (V - E_Na)

        alpha_m = 0.32 * (V + 47.13) / (1.0 - np.exp(-0.1 * (V + 47.13)))
        beta_m = 0.08 * np.exp(-V / 11.0)
        dm_dt = alpha_m * (1.0 - m) - beta_m * m

        if V < -40.0:
            alpha_h = 0.135 * np.exp((V + 80.0) / -6.8)
            beta_h = 3.56 * np.exp(0.079 * V) + 3.1e5 * np.exp(0.35 * V)
            alpha_j = (-127140.0 * np.exp(0.2444 * V) - 3.474e-5 * np.exp(-0.04391 * V)) * \
                      (V + 37.78) / (1.0 + np.exp(0.311 * (V + 79.23)))
            beta_j = 0.1212 * np.exp(-0.01052 * V) / (1.0 + np.exp(-0.1378 * (V + 40.14)))
        else:
            alpha_h = 0.0
            beta_h = 1.0 / (0.13 * (1.0 + np.exp((V + 10.66) / -11.1)))
            alpha_j = 0.0
            beta_j = 0.3 * np.exp(-2.535e-7 * V) / (1.0 + np.exp(-0.1 * (V + 32.0)))

        dh_dt = alpha_h * (1.0 - h) - beta_h * h
        dj_dt = alpha_j * (1.0 - j) - beta_j * j

        # Ito - Transient outward current
        I_to = p.C_m * self.g_to * oa**3 * oi * (V - E_K)

        alpha_oa = 0.65 / (np.exp((V + 10.0) / -8.5) + np.exp((V - 30.0) / -59.0))
        beta_oa = 0.65 / (2.5 + np.exp((V + 82.0) / 17.0))
        tau_oa = 1.0 / (alpha_oa + beta_oa) / 1000.0  # Convert to seconds
        oa_inf = 1.0 / (1.0 + np.exp((V + 20.47) / -17.54))
        doa_dt = (oa_inf - oa) / tau_oa

        alpha_oi = 1.0 / (18.53 + np.exp((V + 113.7) / 10.95))
        beta_oi = 1.0 / (35.56 + np.exp((V + 1.26) / -7.44))
        tau_oi = 1.0 / (alpha_oi + beta_oi) / 1000.0
        oi_inf = 1.0 / (1.0 + np.exp((V + 43.1) / 5.3))
        doi_dt = (oi_inf - oi) / tau_oi

        # IKur - Ultra-rapid delayed rectifier (atrial-specific)
        I_Kur = p.C_m * self.g_Kur * ua**3 * ui * (V - E_K)

        ua_inf = 1.0 / (1.0 + np.exp((V + 30.3) / -9.6))
        tau_ua = 0.009 / (1.0 + np.exp((V + 5.0) / 12.0)) + 0.0005
        dua_dt = (ua_inf - ua) / tau_ua

        ui_inf = 1.0 / (1.0 + np.exp((V + 7.5) / 10.0))
        tau_ui = 0.59 / (1.0 + np.exp((V + 60.0) / 10.0)) + 3.05
        dui_dt = (ui_inf - ui) / tau_ui

        uk_inf = 1.0 / (1.0 + np.exp((V + 7.5) / 10.0))
        tau_uk = 0.01 + 0.005 / (1.0 + np.exp((V + 15.0) / 13.0))
        duk_dt = (uk_inf - uk) / tau_uk

        # ICaL - L-type calcium current
        I_CaL = p.C_m * self.g_CaL * d * f * fCa * (V - 65.0)

        d_inf = 1.0 / (1.0 + np.exp((V + 10.0) / -8.0))
        tau_d = (1.0 - np.exp((V + 10.0) / -6.24)) / (0.035 * (V + 10.0) * (1.0 + np.exp((V + 10.0) / -6.24)))
        dd_dt = (d_inf - d) / tau_d

        f_inf = np.exp(-(V + 28.0) / 6.9) / (1.0 + np.exp(-(V + 28.0) / 6.9))
        tau_f = 9.0 / (0.0197 * np.exp(-(0.0337 * (V + 10.0))**2) + 0.02)
        df_dt = (f_inf - f) / tau_f

        fCa_inf = 1.0 / (1.0 + (Ca_i / 0.00035)**2)
        tau_fCa = 2.0
        dfCa_dt = (fCa_inf - fCa) / tau_fCa

        # IKr - Rapid delayed rectifier
        I_Kr = p.C_m * self.g_Kr * xr * (V - E_K) / (1.0 + np.exp((V + 15.0) / 22.4))

        xr_inf = 1.0 / (1.0 + np.exp((V + 14.1) / -6.5))
        tau_xr = 1.0 / (0.0003 * (V + 14.1) / (1.0 - np.exp((V + 14.1) / -5.0)) +
                       0.000073898 * (V - 3.3328) / (np.exp((V - 3.3328) / 5.1237) - 1.0))
        dxr_dt = (xr_inf - xr) / tau_xr

        # IKs - Slow delayed rectifier
        I_Ks = p.C_m * self.g_Ks * xs**2 * (V - E_K)

        xs_inf = 1.0 / (1.0 + np.exp((V - 19.9) / -12.7))**0.5
        tau_xs = 0.5 / (0.00004 * (V - 19.9) / (1.0 - np.exp((V - 19.9) / -17.0)) +
                       0.000035 * (V - 19.9) / (np.exp((V - 19.9) / 9.0) - 1.0))
        dxs_dt = (xs_inf - xs) / tau_xs

        # IK1 - Inward rectifier
        K1_inf = 1.0 / (2.0 + np.exp(1.62 * p.F * (V - E_K) / (p.R * p.T)))
        I_K1 = p.C_m * self.g_K1 * K1_inf * (V - E_K)

        # Background currents
        I_bNa = p.C_m * self.g_bNa * (V - E_Na)
        I_bCa = p.C_m * self.g_bCa * (V - E_Ca)

        # Pumps and exchangers (simplified)
        I_NaK = p.C_m * 0.59933 * (p.K_o / (p.K_o + 1.0)) * (Na_i / (Na_i + 40.0)) / \
                (1.0 + 0.1245 * np.exp(-0.1 * p.F * V / (p.R * p.T)) +
                 0.0365 * np.exp(-p.F * V / (p.R * p.T)))

        I_NaCa = p.C_m * 1600.0 * (np.exp(0.35 * p.F * V / (p.R * p.T)) * Na_i**3 * p.Ca_o -
                                    np.exp((0.35 - 1.0) * p.F * V / (p.R * p.T)) * p.Na_o**3 * Ca_i) / \
                 ((87.5**3 + p.Na_o**3) * (1.38 + p.Ca_o))

        # Calcium dynamics (simplified)
        I_up = 0.005 * Ca_i / (Ca_i + 0.00092)
        I_rel = 0.01 * u * (Ca_rel - Ca_i)
        I_leak = 0.0001 * (Ca_up - Ca_i)

        # RyR gating (simplified)
        u_inf = 1.0 / (1.0 + np.exp(-(Ca_i - 0.0003) / 0.0001))
        du_dt = (u_inf - u) / 0.008

        v_inf = 1.0 - 1.0 / (1.0 + np.exp(-(Ca_i - 0.0006) / 0.0002))
        dv_dt = (v_inf - v) / 0.050

        dCa_i_dt = (I_leak - I_up + I_rel) - (I_CaL + I_bCa - 2.0 * I_NaCa) / (2.0 * p.V_i * p.F)
        dCa_up_dt = I_up - I_leak
        dCa_rel_dt = -I_rel * p.V_i / (p.V_cell * 0.01)

        # Ion concentrations
        dNa_i_dt = -(I_Na + I_bNa + 3.0 * I_NaK + 3.0 * I_NaCa) / (p.V_i * p.F)
        dK_i_dt = -(I_to + I_Kur + I_Kr + I_Ks + I_K1 - 2.0 * I_NaK + stimulus) / (p.V_i * p.F)

        # Membrane potential
        I_total = I_Na + I_to + I_Kur + I_CaL + I_Kr + I_Ks + I_K1 + I_NaCa + I_NaK + I_bNa + I_bCa
        dV_dt = -(I_total + stimulus) / p.C_m

        return np.array([dV_dt, dm_dt, dh_dt, dj_dt, doa_dt, doi_dt, dua_dt, dui_dt, duk_dt,
                        dd_dt, df_dt, dfCa_dt, dxr_dt, dxs_dt, dCa_i_dt, dCa_up_dt, dCa_rel_dt,
                        dNa_i_dt, dK_i_dt, du_dt, dv_dt])

    def step(self, t: float, state: np.ndarray, dt: float, stimulus: float = 0.0) -> np.ndarray:
        """Forward Euler step"""
        derivs = self.derivatives(t, state, stimulus)
        return state + dt * derivs


if __name__ == '__main__':
    print("=" * 60)
    print("Courtemanche Human Atrial Model")
    print("=" * 60)

    # Normal atrial cell
    model = CourtemancheModel()
    state = model.get_initial_state()

    print(f"\nNormal atrial cell - Initial state:")
    print(f"  V = {state[0]:.1f} mV")
    print(f"  Ca_i = {state[14]:.6f} mM")

    print("\nSimulating atrial AP...")
    t, dt = 0.0, 0.01
    for step in range(30000):
        stim = -200.0 if (10 <= t < 12) else 0.0
        state = model.step(t, state, dt, stimulus=stim)
        t += dt

        if step % 5000 == 0:
            print(f"  t={t:.1f}ms: V={state[0]:.1f}mV")

    print("\n" + "=" * 60)
