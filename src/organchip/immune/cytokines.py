"""Cytokine signaling network and inflammatory cascade models.

This module implements immune response dynamics including:
- Pro-inflammatory cytokine cascades (TNF-α, IL-1β, IL-6)
- Anti-inflammatory responses (IL-10, TGF-β)
- Acute phase response
- Drug-induced inflammation and immunotoxicity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Dict, List
import math


@dataclass
class CytokineParameters:
    """Parameters for cytokine network dynamics.

    Attributes
    ----------
    k_prod_base : Dict[str, float]
        Basal production rates for each cytokine (pg/mL/h)
    k_deg : Dict[str, float]
        Degradation rate constants (1/h)
    EC50 : Dict[str, float]
        Half-maximal effective concentrations (pg/mL)
    hill : Dict[str, float]
        Hill coefficients for dose-response curves
    """

    k_prod_base: Dict[str, float] = field(default_factory=lambda: {
        'TNFa': 0.1,      # TNF-alpha basal production
        'IL1b': 0.05,     # IL-1 beta basal production
        'IL6': 0.08,      # IL-6 basal production
        'IL10': 0.03,     # IL-10 anti-inflammatory
        'TGFb': 0.02,     # TGF-beta
    })

    k_deg: Dict[str, float] = field(default_factory=lambda: {
        'TNFa': 2.0,      # TNF-alpha clearance
        'IL1b': 1.5,      # IL-1 beta clearance
        'IL6': 1.0,       # IL-6 clearance
        'IL10': 1.2,      # IL-10 clearance
        'TGFb': 0.8,      # TGF-beta clearance
    })

    EC50: Dict[str, float] = field(default_factory=lambda: {
        'TNFa': 10.0,
        'IL1b': 8.0,
        'IL6': 15.0,
        'IL10': 12.0,
        'TGFb': 20.0,
    })

    hill: Dict[str, float] = field(default_factory=lambda: {
        'TNFa': 2.0,
        'IL1b': 2.0,
        'IL6': 1.5,
        'IL10': 1.8,
        'TGFb': 1.5,
    })


@dataclass
class CytokineNetwork:
    """Mechanistic model of cytokine signaling network.

    Models interactions between pro- and anti-inflammatory cytokines
    including feedback loops and cross-regulation.

    State variables (all in pg/mL):
    - TNFa: Tumor necrosis factor alpha
    - IL1b: Interleukin-1 beta
    - IL6: Interleukin-6
    - IL10: Interleukin-10 (anti-inflammatory)
    - TGFb: Transforming growth factor beta
    """

    params: CytokineParameters = field(default_factory=CytokineParameters)

    # Interaction strength parameters
    tnf_amplify_il1: float = 2.0      # TNF-α amplifies IL-1β
    tnf_amplify_il6: float = 1.5      # TNF-α amplifies IL-6
    il1_amplify_il6: float = 1.8      # IL-1β amplifies IL-6
    il10_inhibit_tnf: float = 0.5     # IL-10 inhibits TNF-α
    il10_inhibit_il1: float = 0.6     # IL-10 inhibits IL-1β
    tgfb_inhibit_tnf: float = 0.4     # TGF-β inhibits TNF-α

    def hill_activation(self, conc: float, EC50: float, n: float) -> float:
        """Hill equation for activation dynamics.

        Parameters
        ----------
        conc : float
            Effector concentration
        EC50 : float
            Half-maximal concentration
        n : float
            Hill coefficient

        Returns
        -------
        float
            Activation factor [0, 1]
        """
        if conc <= 0:
            return 0.0
        return (conc ** n) / (EC50 ** n + conc ** n)

    def hill_inhibition(self, conc: float, IC50: float, n: float) -> float:
        """Hill equation for inhibition dynamics.

        Parameters
        ----------
        conc : float
            Inhibitor concentration
        IC50 : float
            Half-maximal inhibitory concentration
        n : float
            Hill coefficient

        Returns
        -------
        float
            Inhibition factor [0, 1]
        """
        if conc <= 0:
            return 1.0
        return 1.0 / (1.0 + (conc / IC50) ** n)

    def derivatives(
        self,
        t: float,
        state: Tuple[float, float, float, float, float],
        stimulus: float = 0.0,
        drug_effect: float = 0.0
    ) -> Tuple[float, float, float, float, float]:
        """Compute time derivatives for cytokine network.

        Parameters
        ----------
        t : float
            Time (hours)
        state : tuple
            (TNFa, IL1b, IL6, IL10, TGFb) concentrations (pg/mL)
        stimulus : float
            External inflammatory stimulus (e.g., LPS, damage signal)
        drug_effect : float
            Drug-induced modulation of inflammation

        Returns
        -------
        tuple
            Time derivatives (dTNFa/dt, dIL1b/dt, dIL6/dt, dIL10/dt, dTGFb/dt)
        """
        TNFa, IL1b, IL6, IL10, TGFb = state
        p = self.params

        # TNF-alpha dynamics
        # Amplified by stimulus, inhibited by IL-10 and TGF-beta
        tnf_production = p.k_prod_base['TNFa'] * (1.0 + stimulus + drug_effect)
        tnf_inhibition = self.hill_inhibition(IL10, p.EC50['IL10'], p.hill['IL10']) * \
                        self.hill_inhibition(TGFb, p.EC50['TGFb'], p.hill['TGFb'])
        dTNFa = tnf_production * tnf_inhibition - p.k_deg['TNFa'] * TNFa

        # IL-1 beta dynamics
        # Amplified by TNF-alpha and stimulus, inhibited by IL-10
        il1_amplification = 1.0 + self.tnf_amplify_il1 * self.hill_activation(
            TNFa, p.EC50['TNFa'], p.hill['TNFa']
        )
        il1_production = p.k_prod_base['IL1b'] * (1.0 + stimulus) * il1_amplification
        il1_inhibition = self.hill_inhibition(IL10, p.EC50['IL10'], p.hill['IL10'])
        dIL1b = il1_production * il1_inhibition - p.k_deg['IL1b'] * IL1b

        # IL-6 dynamics
        # Amplified by TNF-alpha and IL-1 beta
        il6_amplification = 1.0 + \
            self.tnf_amplify_il6 * self.hill_activation(TNFa, p.EC50['TNFa'], p.hill['TNFa']) + \
            self.il1_amplify_il6 * self.hill_activation(IL1b, p.EC50['IL1b'], p.hill['IL1b'])
        il6_production = p.k_prod_base['IL6'] * (1.0 + stimulus * 0.5) * il6_amplification
        dIL6 = il6_production - p.k_deg['IL6'] * IL6

        # IL-10 dynamics (anti-inflammatory, induced by IL-6)
        il10_induction = 1.0 + 2.0 * self.hill_activation(IL6, p.EC50['IL6'], p.hill['IL6'])
        il10_production = p.k_prod_base['IL10'] * il10_induction
        dIL10 = il10_production - p.k_deg['IL10'] * IL10

        # TGF-beta dynamics (anti-inflammatory, slow response)
        tgfb_induction = 1.0 + 0.5 * self.hill_activation(IL6, p.EC50['IL6'], p.hill['IL6'])
        tgfb_production = p.k_prod_base['TGFb'] * tgfb_induction
        dTGFb = tgfb_production - p.k_deg['TGFb'] * TGFb

        return dTNFa, dIL1b, dIL6, dIL10, dTGFb

    def inflammatory_index(self, state: Tuple[float, float, float, float, float]) -> float:
        """Calculate overall inflammatory index.

        Parameters
        ----------
        state : tuple
            (TNFa, IL1b, IL6, IL10, TGFb) concentrations

        Returns
        -------
        float
            Inflammatory index (pro-inflammatory / anti-inflammatory ratio)
        """
        TNFa, IL1b, IL6, IL10, TGFb = state

        pro_inflammatory = TNFa + IL1b + IL6
        anti_inflammatory = IL10 + TGFb + 1.0  # +1 to avoid division by zero

        return pro_inflammatory / anti_inflammatory

    def step(
        self,
        t: float,
        state: Tuple[float, float, float, float, float],
        dt: float,
        stimulus: float = 0.0,
        drug_effect: float = 0.0
    ) -> Tuple[float, float, float, float, float]:
        """Advance cytokine network by one time step.

        Parameters
        ----------
        t : float
            Current time (hours)
        state : tuple
            Current state
        dt : float
            Time step (hours)
        stimulus : float
            Inflammatory stimulus
        drug_effect : float
            Drug modulation

        Returns
        -------
        tuple
            Updated state
        """
        derivs = self.derivatives(t, state, stimulus, drug_effect)
        new_state = tuple(max(0.0, s + dt * ds) for s, ds in zip(state, derivs))
        return new_state


@dataclass
class InflammatoryResponse:
    """Acute inflammatory response model with temporal dynamics.

    Models the time course of inflammation including:
    - Acute phase (0-24h): Rapid cytokine release
    - Resolution phase (24-72h): Anti-inflammatory dominance
    - Recovery phase (>72h): Return to baseline
    """

    cytokine_network: CytokineNetwork = field(default_factory=CytokineNetwork)

    # Acute phase response parameters
    acute_phase_proteins: Dict[str, float] = field(default_factory=lambda: {
        'CRP': 0.5,      # C-reactive protein (mg/L)
        'SAA': 0.2,      # Serum amyloid A (mg/L)
        'Fibrinogen': 2.5,  # Fibrinogen (g/L)
    })

    def acute_phase_response(
        self,
        il6_conc: float,
        il1b_conc: float,
        time_hours: float
    ) -> Dict[str, float]:
        """Calculate acute phase protein levels.

        Parameters
        ----------
        il6_conc : float
            IL-6 concentration (pg/mL)
        il1b_conc : float
            IL-1β concentration (pg/mL)
        time_hours : float
            Time since stimulus (hours)

        Returns
        -------
        dict
            Acute phase protein concentrations
        """
        # IL-6 is the primary driver of acute phase response
        il6_effect = self.cytokine_network.hill_activation(
            il6_conc, 20.0, 2.0
        )

        il1_effect = self.cytokine_network.hill_activation(
            il1b_conc, 10.0, 2.0
        )

        # Time-dependent modulation (peak at 24-48h)
        time_factor = math.exp(-((time_hours - 36.0) ** 2) / (2 * 24.0 ** 2))

        response = {
            'CRP': self.acute_phase_proteins['CRP'] * (
                1.0 + 100.0 * il6_effect * time_factor
            ),
            'SAA': self.acute_phase_proteins['SAA'] * (
                1.0 + 500.0 * il6_effect * time_factor
            ),
            'Fibrinogen': self.acute_phase_proteins['Fibrinogen'] * (
                1.0 + 2.0 * (il6_effect + 0.5 * il1_effect) * time_factor
            ),
        }

        return response

    def simulate_inflammatory_event(
        self,
        stimulus_magnitude: float,
        duration_hours: float,
        dt: float = 0.1
    ) -> List[Tuple[float, Tuple[float, float, float, float, float]]]:
        """Simulate inflammatory response to a stimulus event.

        Parameters
        ----------
        stimulus_magnitude : float
            Magnitude of inflammatory stimulus
        duration_hours : float
            Simulation duration (hours)
        dt : float
            Time step (hours)

        Returns
        -------
        list
            Time series of (time, cytokine_state) tuples
        """
        # Initial state (baseline)
        state = (0.5, 0.3, 0.4, 1.0, 0.8)  # (TNFa, IL1b, IL6, IL10, TGFb)
        trajectory = [(0.0, state)]

        t = 0.0
        while t < duration_hours:
            # Stimulus decays exponentially
            current_stimulus = stimulus_magnitude * math.exp(-t / 6.0)

            state = self.cytokine_network.step(t, state, dt, stimulus=current_stimulus)
            t += dt
            trajectory.append((t, state))

        return trajectory
