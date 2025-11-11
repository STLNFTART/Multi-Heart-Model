"""
Heart-on-Chip Module

Implements cardiomyocyte populations, cardiac electrophysiology, contractility,
and cardiotoxicity within the RPO framework.

Key Features:
- Cardiomyocyte cell population dynamics
- Action potential generation and propagation
- Excitation-contraction coupling
- Cardiac ion channels (Na+, K+, Ca2+)
- Cardiotoxicity mechanisms (QT prolongation, arrhythmias, contractile dysfunction)
- Integration with Van der Pol cardiac oscillator
- Cardiac biomarkers (Troponin, BNP, CK-MB)

Author: Multi-Organ Chip Architecture Team
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .rpo_organ_chip import (
    OrganChip,
    CellPopulation,
    Receptor,
    ReceptorType,
    Ligand,
    ToxicityMechanism,
    CellularStress,
    SignalTransduction,
    ProteinExpression,
)
from ..cardiac.van_der_pol import VanDerPolOscillator


@dataclass
class IonChannel:
    """
    Cardiac ion channel model

    Implements voltage-gated ion channels for action potential generation
    """
    channel_type: str  # Na+, K+, Ca2+
    conductance: float = 1.0  # mS/cm²
    activation: float = 0.0  # gating variable (0-1)
    inactivation: float = 1.0  # gating variable (0-1)

    # Voltage dependence
    v_half_activation: float = -40.0  # mV
    v_half_inactivation: float = -60.0  # mV
    slope_activation: float = 10.0
    slope_inactivation: float = 10.0

    # Kinetics
    tau_activation: float = 1.0  # ms
    tau_inactivation: float = 10.0  # ms

    # Reversal potential
    e_rev: float = 50.0  # mV

    def steady_state(self, voltage: float, gate_type: str = 'activation') -> float:
        """Boltzmann equation for steady-state gating"""
        if gate_type == 'activation':
            v_half = self.v_half_activation
            slope = self.slope_activation
        else:
            v_half = self.v_half_inactivation
            slope = self.slope_inactivation

        return 1.0 / (1.0 + np.exp((v_half - voltage) / slope))

    def update_gates(self, voltage: float, dt: float) -> None:
        """Update gating variables"""
        # Activation
        m_inf = self.steady_state(voltage, 'activation')
        self.activation += (m_inf - self.activation) / self.tau_activation * dt

        # Inactivation
        h_inf = self.steady_state(voltage, 'inactivation')
        self.inactivation += (h_inf - self.inactivation) / self.tau_inactivation * dt

    def current(self, voltage: float) -> float:
        """Calculate ionic current"""
        return self.conductance * self.activation * self.inactivation * (voltage - self.e_rev)


@dataclass
class ActionPotential:
    """
    Cardiac action potential model

    Simplified model capturing key phases:
    Phase 0: Rapid depolarization (Na+ influx)
    Phase 1: Early repolarization (K+ efflux)
    Phase 2: Plateau (Ca2+ influx)
    Phase 3: Repolarization (K+ efflux)
    Phase 4: Resting potential
    """
    # Membrane potential
    voltage: float = -85.0  # mV (resting)

    # Ion channels
    i_na: IonChannel = field(default_factory=lambda: IonChannel(
        channel_type="Na+",
        conductance=15.0,
        e_rev=50.0,
        v_half_activation=-40.0,
        tau_activation=0.1,
        tau_inactivation=1.0
    ))
    i_ca: IonChannel = field(default_factory=lambda: IonChannel(
        channel_type="Ca2+",
        conductance=0.5,
        e_rev=130.0,
        v_half_activation=-10.0,
        tau_activation=5.0,
        tau_inactivation=50.0
    ))
    i_k: IonChannel = field(default_factory=lambda: IonChannel(
        channel_type="K+",
        conductance=1.0,
        e_rev=-90.0,
        v_half_activation=-30.0,
        tau_activation=10.0,
        tau_inactivation=100.0
    ))

    # Membrane properties
    capacitance: float = 1.0  # μF/cm²
    resting_potential: float = -85.0  # mV

    # Action potential duration
    apd90: float = 300.0  # ms (APD at 90% repolarization)

    # QT interval (surrogate)
    qt_interval: float = 400.0  # ms

    def update(self, stimulus: float, dt: float) -> None:
        """
        Update action potential

        Args:
            stimulus: External stimulus current (μA/cm²)
            dt: Time step (ms)
        """
        # Update ion channel gates
        self.i_na.update_gates(self.voltage, dt)
        self.i_ca.update_gates(self.voltage, dt)
        self.i_k.update_gates(self.voltage, dt)

        # Calculate ionic currents
        i_ion = (self.i_na.current(self.voltage) +
                self.i_ca.current(self.voltage) +
                self.i_k.current(self.voltage))

        # Leak current
        i_leak = 0.05 * (self.voltage - self.resting_potential)

        # Membrane voltage equation
        dv = (stimulus - i_ion - i_leak) / self.capacitance * dt
        self.voltage += dv

        # Update APD90 (simplified)
        if self.voltage > -40.0:  # During action potential
            self.apd90 = 300.0 + (self.i_ca.conductance - 0.5) * 200.0

        # QT interval correlates with APD
        self.qt_interval = self.apd90 * 1.3


@dataclass
class CalciumDynamics:
    """
    Intracellular calcium dynamics for excitation-contraction coupling

    Ca2+ influx → Ca2+-induced Ca2+ release (CICR) → Contraction
    """
    # Calcium concentrations
    ca_cytosol: float = 0.1  # μM (resting)
    ca_sr: float = 1000.0  # μM (sarcoplasmic reticulum)
    ca_peak: float = 1.0  # μM (during contraction)

    # Ca2+ fluxes
    ca_influx: float = 0.0  # from L-type Ca channels
    ca_release: float = 0.0  # from SR (RyR)
    ca_uptake: float = 0.0  # SERCA pump
    ca_extrusion: float = 0.0  # NCX, PMCA

    # Parameters
    ca_sensitivity: float = 1.0  # troponin C sensitivity
    sr_leak: float = 0.01

    def update(self, i_ca_current: float, dt: float) -> None:
        """Update calcium dynamics"""
        # Ca2+ influx from L-type channels
        self.ca_influx = -i_ca_current * 0.01  # Convert current to concentration change

        # Ca2+-induced Ca2+ release from SR
        self.ca_release = self.ca_influx * 10.0 * (self.ca_sr / 1000.0)

        # SR Ca2+ uptake (SERCA)
        self.ca_uptake = 0.5 * self.ca_cytosol

        # Ca2+ extrusion (NCX, PMCA)
        self.ca_extrusion = 0.3 * self.ca_cytosol

        # SR leak
        leak = self.sr_leak * (self.ca_sr / 1000.0)

        # Update cytosolic Ca2+
        d_ca_cytosol = (self.ca_influx + self.ca_release + leak -
                       self.ca_uptake - self.ca_extrusion)
        self.ca_cytosol += d_ca_cytosol * dt
        self.ca_cytosol = max(0.05, min(10.0, self.ca_cytosol))

        # Update SR Ca2+
        d_ca_sr = self.ca_uptake - self.ca_release - leak
        self.ca_sr += d_ca_sr * dt
        self.ca_sr = max(100.0, min(2000.0, self.ca_sr))

        # Track peak Ca2+ for contractility
        self.ca_peak = max(self.ca_cytosol, self.ca_peak * 0.95)

    def contractile_force(self) -> float:
        """Calculate contractile force from Ca2+ transient"""
        # Hill equation for Ca2+-troponin C binding
        ca_binding = (self.ca_cytosol ** 2) / (self.ca_sensitivity ** 2 + self.ca_cytosol ** 2)
        return ca_binding


@dataclass
class CardiomyocyteModel(CellPopulation):
    """
    Cardiomyocyte cell population with electrophysiology and contractility
    """
    # Electrophysiology
    action_potential: ActionPotential = field(default_factory=ActionPotential)
    calcium_dynamics: CalciumDynamics = field(default_factory=CalciumDynamics)

    # Mechanical properties
    contractility: float = 1.0  # relative contractile force
    relaxation_rate: float = 1.0

    # Cardiac oscillator (from existing model)
    oscillator: VanDerPolOscillator = field(default_factory=lambda: VanDerPolOscillator(mu=1.5, omega=1.0))
    oscillator_state: Tuple[float, float] = (1.0, 0.0)

    # Cardiac receptors
    beta1_adrenergic: Optional[Receptor] = None
    m2_muscarinic: Optional[Receptor] = None

    # Cardiac biomarkers
    troponin_i: float = 0.01  # ng/mL (normal < 0.04)
    ck_mb: float = 2.0  # ng/mL (normal < 5)
    bnp: float = 50.0  # pg/mL (normal < 100)

    # Pacing
    heart_rate: float = 70.0  # bpm
    rhythm: str = "sinus"  # sinus, AF, VT, VF

    def __post_init__(self):
        """Initialize cardiomyocyte-specific receptors"""
        super().__post_init__() if hasattr(super(), '__post_init__') else None

        # Beta-1 adrenergic receptor (sympathetic)
        self.beta1_adrenergic = Receptor(
            name="beta1_adrenergic",
            receptor_type=ReceptorType.GPCR,
            total_density=50000.0,
            k_on=1e7,
            k_off=0.1
        )
        self.add_receptor(self.beta1_adrenergic)

        # M2 muscarinic receptor (parasympathetic)
        self.m2_muscarinic = Receptor(
            name="M2_muscarinic",
            receptor_type=ReceptorType.GPCR,
            total_density=30000.0,
            k_on=5e6,
            k_off=0.2
        )
        self.add_receptor(self.m2_muscarinic)

    def update_electrophysiology(self, dt: float) -> None:
        """Update cardiac electrophysiology"""
        # Pacing stimulus
        pacing_cycle = 60000.0 / self.heart_rate  # ms
        stimulus = 10.0 if (self.time * 1000) % pacing_cycle < 2.0 else 0.0

        # Update action potential
        self.action_potential.update(stimulus, dt * 1000)  # Convert s to ms

        # Update calcium dynamics
        ca_current = self.action_potential.i_ca.current(self.action_potential.voltage)
        self.calcium_dynamics.update(ca_current, dt * 1000)

        # Update contractility
        self.contractility = self.calcium_dynamics.contractile_force()

    def update_oscillator(self, dt: float, neural_input: float = 0.0) -> None:
        """Update Van der Pol cardiac oscillator"""
        # Integrate oscillator (maintains rhythmicity)
        self.oscillator_state = self.oscillator.step(
            self.time,
            self.oscillator_state,
            dt,
            input_force=neural_input
        )

        # Oscillator modulates heart rate
        oscillator_amplitude = np.sqrt(self.oscillator_state[0]**2 + self.oscillator_state[1]**2)
        self.heart_rate = 70.0 + oscillator_amplitude * 10.0

    def update_biomarkers(self, dt: float) -> None:
        """Update cardiac injury biomarkers"""
        damage = self.stress.total_stress()

        # Troponin I released with cardiomyocyte damage
        self.troponin_i += (damage * 5.0 - 0.1 * self.troponin_i) * dt

        # CK-MB released with cell death
        cell_death_rate = 1.0 - self.stress.viability()
        self.ck_mb += (cell_death_rate * 50.0 - 0.2 * self.ck_mb) * dt

        # BNP increases with cardiac stress
        self.bnp += (damage * 100.0 + self.stress.mitochondrial_damage * 50.0 - 0.15 * self.bnp) * dt

    def detect_arrhythmia(self) -> str:
        """Detect cardiac arrhythmias based on cellular state"""
        # QT prolongation
        if self.action_potential.qt_interval > 500:
            if np.random.random() < 0.01:  # Risk of torsades
                return "Torsades de Pointes"

        # Irregular rhythm from cellular damage
        if self.stress.total_stress() > 5.0:
            return "Ventricular Tachycardia"

        # Normal sinus rhythm
        if 60 <= self.heart_rate <= 100:
            return "Sinus Rhythm"
        elif self.heart_rate < 60:
            return "Bradycardia"
        else:
            return "Tachycardia"

    def update(self, dt: float) -> None:
        """Update cardiomyocyte population"""
        super().update(dt)
        self.time = getattr(self, 'time', 0.0) + dt

        # Update cardiac-specific functions
        self.update_electrophysiology(dt)
        self.update_oscillator(dt)
        self.update_biomarkers(dt)

        # Update rhythm
        self.rhythm = self.detect_arrhythmia()


class HeartChip(OrganChip):
    """
    Heart-on-chip with cardiomyocyte populations and cardiac function
    """

    def __init__(self):
        super().__init__(organ_name="heart")

        # Heart tissue properties
        self.tissue_properties = {
            'mass': 300.0,  # grams (typical adult heart)
            'cardiac_output': 5.0,  # L/min
            'ejection_fraction': 0.60,  # 60% (normal)
            'stroke_volume': 70.0,  # mL
        }

        # Create cardiomyocyte population
        self.cardiomyocytes = CardiomyocyteModel(
            cell_type="cardiomyocyte",
            cell_count=2e9  # ~2-3 billion cardiomyocytes
        )
        self.add_cell_population(self.cardiomyocytes)

        # Fibroblasts, endothelial cells could be added

    def get_cardiac_function(self) -> Dict[str, float]:
        """Get cardiac function parameters"""
        # Base values modulated by cell viability and contractility
        viability = self.get_viability()
        contractility = self.cardiomyocytes.contractility

        return {
            'heart_rate': self.cardiomyocytes.heart_rate,
            'contractility': contractility,
            'ejection_fraction': self.tissue_properties['ejection_fraction'] * viability * contractility,
            'cardiac_output': self.tissue_properties['cardiac_output'] * viability * contractility,
            'stroke_volume': self.tissue_properties['stroke_volume'] * viability * contractility,
        }

    def get_ecg_parameters(self) -> Dict[str, float]:
        """Get ECG-like parameters"""
        return {
            'heart_rate': self.cardiomyocytes.heart_rate,
            'QT_interval': self.cardiomyocytes.action_potential.qt_interval,
            'QTc': self.cardiomyocytes.action_potential.qt_interval / np.sqrt(self.cardiomyocytes.heart_rate / 60.0),  # Bazett's formula
            'rhythm': self.cardiomyocytes.rhythm,
        }

    def get_biomarkers(self) -> Dict[str, float]:
        """Get cardiac biomarkers"""
        return {
            'troponin_I': self.cardiomyocytes.troponin_i,
            'CK_MB': self.cardiomyocytes.ck_mb,
            'BNP': self.cardiomyocytes.bnp,
        }

    def assess_cardiotoxicity(self) -> Dict[str, any]:
        """
        Assess drug-induced cardiotoxicity

        Returns clinical-grade cardiotoxicity assessment
        """
        function = self.get_cardiac_function()
        ecg = self.get_ecg_parameters()
        biomarkers = self.get_biomarkers()
        viability = self.get_viability()

        # QTc prolongation risk (Torsades de Pointes)
        qtc_risk = "None"
        if ecg['QTc'] > 450:
            qtc_risk = "Moderate"
        if ecg['QTc'] > 500:
            qtc_risk = "High"

        # Contractile dysfunction
        contractile_dysfunction = "None"
        if function['ejection_fraction'] < 0.50:
            contractile_dysfunction = "Mild"
        if function['ejection_fraction'] < 0.40:
            contractile_dysfunction = "Moderate"
        if function['ejection_fraction'] < 0.30:
            contractile_dysfunction = "Severe"

        # Myocardial injury
        myocardial_injury = "None"
        if biomarkers['troponin_I'] > 0.04:
            myocardial_injury = "Mild"
        if biomarkers['troponin_I'] > 0.1:
            myocardial_injury = "Moderate"
        if biomarkers['troponin_I'] > 1.0:
            myocardial_injury = "Severe"

        return {
            'viability': viability,
            'QTc_prolongation': qtc_risk,
            'contractile_dysfunction': contractile_dysfunction,
            'myocardial_injury': myocardial_injury,
            'arrhythmia_risk': self.cardiomyocytes.rhythm,
            'cardiac_output_percent': function['cardiac_output'] / 5.0 * 100,
        }


class CardiacToxicity:
    """
    Models for specific cardiotoxic drugs
    """

    @staticmethod
    def doxorubicin_toxicity(heart_chip: HeartChip, dose_mg_m2: float, duration_hours: float, dt: float = 0.01):
        """
        Model doxorubicin cardiotoxicity

        Mechanism:
        - Mitochondrial damage
        - ROS generation (iron-mediated)
        - Topoisomerase II inhibition
        - Dose-dependent cardiomyopathy

        Cumulative dose > 450 mg/m² → High risk of heart failure
        """
        # Convert dose to concentration (simplified)
        concentration_uM = dose_mg_m2 / 543.5 * 10  # MW of doxorubicin = 543.5

        drug = Ligand(
            name="doxorubicin",
            concentration=concentration_uM,
            molecular_weight=543.5,
            clearance_rate=0.05,  # slow clearance
        )

        # Simulate exposure
        steps = int(duration_hours * 3600 / dt)
        results = []

        for step in range(steps):
            # Doxorubicin mechanisms
            toxicity_signals = {
                ToxicityMechanism.MITOCHONDRIAL_DYSFUNCTION: drug.concentration * 0.5,
                ToxicityMechanism.OXIDATIVE_STRESS: drug.concentration * 0.8,  # High ROS
                ToxicityMechanism.DNA_DAMAGE: drug.concentration * 0.3,
            }

            heart_chip.cardiomyocytes.stress.update(toxicity_signals, dt)

            # Drug clearance
            drug.concentration *= np.exp(-drug.clearance_rate * dt / 3600)

            heart_chip.update(dt)

            if step % 1000 == 0:
                state = heart_chip.get_state()
                state['drug_concentration'] = drug.concentration
                state['cardiac_function'] = heart_chip.get_cardiac_function()
                state['biomarkers'] = heart_chip.get_biomarkers()
                state['toxicity_assessment'] = heart_chip.assess_cardiotoxicity()
                results.append(state)

        return results

    @staticmethod
    def qt_prolonging_drug(heart_chip: HeartChip, drug_name: str, concentration: float,
                          herg_ic50: float, duration_hours: float, dt: float = 0.01):
        """
        Model QT-prolonging drugs (hERG channel blockers)

        Mechanism: Block IKr (hERG/Kv11.1) → Prolonged repolarization → Torsades risk

        Examples: Sotalol, Dofetilide, Quinidine, Azithromycin
        """
        drug = Ligand(
            name=drug_name,
            concentration=concentration,
            clearance_rate=0.15,
        )

        # hERG block
        fraction_blocked = concentration / (herg_ic50 + concentration)

        # Simulate
        steps = int(duration_hours * 3600 / dt)
        results = []

        for step in range(steps):
            # Reduce IK conductance (hERG block)
            heart_chip.cardiomyocytes.action_potential.i_k.conductance = 1.0 * (1.0 - fraction_blocked * 0.8)

            # Update hERG block as drug clears
            drug.concentration *= np.exp(-drug.clearance_rate * dt / 3600)
            fraction_blocked = drug.concentration / (herg_ic50 + drug.concentration)

            heart_chip.update(dt)

            if step % 1000 == 0:
                state = heart_chip.get_state()
                state['drug_concentration'] = drug.concentration
                state['hERG_block'] = fraction_blocked
                state['ecg'] = heart_chip.get_ecg_parameters()
                state['toxicity_assessment'] = heart_chip.assess_cardiotoxicity()
                results.append(state)

        return results


if __name__ == "__main__":
    # Example: Doxorubicin cardiotoxicity
    print("Heart-on-Chip: Doxorubicin Cardiotoxicity Simulation")
    print("=" * 70)

    heart = HeartChip()

    print("\n1. Low dose doxorubicin (50 mg/m²):")
    results_low = CardiacToxicity.doxorubicin_toxicity(
        heart, dose_mg_m2=50, duration_hours=1.0, dt=0.01
    )
    final = results_low[-1]
    print(f"   Viability: {final['viability']:.3f}")
    print(f"   EF: {final['cardiac_function']['ejection_fraction']:.3f}")
    print(f"   Troponin: {final['biomarkers']['troponin_I']:.3f} ng/mL")
    print(f"   Injury: {final['toxicity_assessment']['myocardial_injury']}")

    # Reset
    heart = HeartChip()

    print("\n2. High dose doxorubicin (300 mg/m²):")
    results_high = CardiacToxicity.doxorubicin_toxicity(
        heart, dose_mg_m2=300, duration_hours=1.0, dt=0.01
    )
    final = results_high[-1]
    print(f"   Viability: {final['viability']:.3f}")
    print(f"   EF: {final['cardiac_function']['ejection_fraction']:.3f}")
    print(f"   Troponin: {final['biomarkers']['troponin_I']:.3f} ng/mL")
    print(f"   Injury: {final['toxicity_assessment']['myocardial_injury']}")

    print("\nHeart chip module ready for integration!")
