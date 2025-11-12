"""Ligand-receptor binding demonstration.

Shows receptor occupancy dynamics, competitive inhibition, and
target-mediated drug disposition.
"""

import sys
from pathlib import Path
import math

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from organchip.ligand_receptor.binding import (
    LigandReceptorBinding,
    BindingParameters,
    CompetitiveInhibition,
    ReceptorDynamics
)


def demo_basic_binding():
    """Demonstrate basic ligand-receptor binding."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Ligand-Receptor Binding")
    print("="*60)

    # Create binding model
    params = BindingParameters(
        kon=0.1,      # Fast association
        koff=0.01,    # Slow dissociation (high affinity)
        kint=0.001,   # Slow internalization
        Rtot=100.0    # 100 nM receptors
    )

    model = LigandReceptorBinding(params=params)

    print(f"\nBinding Parameters:")
    print(f"  Kd = {model.params.Kd:.2f} nM")
    print(f"  Affinity = {model.params.affinity:.4f} nM⁻¹")
    print(f"  Total Receptors = {model.params.Rtot:.1f} nM")

    # Simulate binding kinetics
    ligand_conc = 50.0  # 50 nM
    state = (ligand_conc, 100.0, 0.0, 0.0)  # (L, R, LR, Rint)

    print(f"\nSimulating binding with [{ligand_conc} nM] ligand...")

    dt = 0.1  # seconds
    time_points = []
    occupancy_points = []

    for i in range(1000):
        t = i * dt
        time_points.append(t)
        occupancy = model.occupancy(state)
        occupancy_points.append(occupancy)

        state = model.step(t, state, dt, ligand_input=0.0)

        if i % 200 == 0:
            print(f"  t={t:.1f}s: Occupancy = {occupancy:.1%}, LR = {state[2]:.2f} nM")

    # Steady state
    ss_state = model.steady_state(ligand_conc)
    ss_occupancy = model.occupancy(ss_state)
    print(f"\nSteady State:")
    print(f"  Occupancy = {ss_occupancy:.1%}")
    print(f"  Free Receptors = {ss_state[1]:.2f} nM")
    print(f"  Bound Complex = {ss_state[2]:.2f} nM")


def demo_competitive_inhibition():
    """Demonstrate competitive inhibition between drug and native ligand."""
    print("\n" + "="*60)
    print("DEMO 2: Competitive Inhibition")
    print("="*60)

    # Native ligand (high affinity)
    ligand_params = BindingParameters(
        kon=0.2, koff=0.01, Rtot=100.0  # Kd = 0.05 nM
    )

    # Drug (lower affinity)
    drug_params = BindingParameters(
        kon=0.1, koff=0.1, Rtot=100.0   # Kd = 1.0 nM
    )

    competition = CompetitiveInhibition(
        drug_binding=LigandReceptorBinding(params=drug_params),
        ligand_binding=LigandReceptorBinding(params=ligand_params)
    )

    print(f"\nNative Ligand Kd = {ligand_params.Kd:.3f} nM")
    print(f"Drug Kd = {drug_params.Kd:.3f} nM")

    # Test different drug concentrations
    ligand_conc = 0.1  # Fixed ligand
    drug_concs = [0.0, 0.5, 1.0, 5.0, 10.0]

    print(f"\nCompetition at fixed ligand [{ligand_conc} nM]:")
    print(f"{'Drug [nM]':<12} {'Drug Occ':<12} {'Ligand Occ':<12}")
    print("-"*40)

    for drug_conc in drug_concs:
        drug_occ, ligand_occ = competition.fractional_occupancy(
            drug_conc, ligand_conc, 100.0
        )
        print(f"{drug_conc:<12.1f} {drug_occ:<12.1%} {ligand_occ:<12.1%}")


def demo_receptor_desensitization():
    """Demonstrate receptor desensitization and trafficking."""
    print("\n" + "="*60)
    print("DEMO 3: Receptor Desensitization & Trafficking")
    print("="*60)

    # Create receptor dynamics model with desensitization
    params = BindingParameters(kon=0.1, koff=0.01, kint=0.01, Rtot=100.0)

    dynamics = ReceptorDynamics(
        params=params,
        kdes=0.02,      # Desensitization rate
        kresens=0.005,  # Resensitization rate
        krecycle=0.01   # Recycling rate
    )

    print(f"\nReceptor Dynamics Parameters:")
    print(f"  Desensitization rate = {dynamics.kdes:.3f} /s")
    print(f"  Resensitization rate = {dynamics.kresens:.3f} /s")
    print(f"  Recycling rate = {dynamics.krecycle:.3f} /s")

    # Initial state (L, R, Rd, Ri, LR)
    ligand_conc = 20.0
    state = (ligand_conc, 100.0, 0.0, 0.0, 0.0)

    print(f"\nSimulating with [{ligand_conc} nM] ligand...")
    print(f"{'Time (s)':<10} {'Active R':<12} {'Desens R':<12} {'Intern R':<12} {'LR':<12}")
    print("-"*60)

    dt = 1.0
    for i in range(100):
        t = i * dt

        if i % 20 == 0:
            L, R, Rd, Ri, LR = state
            print(f"{t:<10.1f} {R:<12.2f} {Rd:<12.2f} {Ri:<12.2f} {LR:<12.2f}")

        derivs = dynamics.derivatives(t, state, ligand_conc=ligand_conc)
        state = tuple(max(0.0, s + dt * d) for s, d in zip(state, derivs))


def demo_dose_response():
    """Demonstrate dose-response curve."""
    print("\n" + "="*60)
    print("DEMO 4: Dose-Response Curve")
    print("="*60)

    params = BindingParameters(kon=0.1, koff=0.1, Rtot=100.0)  # Kd = 1.0 nM
    model = LigandReceptorBinding(params=params)

    print(f"\nReceptor Kd = {model.params.Kd:.2f} nM")
    print(f"\n{'[Ligand] nM':<15} {'Occupancy %':<15} {'EC50 Ratio':<15}")
    print("-"*50)

    # Dose range: 0.01 Kd to 100 Kd
    doses = [0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 100.0]

    for dose in doses:
        conc = dose * model.params.Kd
        ss_state = model.steady_state(conc)
        occupancy = model.occupancy(ss_state)
        ratio = conc / model.params.Kd

        print(f"{conc:<15.2f} {occupancy*100:<15.1f} {ratio:<15.2f}")

    print("\nNote: At [L] = Kd, occupancy should be ~50%")


def main():
    """Run all ligand-receptor demos."""
    print("\n" + "="*70)
    print("LIGAND-RECEPTOR BINDING DEMONSTRATIONS")
    print("="*70)

    demo_basic_binding()
    demo_competitive_inhibition()
    demo_receptor_desensitization()
    demo_dose_response()

    print("\n" + "="*70)
    print("ALL DEMONSTRATIONS COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
