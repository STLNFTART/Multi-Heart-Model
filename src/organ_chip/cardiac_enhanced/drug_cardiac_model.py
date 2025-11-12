"""
Enhanced Cardiac Subsystem with Drug Effects

This module implements an enhanced cardiac electrophysiology model that includes:
- Action potential dynamics (modified Hodgkin-Huxley formalism)
- Ion channel drug interactions (hERG, Na+, Ca2+ channels)
- Calcium handling and contractility
- Drug-induced arrhythmia risk (QT prolongation, EADs, DADs)
- Mechanical coupling

Mathematical Model:
-------------------
Simplified cardiac action potential with drug effects:

Membrane Potential:
C_m * dV/dt = -(I_Na + I_Ca + I_K + I_leak) + I_stim

Ion Currents with Drug Block:
I_Na = g_Na * m^3 * h * (V - E_Na) * (1 - block_Na)
I_Ca = g_Ca * d * f * (V - E_Ca) * (1 - block_Ca)
I_K = g_K * n^4 * (V - E_K) * (1 - block_K)

Gating Variables (Hodgkin-Huxley formalism):
dx/dt = (x_inf(V) - x) / tau_x(V)  for x ∈ {m, h, d, f, n}

Calcium Handling:
dCa_i/dt = -I_Ca / (2*F*V_cell) + J_SR - k_Ca_uptake * Ca_i
dCa_SR/dt = k_Ca_uptake * Ca_i - J_SR

Contractility:
Force = k_force * Ca_i^n_Hill / (K_Ca^n_Hill + Ca_i^n_Hill)

Drug Binding (receptor occupancy model):
block_X = [Drug] / (IC50_X + [Drug])

Where:
- V: Membrane potential (mV)
- m, h: Na+ channel gating variables
- d, f: Ca2+ channel gating variables
- n: K+ channel gating variable
- Ca_i: Intracellular calcium (μM)
- Ca_SR: Sarcoplasmic reticulum calcium (μM)
- I_X: Ion currents (pA/pF)
- block_X: Fractional channel block (0-1)
- IC50_X: Half-maximal inhibitory concentration (μM)

References:
-----------
- Ten Tusscher et al. (2004) "A model for human ventricular tissue"
- Mirams et al. (2011) "Simulation of multiple ion channel block provides
  improved early prediction of compounds' clinical torsadogenic risk"
- Colatsky et al. (2016) "The Comprehensive in Vitro Proarrhythmia Assay (CiPA)"
"""

import numpy as np
from typing import Dict, Optional, Tuple


