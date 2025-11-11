"""
Immune System Integration Module

Extends the RPO_ImmuneResponse to provide comprehensive immune system
modeling across multi-organ systems.

Key Features:
- Integration with existing ImmuneSignaling from coupling module
- Systemic inflammatory response
- Cytokine networks
- Immune cell trafficking between organs
- Drug-induced immunotoxicity

Author: Multi-Organ Chip Architecture Team
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .rpo_organ_chip import RPO_ImmuneResponse, CellularStress, OrganChip


@dataclass
class CytokineNetwork:
    """
    Systemic cytokine signaling network
    """
    # Pro-inflammatory cytokines
    tnf_alpha: float = 0.0  # pg/mL
    il1_beta: float = 0.0
    il6: float = 0.0
    il8: float = 0.0

    # Anti-inflammatory cytokines
    il10: float = 0.0
    il4: float = 0.0
    tgf_beta: float = 0.0

    # Chemokines
    mcp1: float = 0.0  # Monocyte chemoattractant
    ccl5: float = 0.0  # RANTES

    # Acute phase proteins
    crp: float = 0.5  # mg/L (C-reactive protein)
    serum_amyloid_a: float = 5.0  # mg/L

    def update(self, organ_damage_signals: Dict[str, float], dt: float) -> None:
        """Update cytokine levels based on organ damage"""
        total_damage = sum(organ_damage_signals.values())

        # Pro-inflammatory response
        self.tnf_alpha += (total_damage * 50.0 - 0.5 * self.tnf_alpha) * dt
        self.il1_beta += (total_damage * 30.0 - 0.4 * self.il1_beta) * dt
        self.il6 += (total_damage * 100.0 + self.tnf_alpha * 2.0 - 0.3 * self.il6) * dt
        self.il8 += (total_damage * 20.0 - 0.4 * self.il8) * dt

        # Anti-inflammatory feedback (Resolution)
        self.il10 += (self.il6 * 0.3 + self.tnf_alpha * 0.2 - 0.3 * self.il10) * dt
        self.il4 += (self.il10 * 0.1 - 0.2 * self.il4) * dt
        self.tgf_beta += (total_damage * 5.0 - 0.1 * self.tgf_beta) * dt

        # Chemokines (recruit immune cells)
        self.mcp1 += (self.tnf_alpha * 1.5 - 0.5 * self.mcp1) * dt
        self.ccl5 += (self.il1_beta * 0.8 - 0.4 * self.ccl5) * dt

        # Acute phase proteins (liver synthesis)
        self.crp += (self.il6 * 0.5 - 0.1 * self.crp) * dt
        self.serum_amyloid_a += (self.il6 * 0.3 + self.il1_beta * 0.2 - 0.05 * self.serum_amyloid_a) * dt

    def inflammation_score(self) -> float:
        """Calculate overall inflammation score"""
        pro_inflammatory = self.tnf_alpha + self.il1_beta + self.il6 + self.il8
        anti_inflammatory = self.il10 + self.il4 + self.tgf_beta
        return (pro_inflammatory - anti_inflammatory) / 100.0

    def sirs_criteria(self) -> int:
        """
        Evaluate Systemic Inflammatory Response Syndrome (SIRS) criteria

        Returns number of SIRS criteria met (0-4)
        """
        criteria_met = 0

        # Temperature (not directly modeled, but inferred from cytokines)
        if self.il1_beta > 100.0 or self.il6 > 500.0:
            criteria_met += 1  # Fever equivalent

        # Heart rate (increased with inflammation)
        if self.tnf_alpha > 100.0:
            criteria_met += 1  # Tachycardia equivalent

        # Respiratory rate (increased with inflammation)
        if self.il8 > 50.0:
            criteria_met += 1  # Tachypnea equivalent

        # WBC (increased)
        if self.mcp1 > 100.0:
            criteria_met += 1  # Leukocytosis equivalent

        return criteria_met


@dataclass
class ImmuneCellCompartment:
    """
    Immune cell populations
    """
    # Innate immune cells
    neutrophils: float = 4000.0  # cells/μL
    monocytes: float = 500.0
    macrophages: float = 200.0
    nk_cells: float = 200.0

    # Adaptive immune cells
    t_cells_cd4: float = 700.0
    t_cells_cd8: float = 400.0
    b_cells: float = 200.0

    # Activation states
    neutrophil_activation: float = 0.0  # 0-1
    macrophage_activation: float = 0.0  # M1 (pro-inflammatory)
    t_cell_activation: float = 0.0

    def update(self, cytokines: CytokineNetwork, dt: float) -> None:
        """Update immune cell populations based on cytokine signals"""
        # Neutrophil expansion with G-CSF (induced by IL-1, TNF)
        neutrophil_growth = (cytokines.il1_beta + cytokines.tnf_alpha) * 0.1
        self.neutrophils += (neutrophil_growth - 0.01 * (self.neutrophils - 4000.0)) * dt

        # Monocyte recruitment
        monocyte_recruitment = cytokines.mcp1 * 0.5
        self.monocytes += (monocyte_recruitment - 0.02 * (self.monocytes - 500.0)) * dt

        # Macrophage polarization
        m1_stimulus = cytokines.tnf_alpha + cytokines.il1_beta
        m2_stimulus = cytokines.il10 + cytokines.il4
        self.macrophage_activation += ((m1_stimulus - m2_stimulus) * 0.001 -
                                      0.1 * self.macrophage_activation) * dt

        # T cell activation
        t_cell_stimulus = cytokines.il6 + cytokines.il1_beta
        self.t_cell_activation += (t_cell_stimulus * 0.002 - 0.05 * self.t_cell_activation) * dt

        # Neutrophil activation
        neutrophil_stimulus = cytokines.il8 + cytokines.tnf_alpha
        self.neutrophil_activation += (neutrophil_stimulus * 0.001 - 0.1 * self.neutrophil_activation) * dt


class SystemicImmuneResponse:
    """
    Integrates immune response across all organs
    """

    def __init__(self):
        self.cytokines = CytokineNetwork()
        self.immune_cells = ImmuneCellCompartment()
        self.organ_immune_responses: Dict[str, RPO_ImmuneResponse] = {}
        self.time: float = 0.0

    def add_organ(self, organ_name: str, immune_response: RPO_ImmuneResponse) -> None:
        """Register organ-specific immune response"""
        self.organ_immune_responses[organ_name] = immune_response

    def update(self, organs: Dict[str, OrganChip], dt: float) -> None:
        """
        Update systemic immune response

        Integrates damage signals from all organs and coordinates response
        """
        self.time += dt

        # Collect damage signals from all organs
        organ_damage_signals = {}
        for organ_name, organ in organs.items():
            total_stress = 0.0
            for population in organ.cell_populations.values():
                total_stress += population.stress.total_stress()
            organ_damage_signals[organ_name] = total_stress

        # Update systemic cytokine network
        self.cytokines.update(organ_damage_signals, dt)

        # Update immune cell populations
        self.immune_cells.update(self.cytokines, dt)

        # Update organ-specific immune responses
        for organ_name, immune_response in self.organ_immune_responses.items():
            if organ_name in organ_damage_signals:
                immune_response.update(organ_damage_signals, dt)

        # Immune cells can cause additional damage (immunopathology)
        if self.immune_cells.neutrophil_activation > 0.7:
            # Activated neutrophils release ROS and proteases
            for organ in organs.values():
                for population in organ.cell_populations.values():
                    # Add oxidative stress from immune response
                    additional_stress = self.immune_cells.neutrophil_activation * 0.1
                    population.stress.oxidative_stress += additional_stress * dt

    def get_state(self) -> Dict:
        """Get current immune system state"""
        return {
            'time': self.time,
            'cytokines': {
                'TNF_alpha': self.cytokines.tnf_alpha,
                'IL1_beta': self.cytokines.il1_beta,
                'IL6': self.cytokines.il6,
                'IL10': self.cytokines.il10,
                'CRP': self.cytokines.crp,
            },
            'immune_cells': {
                'neutrophils': self.immune_cells.neutrophils,
                'monocytes': self.immune_cells.monocytes,
                'macrophages': self.immune_cells.macrophages,
                't_cells': self.immune_cells.t_cells_cd4 + self.immune_cells.t_cells_cd8,
            },
            'inflammation_score': self.cytokines.inflammation_score(),
            'SIRS_criteria': self.cytokines.sirs_criteria(),
        }

    def assess_sepsis_risk(self) -> Dict[str, any]:
        """
        Assess risk of sepsis/SIRS

        SIRS → Sepsis → Severe Sepsis → Septic Shock
        """
        sirs_count = self.cytokines.sirs_criteria()
        inflammation = self.cytokines.inflammation_score()

        if sirs_count >= 2:
            if inflammation > 10.0:
                severity = "Severe SIRS / Sepsis"
                risk = "High"
            else:
                severity = "SIRS"
                risk = "Moderate"
        else:
            severity = "Normal"
            risk = "Low"

        return {
            'severity': severity,
            'risk': risk,
            'SIRS_criteria_met': sirs_count,
            'inflammation_score': inflammation,
            'cytokine_storm': self.cytokines.il6 > 1000.0 or self.cytokines.tnf_alpha > 500.0
        }


# Integration with existing coupling module
class ImmuneSignalingBridge:
    """
    Bridge between new immune system and existing heart-brain coupling
    """

    @staticmethod
    def immune_to_neural_signal(immune_response: SystemicImmuneResponse) -> float:
        """
        Convert immune signals to neural modulation

        Cytokines like IL-1β and TNF-α affect neural activity
        """
        # Pro-inflammatory cytokines can increase neural excitability
        neural_modulation = (immune_response.cytokines.il1_beta * 0.001 +
                           immune_response.cytokines.tnf_alpha * 0.0005)
        return np.clip(neural_modulation, -1.0, 1.0)

    @staticmethod
    def immune_to_cardiac_signal(immune_response: SystemicImmuneResponse) -> float:
        """
        Convert immune signals to cardiac modulation

        Cytokines affect cardiac contractility and rhythm
        """
        # Inflammation reduces cardiac contractility
        cardiac_suppression = (immune_response.cytokines.tnf_alpha * 0.001 +
                             immune_response.cytokines.il6 * 0.0005)
        return -np.clip(cardiac_suppression, 0.0, 1.0)  # Negative = suppression


if __name__ == "__main__":
    # Example: Systemic immune response to multi-organ injury
    print("Systemic Immune Response - Multi-Organ Injury Example")
    print("=" * 70)

    immune_system = SystemicImmuneResponse()

    # Simulate organ injury
    print("\nSimulating multi-organ injury...")
    for step in range(100):
        t = step * 0.1

        # Simulated organ damage signals
        organ_damage = {
            'liver': 3.0 if step < 50 else 1.0,  # Initial liver injury
            'heart': 1.5 if step > 30 else 0.5,  # Secondary cardiac stress
        }

        immune_system.cytokines.update(organ_damage, dt=0.1)
        immune_system.immune_cells.update(immune_system.cytokines, dt=0.1)

        if step % 20 == 0:
            state = immune_system.get_state()
            print(f"\nt = {t:.1f}h:")
            print(f"  TNF-α: {state['cytokines']['TNF_alpha']:.1f} pg/mL")
            print(f"  IL-6: {state['cytokines']['IL6']:.1f} pg/mL")
            print(f"  CRP: {state['cytokines']['CRP']:.1f} mg/L")
            print(f"  Inflammation score: {state['inflammation_score']:.2f}")

    # Assess sepsis risk
    risk_assessment = immune_system.assess_sepsis_risk()
    print(f"\nFinal Assessment:")
    print(f"  Severity: {risk_assessment['severity']}")
    print(f"  Risk: {risk_assessment['risk']}")
    print(f"  SIRS criteria met: {risk_assessment['SIRS_criteria_met']}/4")

    print("\nImmune system module ready for integration!")
