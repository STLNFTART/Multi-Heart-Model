"""
O'Hara-Rudy 2011 (ORd) Human Ventricular Model

The ORd model is the modern standard for human ventricular electrophysiology
and is the basis for the CiPA (Comprehensive in vitro Proarrhythmia Assay)
initiative for cardiac drug safety testing.

References:
- O'Hara, T., Virág, L., Varró, A., & Rudy, Y. (2011). "Simulation of the
  undiseased human cardiac ventricular action potential: Model formulation
  and experimental validation." PLOS Computational Biology, 7(5), e1002061.

- Dutta, S., et al. (2017). "Optimization of an in silico cardiac cell model
  for proarrhythmia risk assessment." Frontiers in Physiology, 8, 616.

This is the CiPA standard model for drug-induced arrhythmia risk assessment.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class OHaraRudyParameters:
    """Parameters for O'Hara-Rudy 2011 model"""

    # Physical constants
    R: float = 8314.0  # Gas constant (J/kmol/K)
    T: float = 310.0  # Temperature (K)
    F: float = 96485.0  # Faraday constant (C/mol)

    # Cell geometry
    L: float = 0.01  # Cell length (cm)
    rad: float = 0.0011  # Cell radius (cm)
    C_m: float = 1.0  # Membrane capacitance (μF/cm²)

    # Ion concentrations (mM)
    Na_o: float = 140.0
    K_o: float = 5.4
    Ca_o: float = 1.8

    # Cell type (0=endo, 1=epi, 2=M cell)
    cell_type: int = 0


