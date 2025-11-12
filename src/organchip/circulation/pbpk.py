"""Physiologically-based pharmacokinetic (PBPK) circulation model.

This module implements:
- Multi-compartment PBPK models
- Organ blood flow distribution
- Drug distribution and clearance
- Tissue partitioning
- Organ-organ coupling via circulation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Dict, List
import math


@dataclass
class PBPKParameters:
    """Physiological parameters for PBPK model.

    Attributes
    ----------
    cardiac_output : float
        Cardiac output (L/h)
    organ_blood_flows : Dict[str, float]
        Fractional blood flows to each organ
    organ_volumes : Dict[str, float]
        Organ volumes (L)
    partition_coefficients : Dict[str, float]
        Tissue:plasma partition coefficients (Kp)
    """

    # Hemodynamic parameters (scaled for 70kg human)
    cardiac_output: float = 300.0  # L/h (5 L/min)
    blood_volume: float = 5.0      # L

    # Fractional organ blood flows (must sum to ~1.0)
    organ_blood_flows: Dict[str, float] = field(default_factory=lambda: {
        'brain': 0.12,
        'heart': 0.04,
        'liver': 0.25,    # Includes portal + arterial
        'kidney': 0.19,
        'muscle': 0.17,
        'adipose': 0.05,
        'gut': 0.15,
        'other': 0.03,
    })

    # Organ volumes (L)
    organ_volumes: Dict[str, float] = field(default_factory=lambda: {
        'plasma': 3.0,
        'brain': 1.4,
        'heart': 0.3,
        'liver': 1.8,
        'kidney': 0.3,
        'muscle': 20.0,
        'adipose': 10.0,
        'gut': 1.0,
        'other': 5.0,
    })

    # Tissue:plasma partition coefficients (drug-specific)
    partition_coefficients: Dict[str, float] = field(default_factory=lambda: {
        'brain': 1.0,
        'heart': 1.2,
        'liver': 3.0,
        'kidney': 2.0,
        'muscle': 0.8,
        'adipose': 0.3,
        'gut': 1.5,
        'other': 1.0,
    })

    # Clearance parameters
    hepatic_clearance: float = 10.0    # L/h
    renal_clearance: float = 5.0       # L/h


@dataclass
class CompartmentModel:
    """Simple multi-compartment PK model.

    Classic 1-, 2-, or 3-compartment models for drug disposition.
    """

    # Compartment volumes (L)
    V_central: float = 3.0
    V_peripheral1: float = 10.0
    V_peripheral2: float = 20.0

    # Distribution rate constants (1/h)
    k12: float = 1.0   # Central to peripheral 1
    k21: float = 0.5   # Peripheral 1 to central
    k13: float = 0.2   # Central to peripheral 2
    k31: float = 0.1   # Peripheral 2 to central

    # Elimination from central compartment (1/h)
    ke: float = 0.5

    def derivatives_2comp(
        self,
        t: float,
        state: Tuple[float, float],
        infusion_rate: float = 0.0
    ) -> Tuple[float, float]:
        """Two-compartment model derivatives.

        Parameters
        ----------
        t : float
            Time (h)
        state : tuple
            (A_central, A_peripheral) - amounts in each compartment (mg)
        infusion_rate : float
            Drug infusion rate (mg/h)

        Returns
        -------
        tuple
            (dA_central/dt, dA_peripheral/dt)
        """
        A_central, A_peripheral = state

        dA_central = (
            infusion_rate
            - self.ke * A_central
            - self.k12 * A_central
            + self.k21 * A_peripheral
        )

        dA_peripheral = (
            self.k12 * A_central
            - self.k21 * A_peripheral
        )

        return dA_central, dA_peripheral

    def derivatives_3comp(
        self,
        t: float,
        state: Tuple[float, float, float],
        infusion_rate: float = 0.0
    ) -> Tuple[float, float, float]:
        """Three-compartment model derivatives.

        Parameters
        ----------
        t : float
            Time (h)
        state : tuple
            (A_central, A_peripheral1, A_peripheral2) amounts (mg)
        infusion_rate : float
            Drug infusion rate (mg/h)

        Returns
        -------
        tuple
            Time derivatives
        """
        A_central, A_periph1, A_periph2 = state

        dA_central = (
            infusion_rate
            - self.ke * A_central
            - self.k12 * A_central + self.k21 * A_periph1
            - self.k13 * A_central + self.k31 * A_periph2
        )

        dA_periph1 = self.k12 * A_central - self.k21 * A_periph1
        dA_periph2 = self.k13 * A_central - self.k31 * A_periph2

        return dA_central, dA_periph1, dA_periph2


@dataclass
class SystemicCirculation:
    """Full PBPK model with organ-specific compartments.

    Models drug distribution through major organs connected
    by blood circulation.
    """

    params: PBPKParameters = field(default_factory=PBPKParameters)

    def get_organ_flow(self, organ: str) -> float:
        """Get blood flow to specific organ.

        Parameters
        ----------
        organ : str
            Organ name

        Returns
        -------
        float
            Blood flow (L/h)
        """
        frac = self.params.organ_blood_flows.get(organ, 0.0)
        return frac * self.params.cardiac_output

    def tissue_concentration(
        self,
        tissue_amount: float,
        organ: str
    ) -> float:
        """Calculate tissue concentration from amount.

        Parameters
        ----------
        tissue_amount : float
            Amount of drug in tissue (mg)
        organ : str
            Organ name

        Returns
        -------
        float
            Tissue concentration (mg/L)
        """
        volume = self.params.organ_volumes.get(organ, 1.0)
        return tissue_amount / volume if volume > 0 else 0.0

    def plasma_concentration_from_tissue(
        self,
        tissue_conc: float,
        organ: str
    ) -> float:
        """Calculate plasma concentration in equilibrium with tissue.

        Parameters
        ----------
        tissue_conc : float
            Tissue concentration (mg/L)
        organ : str
            Organ name

        Returns
        -------
        float
            Plasma concentration (mg/L)
        """
        Kp = self.params.partition_coefficients.get(organ, 1.0)
        return tissue_conc / Kp if Kp > 0 else tissue_conc


@dataclass
class MultiOrganPBPK:
    """Multi-organ PBPK model integrating liver, heart, and other tissues.

    State variables:
    - Plasma drug concentration
    - Drug amount in each organ
    - Metabolite concentrations
    """

    circulation: SystemicCirculation = field(default_factory=SystemicCirculation)

    # Organ list for systematic iteration
    organs: List[str] = field(default_factory=lambda: [
        'brain', 'heart', 'liver', 'kidney', 'muscle', 'adipose', 'gut'
    ])

    def derivatives(
        self,
        t: float,
        state: Dict[str, float],
        dose_rate: float = 0.0
    ) -> Dict[str, float]:
        """Compute derivatives for multi-organ PBPK model.

        Parameters
        ----------
        t : float
            Time (h)
        state : dict
            Drug amounts in plasma and each organ (mg)
            Keys: 'plasma', 'brain', 'heart', 'liver', etc.
        dose_rate : float
            Drug dosing rate into plasma (mg/h)

        Returns
        -------
        dict
            Time derivatives (dAmount/dt)
        """
        params = self.circulation.params
        derivatives = {}

        # Extract plasma amount and concentration
        A_plasma = state.get('plasma', 0.0)
        C_plasma = A_plasma / params.organ_volumes['plasma']

        # Plasma dynamics (central compartment)
        dA_plasma = dose_rate

        for organ in self.organs:
            # Organ amount and concentration
            A_organ = state.get(organ, 0.0)
            V_organ = params.organ_volumes.get(organ, 1.0)
            C_organ = A_organ / V_organ

            # Partition coefficient
            Kp = params.partition_coefficients.get(organ, 1.0)

            # Blood flow
            Q_organ = self.circulation.get_organ_flow(organ)

            # Tissue equilibrium concentration
            C_tissue_eq = C_plasma * Kp

            # Net flux (blood flow × concentration difference)
            flux_to_organ = Q_organ * (C_plasma - C_organ / Kp)

            # Update derivatives
            derivatives[organ] = flux_to_organ
            dA_plasma -= flux_to_organ

        # Add clearance from plasma (hepatic + renal)
        hepatic_clearance = params.hepatic_clearance * C_plasma
        renal_clearance = params.renal_clearance * C_plasma
        dA_plasma -= (hepatic_clearance + renal_clearance)

        derivatives['plasma'] = dA_plasma

        return derivatives

    def simulate_bolus_dose(
        self,
        dose_mg: float,
        duration_hours: float,
        dt: float = 0.1
    ) -> List[Tuple[float, Dict[str, float]]]:
        """Simulate drug distribution after bolus dose.

        Parameters
        ----------
        dose_mg : float
            Bolus dose (mg)
        duration_hours : float
            Simulation duration (h)
        dt : float
            Time step (h)

        Returns
        -------
        list
            Time series of (time, state_dict) tuples
        """
        # Initial state: all drug in plasma
        state = {'plasma': dose_mg}
        for organ in self.organs:
            state[organ] = 0.0

        trajectory = [(0.0, state.copy())]

        t = 0.0
        while t < duration_hours:
            # Compute derivatives
            derivs = self.derivatives(t, state, dose_rate=0.0)

            # Euler step
            for key in state:
                state[key] = max(0.0, state[key] + dt * derivs.get(key, 0.0))

            t += dt
            trajectory.append((t, state.copy()))

        return trajectory

    def get_organ_concentrations(
        self,
        state: Dict[str, float]
    ) -> Dict[str, float]:
        """Convert organ amounts to concentrations.

        Parameters
        ----------
        state : dict
            Drug amounts (mg)

        Returns
        -------
        dict
            Concentrations (mg/L or μM)
        """
        concentrations = {}
        params = self.circulation.params

        for organ, amount in state.items():
            volume = params.organ_volumes.get(organ, 1.0)
            concentrations[organ] = amount / volume if volume > 0 else 0.0

        return concentrations

    def calculate_auc(
        self,
        trajectory: List[Tuple[float, Dict[str, float]]],
        compartment: str = 'plasma'
    ) -> float:
        """Calculate area under the curve (AUC) for a compartment.

        Parameters
        ----------
        trajectory : list
            Time series from simulation
        compartment : str
            Compartment name

        Returns
        -------
        float
            AUC (mg·h/L)
        """
        if len(trajectory) < 2:
            return 0.0

        auc = 0.0
        params = self.circulation.params
        volume = params.organ_volumes.get(compartment, 1.0)

        for i in range(len(trajectory) - 1):
            t1, state1 = trajectory[i]
            t2, state2 = trajectory[i + 1]

            # Concentrations
            C1 = state1.get(compartment, 0.0) / volume
            C2 = state2.get(compartment, 0.0) / volume

            # Trapezoidal rule
            dt = t2 - t1
            auc += 0.5 * (C1 + C2) * dt

        return auc
