"""
Comprehensive Recursive Planck Operator (RPO) Framework for Organ-on-Chip Systems

Applies unified RPO memory kernel across all biological scales:
- Cellular (metabolism, signaling)
- Tissue (organ function)
- Systemic (circulation, integration)

Author: Donte Lightfoot (Lightfoot Technology / Primal Logic)
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Callable, Optional
from dataclasses import dataclass

from .rpo import RPOVariable, RPOParameters


# ==============================================================================
# HEART-BRAIN COUPLING WITH RPO
# ==============================================================================

class RPO_HeartBrainCoupling:
    """
    Heart-brain coupling using RPO for both neural and cardiac state.
    Replaces ad-hoc adaptation with unified memory operator.
    """

    def __init__(self):
        # Neural RPO: slow adaptation (long memory)
        self.x_brain = RPOVariable(
            lambda_decay=0.3,     # Slow neural decay
            beta_feedback=0.25,   # Moderate memory influence
            alpha_memory=0.01     # Very slow memory (1/α ≈ 100 time units)
        )

        # Cardiac RPO: faster dynamics (shorter memory)
        self.x_heart = RPOVariable(
            lambda_decay=0.8,     # Faster cardiac decay
            beta_feedback=0.4,    # Stronger memory influence
            alpha_memory=0.1      # Faster memory formation
        )

        # Coupling strengths
        self.k_brain_to_heart = 0.3
        self.k_heart_to_brain = 0.2

    def coupled_derivatives(
        self,
        state: np.ndarray,  # [z_brain, m_brain, z_heart, m_heart]
        t: float
    ) -> np.ndarray:
        """Coupled heart-brain dynamics with bidirectional RPO feedback"""
        z_b, m_b, z_h, m_h = state

        # External stimuli (could be time-varying)
        S_brain = 0.1 * np.sin(0.3 * t)  # Slow neural oscillation
        S_heart = 0.2 * np.sin(1.0 * t)  # Faster cardiac oscillation

        # Cross-coupling terms
        brain_to_heart_coupling = self.k_brain_to_heart * z_b
        heart_to_brain_coupling = self.k_heart_to_brain * z_h

        # Brain RPO with cardiac influence
        dz_b, dm_b = self.x_brain.derivatives(
            z_b, m_b,
            stimulus=S_brain + heart_to_brain_coupling
        )

        # Heart RPO with neural influence
        dz_h, dm_h = self.x_heart.derivatives(
            z_h, m_h,
            stimulus=S_heart + brain_to_heart_coupling
        )

        return np.array([dz_b, dm_b, dz_h, dm_h])


# ==============================================================================
# LIVER METABOLISM WITH RPO
# ==============================================================================

class RPO_LiverMetabolism:
    """
    Liver drug metabolism with RPO for enzyme adaptation and toxicity accumulation.
    """

    def __init__(self):
        # CYP450 activity: adapts to drug exposure with memory
        self.CYP450_activity = RPOVariable(
            lambda_decay=0.1,     # Slow enzyme degradation
            beta_feedback=0.08,   # Weak memory (prevent over-induction)
            alpha_memory=0.05     # Slow adaptation to chronic exposure
        )

        # Hepatotoxicity: accumulates with memory of damage
        self.toxicity_state = RPOVariable(
            lambda_decay=0.2,     # Repair processes
            beta_feedback=0.15,   # Damage begets more damage (inflammation)
            alpha_memory=0.1      # Memory of past insults
        )

        # Metabolic parameters
        self.Vmax_base = 100.0     # Max metabolism rate (μM/hr)
        self.Km = 10.0             # Michaelis constant (μM)

    def metabolism_with_adaptation(
        self,
        drug_concentration: float,
        CYP_state: Tuple[float, float],     # (z_CYP, m_CYP)
        toxicity_state: Tuple[float, float]  # (z_tox, m_tox)
    ) -> Tuple[float, Tuple[float, float], Tuple[float, float]]:
        """
        Compute drug clearance with adaptive enzyme activity.

        Returns:
            (clearance_rate, new_CYP_state_derivs, new_toxicity_state_derivs)
        """
        z_CYP, m_CYP = CYP_state
        z_tox, m_tox = toxicity_state

        # Effective enzyme activity (current + memory)
        CYP_effective = 1.0 + z_CYP + 0.5 * m_CYP

        # Michaelis-Menten with adaptive Vmax
        Vmax_effective = self.Vmax_base * CYP_effective * (1 - 0.5 * z_tox)
        clearance = (Vmax_effective * drug_concentration) / (self.Km + drug_concentration)

        # CYP induction stimulus (drug concentration)
        S_CYP = 0.01 * drug_concentration

        # Toxicity stimulus (drug + metabolites)
        S_tox = 0.005 * drug_concentration * (1 + 0.5 * z_tox)  # Amplified by existing damage

        # Update RPO states
        dz_CYP, dm_CYP = self.CYP450_activity.derivatives(z_CYP, m_CYP, stimulus=S_CYP)
        dz_tox, dm_tox = self.toxicity_state.derivatives(z_tox, m_tox, stimulus=S_tox)

        return clearance, (dz_CYP, dm_CYP), (dz_tox, dm_tox)


# ==============================================================================
# IMMUNE RESPONSE WITH RPO
# ==============================================================================

class RPO_ImmuneResponse:
    """
    Immune/inflammatory signaling with RPO memory.
    Cytokine dynamics with history-dependent activation/resolution.
    """

    def __init__(self):
        # Pro-inflammatory cytokines (TNF-α, IL-6)
        self.inflammatory_state = RPOVariable(
            lambda_decay=0.5,     # Active resolution mechanisms
            beta_feedback=0.4,    # Self-amplifying inflammation
            alpha_memory=0.2      # Medium-term immune memory
        )

        # Anti-inflammatory / regulatory response
        self.regulatory_state = RPOVariable(
            lambda_decay=0.3,     # Slower resolution (sustained)
            beta_feedback=0.2,    # Moderate memory
            alpha_memory=0.1      # Long-term tolerance
        )

    def immune_dynamics(
        self,
        damage_signal: float,           # From tissue injury (liver, heart, etc)
        pathogen_load: float,           # External antigen
        inflammatory_state: Tuple[float, float],   # (z_inf, m_inf)
        regulatory_state: Tuple[float, float]      # (z_reg, m_reg)
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Compute inflammatory and regulatory dynamics.

        Returns:
            (inflammatory_derivs, regulatory_derivs)
        """
        z_inf, m_inf = inflammatory_state
        z_reg, m_reg = regulatory_state

        # Inflammatory stimulus: damage + pathogen - regulation
        S_inf = damage_signal + pathogen_load - 0.5 * z_reg

        # Regulatory stimulus: inflammation (counter-regulatory)
        S_reg = 0.3 * z_inf

        dz_inf, dm_inf = self.inflammatory_state.derivatives(z_inf, m_inf, stimulus=S_inf)
        dz_reg, dm_reg = self.regulatory_state.derivatives(z_reg, m_reg, stimulus=S_reg)

        return (dz_inf, dm_inf), (dz_reg, dm_reg)


