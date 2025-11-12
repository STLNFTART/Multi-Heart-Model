"""Cardiac organ chip with electrophysiology and drug-induced cardiotoxicity.

This module implements:
- Ion channel dynamics (hERG, Nav, Cav, K+ channels)
- Action potential generation
- Drug effects on ion channels (IC50-based inhibition)
- QT interval prolongation
- Contractility and calcium handling
- Cardiotoxicity biomarkers (troponin, BNP)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Dict, List
import math


@dataclass
class IonChannelDynamics:
    """Simplified cardiac ion channel model with drug effects.

    Models key cardiac ion channels:
    - INa: Fast sodium current (depolarization)
    - ICaL: L-type calcium current (plateau)
    - IKr: Rapid delayed rectifier (hERG, repolarization)
    - IK1: Inward rectifier (resting potential)
    """

    # Maximal conductances (mS/cm²)
    gNa: float = 16.0
    gCaL: float = 0.5
    gKr: float = 0.3
    gK1: float = 5.0

    # Reversal potentials (mV)
    ENa: float = 50.0
    ECa: float = 120.0
    EK: float = -85.0

    # Drug IC50 values (μM) - default is no drug (high IC50)
    IC50_hERG: float = 1000.0    # hERG (IKr) inhibition
    IC50_Nav: float = 1000.0      # Nav inhibition
    IC50_Cav: float = 1000.0      # Cav inhibition

    def hill_inhibition(self, drug_conc: float, IC50: float, n: float = 1.0) -> float:
        """Calculate fractional channel inhibition.

        Parameters
        ----------
        drug_conc : float
            Drug concentration (μM)
        IC50 : float
            Half-maximal inhibitory concentration (μM)
        n : float
            Hill coefficient

        Returns
        -------
        float
            Fraction of channels blocked [0, 1]
        """
        if drug_conc <= 0 or IC50 <= 0:
            return 0.0
        return (drug_conc ** n) / (IC50 ** n + drug_conc ** n)

    def compute_currents(
        self,
        V: float,
        m: float,
        h: float,
        d: float,
        f: float,
        xr: float,
        drug_conc: float = 0.0
    ) -> Dict[str, float]:
        """Compute ion channel currents.

        Parameters
        ----------
        V : float
            Membrane potential (mV)
        m, h : float
            Na+ channel gating variables
        d, f : float
            Ca2+ channel gating variables
        xr : float
            Kr channel gating variable
        drug_conc : float
            Drug concentration (μM)

        Returns
        -------
        dict
            Individual ion currents (μA/cm²)
        """
        # Drug-induced channel block
        block_hERG = self.hill_inhibition(drug_conc, self.IC50_hERG)
        block_Nav = self.hill_inhibition(drug_conc, self.IC50_Nav)
        block_Cav = self.hill_inhibition(drug_conc, self.IC50_Cav)

        # Ion currents with drug effects
        INa = self.gNa * (1.0 - block_Nav) * (m ** 3) * h * (V - self.ENa)
        ICaL = self.gCaL * (1.0 - block_Cav) * d * f * (V - self.ECa)
        IKr = self.gKr * (1.0 - block_hERG) * xr * (V - self.EK)
        IK1 = self.gK1 * (V - self.EK) / (1.0 + math.exp(0.07 * (V + 80)))

        return {
            'INa': INa,
            'ICaL': ICaL,
            'IKr': IKr,
            'IK1': IK1,
            'Itotal': INa + ICaL + IKr + IK1,
        }

    def gating_derivatives(
        self,
        V: float,
        m: float,
        h: float,
        d: float,
        f: float,
        xr: float
    ) -> Tuple[float, float, float, float, float]:
        """Compute gating variable derivatives.

        Parameters
        ----------
        V : float
            Membrane potential (mV)
        m, h, d, f, xr : float
            Gating variables

        Returns
        -------
        tuple
            (dm/dt, dh/dt, dd/dt, df/dt, dxr/dt)
        """
        # Simplified gating kinetics

        # Na channel (m, h)
        alpha_m = 0.32 * (V + 47.13) / (1.0 - math.exp(-0.1 * (V + 47.13)))
        beta_m = 0.08 * math.exp(-V / 11.0)
        m_inf = alpha_m / (alpha_m + beta_m)
        tau_m = 1.0 / (alpha_m + beta_m)

        alpha_h = 0.135 * math.exp(-(V + 80.0) / 6.8)
        beta_h = 7.5 / (1.0 + math.exp(-0.1 * (V + 11.0)))
        h_inf = alpha_h / (alpha_h + beta_h)
        tau_h = 1.0 / (alpha_h + beta_h)

        # Ca channel (d, f)
        d_inf = 1.0 / (1.0 + math.exp(-(V + 10.0) / 6.24))
        tau_d = 0.5 + 1.0 / (math.exp((V + 35.0) / 5.0) + math.exp(-(V + 35.0) / 5.0))

        f_inf = 1.0 / (1.0 + math.exp((V + 32.0) / 8.0))
        tau_f = 5.0 + 10.0 / (1.0 + math.exp((V + 28.0) / 5.0))

        # Kr channel (xr)
        xr_inf = 1.0 / (1.0 + math.exp(-(V + 10.0) / 5.0))
        tau_xr = 1.0 / (0.0006 * (V - 1.7384) / (1.0 - math.exp(-0.136 * (V - 1.7384))) +
                        0.0003 * (V + 38.3608) / (math.exp(0.1522 * (V + 38.3608)) - 1.0))

        # Compute derivatives
        dm = (m_inf - m) / tau_m
        dh = (h_inf - h) / tau_h
        dd = (d_inf - d) / tau_d
        df = (f_inf - f) / tau_f
        dxr = (xr_inf - xr) / tau_xr

        return dm, dh, dd, df, dxr


@dataclass
class ContractilityModel:
    """Cardiac contractility and calcium handling model.

    Models:
    - Intracellular calcium dynamics
    - Calcium-force relationship
    - Contractile force generation
    - Drug effects on contractility
    """

    # Calcium handling parameters
    Ca_baseline: float = 0.1      # μM
    Ca_amplitude: float = 1.0     # μM
    SERCA_rate: float = 0.5       # 1/ms
    NCX_rate: float = 0.3         # 1/ms

    # Force generation parameters
    Ca50: float = 0.5             # μM - half-maximal Ca for contraction
    force_max: float = 100.0      # mN/mm²

    def calcium_transient(self, t: float, frequency: float = 1.0) -> float:
        """Simulate calcium transient during action potential.

        Parameters
        ----------
        t : float
            Time (ms)
        frequency : float
            Pacing frequency (Hz)

        Returns
        -------
        float
            Intracellular Ca2+ concentration (μM)
        """
        # Periodic calcium release
        phase = 2.0 * math.pi * frequency * t / 1000.0
        Ca_release = self.Ca_amplitude * max(0.0, math.sin(phase))

        return self.Ca_baseline + Ca_release

    def force_from_calcium(self, Ca: float) -> float:
        """Calculate contractile force from calcium concentration.

        Parameters
        ----------
        Ca : float
            Calcium concentration (μM)

        Returns
        -------
        float
            Contractile force (mN/mm²)
        """
        # Hill equation for Ca-force relationship
        n = 3.0  # Hill coefficient
        return self.force_max * (Ca ** n) / (self.Ca50 ** n + Ca ** n)

    def derivatives(
        self,
        t: float,
        state: Tuple[float, float],
        ICaL: float = 0.0
    ) -> Tuple[float, float]:
        """Compute derivatives for calcium and force.

        Parameters
        ----------
        t : float
            Time (ms)
        state : tuple
            (Ca_i, Force) - intracellular calcium and force
        ICaL : float
            L-type calcium current (μA/cm²)

        Returns
        -------
        tuple
            (dCa/dt, dForce/dt)
        """
        Ca_i, Force = state

        # Calcium dynamics
        Ca_influx = -0.01 * ICaL  # Convert current to concentration change
        Ca_uptake = self.SERCA_rate * (Ca_i - self.Ca_baseline)
        Ca_extrusion = self.NCX_rate * Ca_i

        dCa = Ca_influx - Ca_uptake - Ca_extrusion

        # Force development
        Force_target = self.force_from_calcium(Ca_i)
        tau_force = 50.0  # ms
        dForce = (Force_target - Force) / tau_force

        return dCa, dForce


@dataclass
class CardiotoxicityModel:
    """Comprehensive cardiotoxicity assessment model.

    Integrates:
    - Electrophysiological effects (QT prolongation, arrhythmias)
    - Contractile dysfunction
    - Biomarker release (troponin, BNP)
    - Mitochondrial toxicity
    """

    ion_channels: IonChannelDynamics = field(default_factory=IonChannelDynamics)
    contractility: ContractilityModel = field(default_factory=ContractilityModel)

    # Biomarker baseline values
    troponin_baseline: float = 0.01  # ng/mL
    BNP_baseline: float = 20.0       # pg/mL

    # Toxicity thresholds
    QTc_prolongation_threshold: float = 30.0  # ms
    force_reduction_threshold: float = 0.3    # 30% reduction

    def calculate_APD(
        self,
        V_trace: List[float],
        time_trace: List[float],
        repol_threshold: float = -70.0
    ) -> float:
        """Calculate action potential duration (APD90).

        Parameters
        ----------
        V_trace : list
            Membrane potential time series (mV)
        time_trace : list
            Time points (ms)
        repol_threshold : float
            Repolarization threshold (mV)

        Returns
        -------
        float
            APD90 duration (ms)
        """
        if len(V_trace) < 2 or len(time_trace) != len(V_trace):
            return 0.0

        # Find upstroke
        V_max = max(V_trace)
        upstroke_idx = V_trace.index(V_max)

        # Find 90% repolarization
        V_90 = repol_threshold + 0.1 * (V_max - repol_threshold)

        for i in range(upstroke_idx, len(V_trace)):
            if V_trace[i] <= V_90:
                return time_trace[i] - time_trace[upstroke_idx]

        return 0.0

    def assess_toxicity(
        self,
        APD: float,
        APD_baseline: float,
        force: float,
        force_baseline: float,
        troponin: float,
        BNP: float
    ) -> Dict[str, any]:
        """Assess cardiotoxicity severity.

        Parameters
        ----------
        APD : float
            Action potential duration (ms)
        APD_baseline : float
            Baseline APD (ms)
        force : float
            Contractile force (mN/mm²)
        force_baseline : float
            Baseline force (mN/mm²)
        troponin : float
            Troponin level (ng/mL)
        BNP : float
            BNP level (pg/mL)

        Returns
        -------
        dict
            Toxicity assessment
        """
        # QTc prolongation (surrogate for APD)
        QTc_change = APD - APD_baseline

        # Contractile dysfunction
        force_reduction = (force_baseline - force) / force_baseline if force_baseline > 0 else 0.0

        # Biomarker elevation
        troponin_fold = troponin / self.troponin_baseline
        BNP_fold = BNP / self.BNP_baseline

        # Severity scores
        electrical_score = min(1.0, max(0.0, QTc_change / 100.0))
        mechanical_score = min(1.0, max(0.0, force_reduction))
        biomarker_score = min(1.0, (troponin_fold - 1.0) / 10.0)

        # Overall toxicity score
        toxicity_score = (
            0.4 * electrical_score +
            0.3 * mechanical_score +
            0.3 * biomarker_score
        )

        # Classification
        if toxicity_score < 0.2:
            severity = "None"
            risk = "Low"
        elif toxicity_score < 0.4:
            severity = "Mild"
            risk = "Low-Moderate"
        elif toxicity_score < 0.6:
            severity = "Moderate"
            risk = "Moderate"
        elif toxicity_score < 0.8:
            severity = "Severe"
            risk = "High"
        else:
            severity = "Critical"
            risk = "Very High"

        return {
            "toxicity_score": toxicity_score,
            "severity": severity,
            "arrhythmia_risk": risk,
            "QTc_prolongation_ms": QTc_change,
            "force_reduction_pct": force_reduction * 100,
            "troponin_fold_elevation": troponin_fold,
            "BNP_fold_elevation": BNP_fold,
            "electrical_score": electrical_score,
            "mechanical_score": mechanical_score,
        }


@dataclass
class CardiacCell:
    """Integrated cardiac cell model.

    Combines electrophysiology, calcium handling, contractility,
    and toxicity assessment.
    """

    ion_channels: IonChannelDynamics = field(default_factory=IonChannelDynamics)
    contractility: ContractilityModel = field(default_factory=ContractilityModel)
    toxicity: CardiotoxicityModel = field(default_factory=CardiotoxicityModel)

    # Cell parameters
    Cm: float = 1.0  # Membrane capacitance (μF/cm²)

    def derivatives(
        self,
        t: float,
        state: Tuple[float, float, float, float, float, float, float, float, float, float],
        drug_conc: float = 0.0,
        stimulus: float = 0.0
    ) -> Tuple[float, ...]:
        """Compute derivatives for complete cardiac cell model.

        State (10 variables):
        - V: Membrane potential (mV)
        - m, h: Na+ channel gates
        - d, f: Ca2+ channel gates
        - xr: Kr channel gate
        - Ca_i: Intracellular calcium (μM)
        - Force: Contractile force (mN/mm²)
        - Troponin: Troponin release (ng/mL)
        - BNP: B-type natriuretic peptide (pg/mL)

        Parameters
        ----------
        t : float
            Time (ms)
        state : tuple
            State vector
        drug_conc : float
            Drug concentration (μM)
        stimulus : float
            External stimulus current (μA/cm²)

        Returns
        -------
        tuple
            Time derivatives
        """
        V, m, h, d, f, xr, Ca_i, Force, Troponin, BNP = state

        # Ion currents
        currents = self.ion_channels.compute_currents(V, m, h, d, f, xr, drug_conc)
        Itotal = currents['Itotal']
        ICaL = currents['ICaL']

        # Membrane potential
        dV = -(Itotal - stimulus) / self.Cm

        # Gating variables
        dm, dh, dd, df, dxr = self.ion_channels.gating_derivatives(V, m, h, d, f, xr)

        # Calcium and force
        dCa, dForce = self.contractility.derivatives(t, (Ca_i, Force), ICaL)

        # Biomarker release (stress-dependent)
        stress_factor = max(0.0, drug_conc / 10.0)  # Simplified
        dTroponin = 0.01 * stress_factor - 0.1 * Troponin
        dBNP = 0.1 * stress_factor - 0.05 * BNP

        return dV, dm, dh, dd, df, dxr, dCa, dForce, dTroponin, dBNP