class DrugCardiacModel:
    """
    Enhanced cardiac model with drug effects on ion channels.

    This model captures:
    - Cardiac action potential (simplified Noble-type model)
    - hERG (IKr) block → QT prolongation
    - Nav1.5 (INa) block → conduction slowing
    - Cav1.2 (ICa) block → reduced contractility
    - Calcium handling and force generation
    - Early afterdepolarizations (EADs)
    - Delayed afterdepolarizations (DADs)

    State Variables:
    ----------------
    [V, m, h, d, f, n, Ca_i, Ca_SR]
    """

    def __init__(
        self,
        # Membrane capacitance
        C_m: float = 1.0,               # Membrane capacitance (μF/cm²)
        # Maximal conductances (mS/cm²)
        g_Na: float = 23.0,             # Fast Na+ current
        g_Ca: float = 0.09,             # L-type Ca2+ current
        g_K: float = 0.282,             # Delayed rectifier K+ current
        g_leak: float = 0.003,          # Leak current
        # Reversal potentials (mV)
        E_Na: float = 50.0,
        E_Ca: float = 60.0,
        E_K: float = -85.0,
        E_leak: float = -60.0,
        # Calcium handling
        k_Ca_uptake: float = 0.5,       # SERCA uptake rate (1/ms)
        k_SR_release: float = 5.0,      # SR release rate (1/ms)
        Ca_SR_threshold: float = 100.0, # SR release threshold (μM)
        # Contractility
        k_force: float = 1.0,           # Force scaling factor
        K_Ca: float = 1.0,              # Ca2+ sensitivity (μM)
        n_Hill: float = 2.0,            # Hill coefficient
        # Drug effects (IC50 values in μM)
        IC50_hERG: float = 1.0,         # hERG block IC50
        IC50_Na: float = 10.0,          # Nav1.5 block IC50
        IC50_Ca: float = 5.0,           # Cav1.2 block IC50
        # Initial conditions
        V0: float = -85.0,              # Resting potential (mV)
        Ca_i0: float = 0.1,             # Resting Ca2+ (μM)
        Ca_SR0: float = 100.0,          # SR Ca2+ (μM)
    ):
        """
        Initialize enhanced cardiac model with drug effects.

        Parameters
        ----------
        See class docstring for parameter descriptions.
        """
        self.C_m = C_m
        self.g_Na = g_Na
        self.g_Ca = g_Ca
        self.g_K = g_K
        self.g_leak = g_leak
        self.E_Na = E_Na
        self.E_Ca = E_Ca
        self.E_K = E_K
        self.E_leak = E_leak
        self.k_Ca_uptake = k_Ca_uptake
        self.k_SR_release = k_SR_release
        self.Ca_SR_threshold = Ca_SR_threshold
        self.k_force = k_force
        self.K_Ca = K_Ca
        self.n_Hill = n_Hill
        self.IC50_hERG = IC50_hERG
        self.IC50_Na = IC50_Na
        self.IC50_Ca = IC50_Ca

        # Gating variable initial values
        m0 = self._m_inf(V0)
        h0 = self._h_inf(V0)
        d0 = self._d_inf(V0)
        f0 = self._f_inf(V0)
        n0 = self._n_inf(V0)

        # State: [V, m, h, d, f, n, Ca_i, Ca_SR]
        self.state = np.array([V0, m0, h0, d0, f0, n0, Ca_i0, Ca_SR0], dtype=np.float64)

        # Drug concentration
        self.drug_conc = 0.0  # μM

        # Stimulus parameters
        self.stim_amplitude = 0.0
        self.stim_duration = 2.0  # ms
        self.stim_period = 1000.0  # ms (1 Hz)
        self.last_stim_time = -1000.0

        # History
        self.history = {
            't': [0.0],
            'V': [V0],
            'Ca_i': [Ca_i0],
            'Ca_SR': [Ca_SR0],
            'force': [0.0],
            'APD': [],
            'drug_conc': [0.0],
        }

    # Gating variable steady-state functions
    def _m_inf(self, V: float) -> float:
        """Na+ activation steady state."""
        alpha = 0.1 * (V + 40.0) / (1.0 - np.exp(-(V + 40.0) / 10.0))
        beta = 4.0 * np.exp(-(V + 65.0) / 18.0)
        return alpha / (alpha + beta)

    def _h_inf(self, V: float) -> float:
        """Na+ inactivation steady state."""
        alpha = 0.07 * np.exp(-(V + 65.0) / 20.0)
        beta = 1.0 / (1.0 + np.exp(-(V + 35.0) / 10.0))
        return alpha / (alpha + beta)

    def _d_inf(self, V: float) -> float:
        """Ca2+ activation steady state."""
        return 1.0 / (1.0 + np.exp(-(V + 10.0) / 6.24))

    def _f_inf(self, V: float) -> float:
        """Ca2+ inactivation steady state."""
        return 1.0 / (1.0 + np.exp((V + 35.0) / 7.3))

    def _n_inf(self, V: float) -> float:
        """K+ activation steady state."""
        alpha = 0.01 * (V + 55.0) / (1.0 - np.exp(-(V + 55.0) / 10.0))
        beta = 0.125 * np.exp(-(V + 65.0) / 80.0)
        return alpha / (alpha + beta)

    # Time constants
    def _tau_m(self, V: float) -> float:
        """Na+ activation time constant (ms)."""
        alpha = 0.1 * (V + 40.0) / (1.0 - np.exp(-(V + 40.0) / 10.0))
        beta = 4.0 * np.exp(-(V + 65.0) / 18.0)
        return 1.0 / (alpha + beta)

    def _tau_h(self, V: float) -> float:
        """Na+ inactivation time constant (ms)."""
        alpha = 0.07 * np.exp(-(V + 65.0) / 20.0)
        beta = 1.0 / (1.0 + np.exp(-(V + 35.0) / 10.0))
        return 1.0 / (alpha + beta)

    def _tau_d(self, V: float) -> float:
        """Ca2+ activation time constant (ms)."""
        return 1.0 / (1.0 + np.exp(-(V + 10.0) / 6.24)) + 0.5

    def _tau_f(self, V: float) -> float:
        """Ca2+ inactivation time constant (ms)."""
        return 80.0 / (1.0 + np.exp((V + 35.0) / 7.3)) + 10.0

    def _tau_n(self, V: float) -> float:
        """K+ activation time constant (ms)."""
        alpha = 0.01 * (V + 55.0) / (1.0 - np.exp(-(V + 55.0) / 10.0))
        beta = 0.125 * np.exp(-(V + 65.0) / 80.0)
        return 1.0 / (alpha + beta)

    def _calculate_drug_block(self, IC50: float) -> float:
        """
        Calculate fractional channel block.

        Parameters
        ----------
        IC50 : float
            Half-maximal inhibitory concentration (μM)

        Returns
        -------
        float
            Fractional block (0-1)
        """
        if IC50 <= 0:
            return 0.0
        return self.drug_conc / (IC50 + self.drug_conc)

    def derivatives(self, state: np.ndarray, t: float) -> np.ndarray:
        """
        Compute derivatives of state variables.

        Parameters
        ----------
        state : np.ndarray
            Current state [V, m, h, d, f, n, Ca_i, Ca_SR]
        t : float
            Current time (ms)

        Returns
        -------
        np.ndarray
            Derivatives
        """
        V, m, h, d, f, n, Ca_i, Ca_SR = state

        # Drug-induced channel block
        block_Na = self._calculate_drug_block(self.IC50_Na)
        block_Ca = self._calculate_drug_block(self.IC50_Ca)
        block_K = self._calculate_drug_block(self.IC50_hERG)

        # Ion currents with drug effects
        I_Na = self.g_Na * m**3 * h * (V - self.E_Na) * (1.0 - block_Na)
        I_Ca = self.g_Ca * d * f * (V - self.E_Ca) * (1.0 - block_Ca)
        I_K = self.g_K * n**4 * (V - self.E_K) * (1.0 - block_K)
        I_leak = self.g_leak * (V - self.E_leak)

        # Stimulus current
        I_stim = 0.0
        if self.stim_amplitude > 0:
            time_since_stim = (t - self.last_stim_time) % self.stim_period
            if time_since_stim < self.stim_duration:
                I_stim = self.stim_amplitude

        # Membrane potential
        dV_dt = (-I_Na - I_Ca - I_K - I_leak + I_stim) / self.C_m

        # Gating variables
        dm_dt = (self._m_inf(V) - m) / self._tau_m(V)
        dh_dt = (self._h_inf(V) - h) / self._tau_h(V)
        dd_dt = (self._d_inf(V) - d) / self._tau_d(V)
        df_dt = (self._f_inf(V) - f) / self._tau_f(V)
        dn_dt = (self._n_inf(V) - n) / self._tau_n(V)

        # Calcium handling
        # SR release (calcium-induced calcium release)
        J_SR = 0.0
        if Ca_SR > self.Ca_SR_threshold and I_Ca < -0.01:
            J_SR = self.k_SR_release * (Ca_SR - Ca_i)

        # Calcium dynamics
        F = 96485.0  # Faraday constant (C/mol)
        V_cell = 1.0e-5  # Cell volume (μL)

        dCa_i_dt = -I_Ca / (2.0 * F * V_cell) + J_SR - self.k_Ca_uptake * Ca_i
        dCa_SR_dt = self.k_Ca_uptake * Ca_i - J_SR

        return np.array([dV_dt, dm_dt, dh_dt, dd_dt, df_dt, dn_dt, dCa_i_dt, dCa_SR_dt])

    def step(self, dt: float, drug_conc: Optional[float] = None, pacing: bool = True) -> np.ndarray:
        """
        Advance simulation by one time step.

        Parameters
        ----------
        dt : float
            Time step (ms)
        drug_conc : float, optional
            Drug concentration (μM)
        pacing : bool
            Enable electrical pacing

        Returns
        -------
        np.ndarray
            Updated state
        """
        # Update drug concentration
        if drug_conc is not None:
            self.drug_conc = drug_conc

        # Set pacing
        if pacing:
            self.stim_amplitude = -52.0  # pA/pF
        else:
            self.stim_amplitude = 0.0

        # Get current time
        current_time = self.history['t'][-1]

        # Update last stim time if needed
        if pacing and (current_time - self.last_stim_time) >= self.stim_period:
            self.last_stim_time = current_time

        # Euler integration
        derivs = self.derivatives(self.state, current_time)
        self.state = self.state + dt * derivs

        # Calculate force
        Ca_i = self.state[6]
        force = self.k_force * Ca_i**self.n_Hill / (self.K_Ca**self.n_Hill + Ca_i**self.n_Hill)

        # Update history
        self.history['t'].append(current_time + dt)
        self.history['V'].append(self.state[0])
        self.history['Ca_i'].append(self.state[6])
        self.history['Ca_SR'].append(self.state[7])
        self.history['force'].append(force)
        self.history['drug_conc'].append(self.drug_conc)

        return self.state.copy()

    def get_force(self) -> float:
        """
        Calculate contractile force.

        Returns
        -------
        float
            Normalized force (0-1)
        """
        Ca_i = self.state[6]
        return self.k_force * Ca_i**self.n_Hill / (self.K_Ca**self.n_Hill + Ca_i**self.n_Hill)

    def get_state(self) -> Dict[str, float]:
        """
        Get current state as dictionary.

        Returns
        -------
        dict
            State dictionary
        """
        return {
            'V': self.state[0],
            'Ca_i': self.state[6],
            'Ca_SR': self.state[7],
            'force': self.get_force(),
            'drug_conc': self.drug_conc,
            'hERG_block': self._calculate_drug_block(self.IC50_hERG),
            'Na_block': self._calculate_drug_block(self.IC50_Na),
            'Ca_block': self._calculate_drug_block(self.IC50_Ca),
        }


def create_doxorubicin_cardiac_model() -> DrugCardiacModel:
    """
    Create cardiac model for doxorubicin cardiotoxicity.

    Doxorubicin causes:
    - Calcium handling dysfunction
    - Reduced contractility
    - Arrhythmias

    Returns
    -------
    DrugCardiacModel
        Configured model
    """
    return DrugCardiacModel(
        IC50_hERG=5.0,          # Moderate hERG block
        IC50_Ca=2.0,            # Strong Ca2+ channel effect
        k_Ca_uptake=0.3,        # Reduced SERCA function
    )


def create_quinidine_cardiac_model() -> DrugCardiacModel:
    """
    Create cardiac model for quinidine (potent hERG blocker).

    Quinidine causes:
    - Strong QT prolongation (hERG block)
    - Risk of torsades de pointes

    Returns
    -------
    DrugCardiacModel
        Configured model
    """
    return DrugCardiacModel(
        IC50_hERG=0.5,          # Very potent hERG block
        IC50_Na=50.0,           # Weak Na+ block
        IC50_Ca=100.0,          # Minimal Ca2+ effect
    )
