"""Ligand-receptor binding kinetics and competitive inhibition models.

This module implements mechanistic models of receptor-mediated drug effects
including:
- Receptor occupancy dynamics
- Competitive and non-competitive inhibition
- Receptor desensitization and internalization
- Target-mediated drug disposition (TMDD)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, List
import math


@dataclass
class BindingParameters:
    """Parameters for ligand-receptor binding kinetics.

    Attributes
    ----------
    kon : float
        Association rate constant (1/(nM·s))
    koff : float
        Dissociation rate constant (1/s)
    kint : float
        Receptor internalization rate (1/s)
    ksyn : float
        Receptor synthesis rate (nM/s)
    kdeg : float
        Receptor degradation rate (1/s)
    Rtot : float
        Total receptor concentration (nM)
    Kd : float
        Equilibrium dissociation constant (nM), computed from kon/koff
    """

    kon: float = 0.1  # 1/(nM·s)
    koff: float = 0.01  # 1/s
    kint: float = 0.001  # 1/s - receptor internalization
    ksyn: float = 0.1  # nM/s - receptor synthesis
    kdeg: float = 0.01  # 1/s - receptor degradation
    Rtot: float = 100.0  # nM - total receptor pool

    @property
    def Kd(self) -> float:
        """Equilibrium dissociation constant (nM)."""
        return self.koff / self.kon if self.kon > 0 else float('inf')

    @property
    def affinity(self) -> float:
        """Binding affinity (1/Kd)."""
        return 1.0 / self.Kd if self.Kd > 0 else 0.0


@dataclass
class LigandReceptorBinding:
    """Mechanistic model of ligand-receptor binding dynamics.

    State variables:
    - L: Free ligand concentration (nM)
    - R: Free receptor concentration (nM)
    - LR: Ligand-receptor complex concentration (nM)
    - Rint: Internalized receptor-ligand complex (nM)

    The model captures:
    - Reversible binding: L + R <-> LR
    - Receptor synthesis and degradation
    - Complex internalization and degradation
    """

    params: BindingParameters = field(default_factory=BindingParameters)

    def derivatives(
        self,
        t: float,
        state: Tuple[float, float, float, float],
        ligand_input: float = 0.0
    ) -> Tuple[float, float, float, float]:
        """Compute time derivatives for ligand-receptor system.

        Parameters
        ----------
        t : float
            Current time (s)
        state : tuple
            (L, R, LR, Rint) concentrations (nM)
        ligand_input : float
            External ligand input rate (nM/s)

        Returns
        -------
        tuple
            Time derivatives (dL/dt, dR/dt, dLR/dt, dRint/dt)
        """
        L, R, LR, Rint = state
        p = self.params

        # Binding kinetics: L + R <-> LR
        binding_rate = p.kon * L * R
        unbinding_rate = p.koff * LR

        # Free ligand dynamics
        dL = ligand_input - binding_rate + unbinding_rate

        # Free receptor dynamics (synthesis, degradation, binding)
        dR = p.ksyn - p.kdeg * R - binding_rate + unbinding_rate

        # Bound complex dynamics
        dLR = binding_rate - unbinding_rate - p.kint * LR

        # Internalized complex dynamics
        dRint = p.kint * LR - p.kdeg * Rint

        return dL, dR, dLR, dRint

    def steady_state(self, ligand_conc: float) -> Tuple[float, float, float, float]:
        """Compute steady-state receptor occupancy for given ligand concentration.

        Parameters
        ----------
        ligand_conc : float
            Free ligand concentration (nM)

        Returns
        -------
        tuple
            Steady-state (L, R, LR, Rint) concentrations
        """
        p = self.params

        # At steady state without internalization, simplified:
        # R_free = Rtot / (1 + L/Kd)
        # LR = Rtot * (L/Kd) / (1 + L/Kd)

        R_free = p.Rtot / (1.0 + ligand_conc / p.Kd)
        LR = p.Rtot * ligand_conc / (p.Kd + ligand_conc)

        # Account for internalization
        Rint = (p.kint / p.kdeg) * LR if p.kdeg > 0 else 0.0

        return ligand_conc, R_free, LR, Rint

    def occupancy(self, state: Tuple[float, float, float, float]) -> float:
        """Calculate fraction of receptors bound to ligand.

        Parameters
        ----------
        state : tuple
            (L, R, LR, Rint) concentrations

        Returns
        -------
        float
            Receptor occupancy fraction [0, 1]
        """
        _, R, LR, Rint = state
        total_receptors = R + LR + Rint

        if total_receptors <= 0:
            return 0.0

        return LR / total_receptors

    def step(
        self,
        t: float,
        state: Tuple[float, float, float, float],
        dt: float,
        ligand_input: float = 0.0
    ) -> Tuple[float, float, float, float]:
        """Advance system by one Euler step.

        Parameters
        ----------
        t : float
            Current time (s)
        state : tuple
            Current state (L, R, LR, Rint)
        dt : float
            Time step (s)
        ligand_input : float
            Ligand input rate (nM/s)

        Returns
        -------
        tuple
            Updated state
        """
        dL, dR, dLR, dRint = self.derivatives(t, state, ligand_input)
        L, R, LR, Rint = state

        # Ensure non-negative concentrations
        L_new = max(0.0, L + dt * dL)
        R_new = max(0.0, R + dt * dR)
        LR_new = max(0.0, LR + dt * dLR)
        Rint_new = max(0.0, Rint + dt * dRint)

        return L_new, R_new, LR_new, Rint_new


@dataclass
class CompetitiveInhibition:
    """Model of competitive inhibition between drug and endogenous ligand.

    Describes competition between a drug (D) and native ligand (L) for
    the same receptor binding site.
    """

    drug_binding: LigandReceptorBinding = field(default_factory=LigandReceptorBinding)
    ligand_binding: LigandReceptorBinding = field(default_factory=LigandReceptorBinding)

    def effective_kd(self, drug_conc: float, ligand_conc: float) -> Tuple[float, float]:
        """Calculate effective Kd values under competitive inhibition.

        Parameters
        ----------
        drug_conc : float
            Drug concentration (nM)
        ligand_conc : float
            Ligand concentration (nM)

        Returns
        -------
        tuple
            (Kd_drug_eff, Kd_ligand_eff) in presence of competitor
        """
        Kd_drug = self.drug_binding.params.Kd
        Kd_ligand = self.ligand_binding.params.Kd

        # Effective Kd increases in presence of competitor
        Kd_drug_eff = Kd_drug * (1.0 + ligand_conc / Kd_ligand)
        Kd_ligand_eff = Kd_ligand * (1.0 + drug_conc / Kd_drug)

        return Kd_drug_eff, Kd_ligand_eff

    def fractional_occupancy(
        self,
        drug_conc: float,
        ligand_conc: float,
        total_receptors: float
    ) -> Tuple[float, float]:
        """Calculate fraction of receptors bound to drug vs ligand.

        Parameters
        ----------
        drug_conc : float
            Drug concentration (nM)
        ligand_conc : float
            Native ligand concentration (nM)
        total_receptors : float
            Total receptor concentration (nM)

        Returns
        -------
        tuple
            (drug_occupancy, ligand_occupancy) fractions
        """
        Kd_drug = self.drug_binding.params.Kd
        Kd_ligand = self.ligand_binding.params.Kd

        denominator = 1.0 + drug_conc / Kd_drug + ligand_conc / Kd_ligand

        drug_occupancy = (drug_conc / Kd_drug) / denominator
        ligand_occupancy = (ligand_conc / Kd_ligand) / denominator

        return drug_occupancy, ligand_occupancy


@dataclass
class ReceptorDynamics:
    """Extended receptor model with desensitization and trafficking.

    Models receptor states:
    - R: Active, surface receptors
    - Rd: Desensitized receptors
    - Ri: Internalized receptors
    - LR: Ligand-bound surface receptors
    """

    params: BindingParameters = field(default_factory=BindingParameters)
    kdes: float = 0.01  # Desensitization rate (1/s)
    kresens: float = 0.001  # Resensitization rate (1/s)
    krecycle: float = 0.005  # Receptor recycling rate (1/s)

    def derivatives(
        self,
        t: float,
        state: Tuple[float, float, float, float, float],
        ligand_conc: float = 0.0
    ) -> Tuple[float, float, float, float, float]:
        """Compute derivatives for extended receptor model.

        Parameters
        ----------
        t : float
            Time (s)
        state : tuple
            (L, R, Rd, Ri, LR) - ligand, active receptors, desensitized,
            internalized, and bound receptors
        ligand_conc : float
            External ligand concentration (nM)

        Returns
        -------
        tuple
            Time derivatives
        """
        L, R, Rd, Ri, LR = state
        p = self.params

        # Binding kinetics
        binding = p.kon * L * R
        unbinding = p.koff * LR

        # Ligand dynamics
        dL = -binding + unbinding

        # Active receptor dynamics
        dR = p.ksyn + self.kresens * Rd + self.krecycle * Ri - binding + unbinding - self.kdes * LR - p.kdeg * R

        # Desensitized receptor dynamics
        dRd = self.kdes * LR - self.kresens * Rd - p.kdeg * Rd

        # Internalized receptor dynamics
        dRi = p.kint * LR - self.krecycle * Ri - p.kdeg * Ri

        # Ligand-receptor complex dynamics
        dLR = binding - unbinding - self.kdes * LR - p.kint * LR

        return dL, dR, dRd, dRi, dLR