class OHaraRudyModel:
    """
    O'Hara-Rudy 2011 human ventricular model (CiPA standard)

    State variables (41 total, simplified to 19 for efficiency):
    0: V - Membrane potential (mV)
    1-3: INa gates (m, h, j)
    4-5: Ito gates (a, i)
    6-7: ICaL gates (d, f)
    8-9: IKr gates (xr_fast, xr_slow)
    10: IKs gate (xs1)
    11-13: Ca concentrations (Ca_i, Ca_nsr, Ca_jsr)
    14-15: Na, K concentrations
    16-18: RyR states (simplified)

    This is the CiPA standard for cardiac safety pharmacology.
    """

    def __init__(self, params: Optional[OHaraRudyParameters] = None):
        self.params = params if params is not None else OHaraRudyParameters()
        self._setup_cell_type()

    def _setup_cell_type(self):
        """Adjust parameters for cell type"""
        p = self.params

        # Calculate volumes
        v_cell = 1000.0 * 3.14 * p.rad * p.rad * p.L
        self.v_cyt = 0.678 * v_cell
        self.v_nsr = 0.0552 * v_cell
        self.v_jsr = 0.0048 * v_cell

        # Adjust conductances for cell type
        if p.cell_type == 0:  # Endocardial
            self.GNa = 75.0
            self.Gto = 0.02
            self.GKr = 0.046
            self.GKs = 0.0034
        elif p.cell_type == 1:  # Epicardial
            self.GNa = 75.0
            self.Gto = 0.08  # Higher in epi
            self.GKr = 0.046
            self.GKs = 0.0034
        else:  # M cell
            self.GNa = 75.0
            self.Gto = 0.02
            self.GKr = 0.046
            self.GKs = 0.0034 * 1.87  # Higher in M cells

        self.GCaL = 0.0001
        self.GK1 = 0.1908
        self.GbNa = 0.00029
        self.GbCa = 0.000592
        self.PNaK = 30.0

    def get_initial_state(self) -> np.ndarray:
        """Get resting state"""
        return np.array([
            -87.0,   # V
            0.0,     # m (INa)
            0.75,    # h
            0.75,    # j
            0.0,     # a (Ito)
            1.0,     # i
            0.0,     # d (ICaL)
            1.0,     # f
            0.0,     # xrf (IKr fast)
            0.0,     # xrs (IKr slow)
            0.0,     # xs1 (IKs)
            0.0001,  # Ca_i (mM)
            1.2,     # Ca_nsr (mM)
            1.2,     # Ca_jsr (mM)
            7.0,     # Na_i (mM)
            145.0,   # K_i (mM)
            0.0,     # RyR_open
            0.0,     # RyR_adapt
            0.0,     # RyR_close
        ])

    def derivatives(self, t: float, state: np.ndarray, stimulus: float = 0.0) -> np.ndarray:
        """Compute state derivatives (simplified for efficiency)"""
        V = state[0]
        m, h, j = state[1:4]
        a, i = state[4:6]
        d, f = state[6:8]
        xrf, xrs = state[8:10]
        xs1 = state[10]
        Ca_i, Ca_nsr, Ca_jsr = state[11:14]
        Na_i, K_i = state[14:16]

        p = self.params

        # Reversal potentials
        E_Na = (p.R * p.T / p.F) * np.log(p.Na_o / Na_i)
        E_K = (p.R * p.T / p.F) * np.log(p.K_o / K_i)
        E_Ca = 0.5 * (p.R * p.T / p.F) * np.log(p.Ca_o / Ca_i)
        E_Ks = (p.R * p.T / p.F) * np.log((p.K_o + 0.03 * p.Na_o) / (K_i + 0.03 * Na_i))

        # INa - Fast sodium current
        I_Na = self.GNa * m**3 * h * j * (V - E_Na)

        m_inf = 1.0 / (1.0 + np.exp((-(V + 39.57)) / 9.871))
        tau_m = 1.0 / (6.765 * np.exp((V + 11.64) / 34.77) + 8.552 * np.exp(-(V + 77.42) / 5.955))
        dm_dt = (m_inf - m) / tau_m

        h_inf = 1.0 / (1.0 + np.exp((V + 82.90) / 6.086))
        tau_h = 1.0 / (0.009794 * np.exp(-(V + 17.95) / 28.05) + 0.3343 * np.exp((V + 5.730) / 56.66))
        dh_dt = (h_inf - h) / tau_h

        j_inf = h_inf
        tau_j = 2.038 + 1.0 / (0.02136 * np.exp(-(V + 100.6) / 8.281) + 0.3052 * np.exp((V + 0.9941) / 38.45))
        dj_dt = (j_inf - j) / tau_j

        # Ito - Transient outward current
        I_to = self.Gto * a * i * (V - E_K)

        a_inf = 1.0 / (1.0 + np.exp((-(V - 14.34)) / 14.82))
        tau_a = 1.0515 / (1.0 / (1.2089 * (1.0 + np.exp(-(V - 18.4099) / 29.3814))) +
                         3.5 / (1.0 + np.exp((V + 100.0) / 29.3814)))
        da_dt = (a_inf - a) / tau_a

        i_inf = 1.0 / (1.0 + np.exp((V + 43.94) / 5.711))
        tau_i = 4.562 + 1.0 / (0.3933 * np.exp((-(V + 100.0)) / 100.0) + 0.08004 * np.exp((V + 50.0) / 16.59))
        di_dt = (i_inf - i) / tau_i

        # ICaL - L-type calcium current (simplified)
        I_CaL = self.GCaL * d * f * (V - 65.0)

        d_inf = 1.0 / (1.0 + np.exp((-(V + 3.940)) / 4.230))
        tau_d = 0.6 + 1.0 / (np.exp(-0.05 * (V + 6.0)) + np.exp(0.09 * (V + 14.0)))
        dd_dt = (d_inf - d) / tau_d

        f_inf = 1.0 / (1.0 + np.exp((V + 19.58) / 3.696))
        tau_f = 7.0 + 1.0 / (0.0045 * np.exp(-(V + 20.0) / 10.0) + 0.0045 * np.exp((V + 20.0) / 10.0))
        df_dt = (f_inf - f) / tau_f

        # IKr - Rapid delayed rectifier
        I_Kr = self.GKr * np.sqrt(p.K_o / 5.4) * (0.6 * xrf + 0.4 * xrs) * (V - E_K)

        xr_inf = 1.0 / (1.0 + np.exp((-(V + 8.337)) / 6.789))
        tau_xrf = 12.98 + 1.0 / (0.3652 * np.exp((V - 31.66) / 3.869) + 4.123e-5 * np.exp((-(V - 47.78)) / 20.38))
        tau_xrs = 1.865 + 1.0 / (0.06629 * np.exp((V - 34.70) / 7.355) + 1.128e-5 * np.exp((-(V - 29.74)) / 25.94))
        dxrf_dt = (xr_inf - xrf) / tau_xrf
        dxrs_dt = (xr_inf - xrs) / tau_xrs

        # IKs - Slow delayed rectifier
        I_Ks = self.GKs * xs1**2 * (V - E_Ks)

        xs1_inf = 1.0 / (1.0 + np.exp((-(V + 11.60)) / 8.932))
        tau_xs1 = 817.3 + 1.0 / (2.326e-4 * np.exp((V + 48.28) / 17.80) + 0.001292 * np.exp((-(V + 210.0)) / 230.0))
        dxs1_dt = (xs1_inf - xs1) / tau_xs1

        # IK1 - Inward rectifier
        xK1_inf = 1.0 / (1.0 + np.exp(-(V - E_K - 2.5538 * p.K_o + 144.59) / (1.5692 * p.K_o + 3.8115)))
        tau_xK1 = 122.2 / (np.exp((-(V + 127.2)) / 20.36) + np.exp((V + 236.8) / 69.33))
        I_K1 = self.GK1 * np.sqrt(p.K_o / 5.4) * xK1_inf * (V - E_K)

        # Background currents
        I_bNa = self.GbNa * (V - E_Na)
        I_bCa = self.GbCa * (V - E_Ca)

        # Na-K pump
        I_NaK = self.PNaK * (p.K_o / (p.K_o + 1.0)) * (Na_i / (Na_i + 40.0)) / \
                (1.0 + 0.1245 * np.exp(-0.1 * V * p.F / (p.R * p.T)) + 0.0353 * np.exp(-V * p.F / (p.R * p.T)))

        # Na-Ca exchanger (simplified)
        I_NaCa = 1000.0 * (np.exp(0.35 * V * p.F / (p.R * p.T)) * Na_i**3 * p.Ca_o -
                           np.exp(-0.65 * V * p.F / (p.R * p.T)) * p.Na_o**3 * Ca_i) / \
                 (1.0 + 0.1 * np.exp(-0.65 * V * p.F / (p.R * p.T)))

        # Calcium dynamics (simplified)
        I_up = 0.005 * Ca_i / (Ca_i + 0.001)
        I_rel = 0.01 * d * f * (Ca_jsr - Ca_i)
        I_leak = 0.0002 * (Ca_nsr - Ca_i)

        dCa_i_dt = I_rel - I_up + I_leak - (I_CaL + I_bCa - 2.0 * I_NaCa) / (2.0 * self.v_cyt * p.F)
        dCa_nsr_dt = I_up - I_leak
        dCa_jsr_dt = -I_rel

        # Ion concentrations
        dNa_i_dt = -(I_Na + I_bNa + 3.0 * I_NaK + 3.0 * I_NaCa) / (self.v_cyt * p.F)
        dK_i_dt = -(I_to + I_Kr + I_Ks + I_K1 - 2.0 * I_NaK + stimulus) / (self.v_cyt * p.F)

        # RyR states (simplified)
        dRyR = np.zeros(3)

        # Membrane potential
        I_total = I_Na + I_to + I_CaL + I_Kr + I_Ks + I_K1 + I_NaCa + I_NaK + I_bNa + I_bCa
        dV_dt = -(I_total + stimulus) / p.C_m

        return np.array([dV_dt, dm_dt, dh_dt, dj_dt, da_dt, di_dt, dd_dt, df_dt,
                        dxrf_dt, dxrs_dt, dxs1_dt, dCa_i_dt, dCa_nsr_dt, dCa_jsr_dt,
                        dNa_i_dt, dK_i_dt, *dRyR])

    def step(self, t: float, state: np.ndarray, dt: float, stimulus: float = 0.0) -> np.ndarray:
        """Forward Euler step"""
        derivs = self.derivatives(t, state, stimulus)
        return state + dt * derivs


if __name__ == '__main__':
    print("=" * 60)
    print("O'Hara-Rudy 2011 Model (CiPA Standard)")
    print("=" * 60)

    model = OHaraRudyModel()
    state = model.get_initial_state()

    print(f"\nInitial state:")
    print(f"  V = {state[0]:.1f} mV")
    print(f"  Ca_i = {state[11]:.6f} mM")

    print("\nSimulating action potential (CiPA protocol)...")
    t, dt = 0.0, 0.01
    for step in range(100000):
        stim = -80.0 if (50 <= t < 51) else 0.0
        state = model.step(t, state, dt, stimulus=stim)
        t += dt

        if step % 10000 == 0:
            print(f"  t={t:.1f}ms: V={state[0]:.1f}mV, Ca={state[11]:.6f}mM")

    print("\n" + "=" * 60)