# ==============================================================================
# METABOLIC STRESS WITH RPO
# ==============================================================================

class RPO_MetabolicStress:
    """
    Cellular metabolic stress (ATP depletion, oxidative damage) with memory.
    """

    def __init__(self):
        # ATP/energy state
        self.energy_state = RPOVariable(
            lambda_decay=0.4,     # Consumption rate
            beta_feedback=0.3,    # Mitochondrial adaptation
            alpha_memory=0.15     # Memory of energy crisis
        )

        # Oxidative stress
        self.ROS_state = RPOVariable(
            lambda_decay=0.6,     # Antioxidant clearance
            beta_feedback=0.5,    # Oxidative cascade (self-amplifying)
            alpha_memory=0.2      # Cellular damage memory
        )

    def metabolic_dynamics(
        self,
        ATP_production: float,
        ATP_demand: float,
        drug_induced_ROS: float,
        energy_state: Tuple[float, float],
        ROS_state: Tuple[float, float]
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Energy and oxidative stress dynamics"""
        z_ATP, m_ATP = energy_state
        z_ROS, m_ROS = ROS_state

        # Energy balance
        S_ATP = ATP_production - ATP_demand - 0.3 * z_ROS  # ROS damages mitochondria

        # ROS production
        S_ROS = drug_induced_ROS + 0.2 * (1.0 / (z_ATP + 0.1))  # Energy deficit → ROS

        dz_ATP, dm_ATP = self.energy_state.derivatives(z_ATP, m_ATP, stimulus=S_ATP)
        dz_ROS, dm_ROS = self.ROS_state.derivatives(z_ROS, m_ROS, stimulus=S_ROS)

        return (dz_ATP, dm_ATP), (dz_ROS, dm_ROS)


# ==============================================================================
# INTEGRATED MULTISCALE MODEL
# ==============================================================================

class RPO_OrganChipSuite:
    """
    Complete organ-on-chip digital twin using RPO across all scales.

    State vector organization:
    - Heart: [z_h, m_h]
    - Brain: [z_b, m_b]
    - Liver CYP: [z_cyp, m_cyp]
    - Liver toxicity: [z_tox, m_tox]
    - Immune inflammatory: [z_inf, m_inf]
    - Immune regulatory: [z_reg, m_reg]
    - Metabolic ATP: [z_ATP, m_ATP]
    - Metabolic ROS: [z_ROS, m_ROS]
    - Drug concentration: [drug]
    - Metabolite concentration: [metabolite]

    Total: 18 state variables
    """

    def __init__(self):
        self.heart_brain = RPO_HeartBrainCoupling()
        self.liver = RPO_LiverMetabolism()
        self.immune = RPO_ImmuneResponse()
        self.metabolic = RPO_MetabolicStress()

        # Circulation parameters
        self.cardiac_output = 5.0  # L/min
        self.hepatic_fraction = 0.25
        self.volume_distribution = 50.0  # L

    def system_derivatives(
        self,
        state: np.ndarray,
        t: float,
        drug_dose: float
    ) -> np.ndarray:
        """Complete multiscale dynamics"""
        # Unpack state
        z_h, m_h, z_b, m_b = state[0:4]
        z_cyp, m_cyp, z_tox, m_tox = state[4:8]
        z_inf, m_inf, z_reg, m_reg = state[8:12]
        z_ATP, m_ATP, z_ROS, m_ROS = state[12:16]
        drug, metabolite = state[16:18]

        # Heart-brain coupling
        heart_brain_derivs = self.heart_brain.coupled_derivatives(
            np.array([z_b, m_b, z_h, m_h]), t
        )

        # Liver metabolism
        clearance, (dz_cyp, dm_cyp), (dz_tox, dm_tox) = \
            self.liver.metabolism_with_adaptation(
                drug, (z_cyp, m_cyp), (z_tox, m_tox)
            )

        # Drug/metabolite PK
        drug_input = drug_dose
        drug_clearance = clearance
        metabolite_production = clearance
        metabolite_clearance = 0.5 * metabolite

        dDrug = drug_input - drug_clearance
        dMetabolite = metabolite_production - metabolite_clearance

        # Immune response (damage from toxicity + drug directly)
        damage_signal = z_tox + 0.1 * drug
        pathogen_load = 0.0  # Could model infection

        (dz_inf, dm_inf), (dz_reg, dm_reg) = self.immune.immune_dynamics(
            damage_signal, pathogen_load, (z_inf, m_inf), (z_reg, m_reg)
        )

        # Metabolic stress
        ATP_production = 2.0 * (1 - 0.3 * z_inf)  # Inflammation impairs metabolism
        ATP_demand = 1.5 + 0.5 * z_h  # Cardiac work
        drug_ROS = 0.1 * (drug + 2 * metabolite)

        (dz_ATP, dm_ATP), (dz_ROS, dm_ROS) = self.metabolic.metabolic_dynamics(
            ATP_production, ATP_demand, drug_ROS,
            (z_ATP, m_ATP), (z_ROS, m_ROS)
        )

        # Assemble derivatives
        return np.array([
            heart_brain_derivs[2], heart_brain_derivs[3],  # Heart
            heart_brain_derivs[0], heart_brain_derivs[1],  # Brain
            dz_cyp, dm_cyp, dz_tox, dm_tox,                # Liver
            dz_inf, dm_inf, dz_reg, dm_reg,                # Immune
            dz_ATP, dm_ATP, dz_ROS, dm_ROS,                # Metabolic
            dDrug, dMetabolite                              # PK
        ])

    def simulate(
        self,
        t_span: Tuple[float, float],
        drug_schedule: Callable[[float], float],
        dt: float = 0.01
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Run full multiscale simulation"""
        t_start, t_end = t_span
        n_steps = int((t_end - t_start) / dt)

        times = np.linspace(t_start, t_end, n_steps)
        states = np.zeros((n_steps, 18))

        # Initial conditions (all at rest)
        states[0] = np.zeros(18)

        # RK4 integration
        for i in range(1, n_steps):
            t = times[i-1]
            y = states[i-1]
            drug_dose = drug_schedule(t)

            k1 = self.system_derivatives(y, t, drug_dose)
            k2 = self.system_derivatives(y + 0.5*dt*k1, t + 0.5*dt, drug_dose)
            k3 = self.system_derivatives(y + 0.5*dt*k2, t + 0.5*dt, drug_dose)
            k4 = self.system_derivatives(y + dt*k3, t + dt, drug_dose)

            states[i] = y + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

        return times, states


if __name__ == "__main__":
    print("=" * 70)
    print("RECURSIVE PLANCK OPERATOR (RPO) MULTISCALE FRAMEWORK")
    print("Unified memory kernel across biological timescales")
    print("=" * 70)

    print("\n1. Testing RPO Organ-Chip Suite...")
    suite = RPO_OrganChipSuite()

    # Drug dosing: pulse at t=0, then decay
    def drug_schedule(t):
        if t < 0.1:
            return 100.0  # Bolus dose
        else:
            return 0.0

    print("   Running 48-hour multiscale simulation...")
    times, states = suite.simulate((0, 48), drug_schedule, dt=0.1)

    print(f"\n   Timepoint Analysis:")
    print(f"   {'Time':<8} {'Drug':<10} {'Toxicity':<12} {'Inflammation':<12} {'Heart':<10}")
    print("   " + "-" * 60)

    for tp in [0, 6, 12, 24, 48]:
        idx = int(tp / 0.1)
        if idx < len(times):
            drug = states[idx, 16]
            tox = states[idx, 6]   # z_tox
            inf = states[idx, 8]   # z_inf
            heart = states[idx, 0]  # z_h
            print(f"   {tp:<8.1f} {drug:<10.2f} {tox:<12.3f} {inf:<12.3f} {heart:<10.3f}")

    print("\n" + "=" * 70)
    print("KEY ADVANTAGES OF RPO FRAMEWORK:")
    print("=" * 70)
    print("✓ UNIFIED KERNEL: Same math for synaptic plasticity, enzyme")
    print("               adaptation, immune memory, metabolic stress")
    print("✓ STABILITY: Analytic stability conditions (λ > β)")
    print("✓ INTERPRETABLE: z = current state, m = weighted memory")
    print("✓ NO AD-HOC FILTERS: Replaces arbitrary low-pass with principled operator")
    print("✓ PATENT-WORTHY: Novel mathematical framework with broad applicability")
    print("=" * 70)
