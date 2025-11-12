"""Immune response and cytokine network demonstration.

Shows inflammatory cascades, acute phase response, and
drug-induced immunotoxicity.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from organchip.immune.cytokines import (
    CytokineNetwork,
    InflammatoryResponse,
    CytokineParameters
)


def demo_inflammatory_cascade():
    """Demonstrate inflammatory cascade after stimulus."""
    print("\n" + "="*60)
    print("DEMO 1: Inflammatory Cascade")
    print("="*60)

    network = CytokineNetwork()

    # Initial state (baseline)
    state = (0.5, 0.3, 0.4, 1.0, 0.8)  # (TNFa, IL1b, IL6, IL10, TGFb)

    print("\nBaseline Cytokine Levels:")
    print(f"  TNF-α: {state[0]:.2f} pg/mL")
    print(f"  IL-1β: {state[1]:.2f} pg/mL")
    print(f"  IL-6:  {state[2]:.2f} pg/mL")
    print(f"  IL-10: {state[3]:.2f} pg/mL")
    print(f"  TGF-β: {state[4]:.2f} pg/mL")

    # Apply inflammatory stimulus
    stimulus = 10.0
    print(f"\nApplying inflammatory stimulus (magnitude = {stimulus})...")

    dt = 0.1  # hours
    print(f"\n{'Time (h)':<10} {'TNF-α':<10} {'IL-6':<10} {'IL-10':<10} {'Inflam Idx':<12}")
    print("-"*60)

    for i in range(500):
        t = i * dt

        if i % 50 == 0:
            inflam_idx = network.inflammatory_index(state)
            print(f"{t:<10.1f} {state[0]:<10.2f} {state[2]:<10.2f} {state[3]:<10.2f} {inflam_idx:<12.2f}")

        # Stimulus decays over time
        current_stimulus = stimulus * (1.0 if t < 2.0 else 0.5 if t < 10.0 else 0.0)

        state = network.step(t, state, dt, stimulus=current_stimulus)


def demo_acute_phase_response():
    """Demonstrate acute phase protein production."""
    print("\n" + "="*60)
    print("DEMO 2: Acute Phase Response")
    print("="*60)

    response = InflammatoryResponse()

    # Simulate inflammatory event
    stimulus = 15.0
    trajectory = response.simulate_inflammatory_event(
        stimulus_magnitude=stimulus,
        duration_hours=96.0,
        dt=0.5
    )

    print(f"\nSimulating acute phase response over 96 hours...")
    print(f"{'Time (h)':<10} {'IL-6':<10} {'CRP (mg/L)':<15} {'SAA (mg/L)':<15}")
    print("-"*60)

    for i, (t, state) in enumerate(trajectory):
        if i % 20 == 0:
            TNFa, IL1b, IL6, IL10, TGFb = state

            # Calculate acute phase proteins
            apr = response.acute_phase_response(IL6, IL1b, t)

            print(f"{t:<10.1f} {IL6:<10.2f} {apr['CRP']:<15.1f} {apr['SAA']:<15.1f}")


def demo_drug_induced_inflammation():
    """Demonstrate drug-induced inflammatory response."""
    print("\n" + "="*60)
    print("DEMO 3: Drug-Induced Inflammation")
    print("="*60)

    network = CytokineNetwork()

    # Baseline
    state = (0.5, 0.3, 0.4, 1.0, 0.8)

    print("\nSimulating drug with pro-inflammatory effects...")

    drug_doses = [0.0, 5.0, 10.0, 20.0]

    print(f"\n{'Drug Effect':<15} {'Peak TNF-α':<15} {'Peak IL-6':<15} {'Inflam Index':<15}")
    print("-"*65)

    for drug_effect in drug_doses:
        # Reset state
        test_state = state

        # Simulate for 24 hours
        dt = 0.1
        max_tnf = 0.0
        max_il6 = 0.0

        for i in range(240):  # 24 hours
            t = i * dt
            test_state = network.step(
                t, test_state, dt,
                stimulus=0.0,
                drug_effect=drug_effect
            )

            max_tnf = max(max_tnf, test_state[0])
            max_il6 = max(max_il6, test_state[2])

        final_inflam = network.inflammatory_index(test_state)

        print(f"{drug_effect:<15.1f} {max_tnf:<15.2f} {max_il6:<15.2f} {final_inflam:<15.2f}")


def demo_resolution_phase():
    """Demonstrate inflammation resolution."""
    print("\n" + "="*60)
    print("DEMO 4: Inflammation Resolution")
    print("="*60)

    network = CytokineNetwork()
    state = (0.5, 0.3, 0.4, 1.0, 0.8)

    print("\nThree phases of inflammation:")
    print("  Phase 1 (0-6h):   Acute (high stimulus)")
    print("  Phase 2 (6-24h):  Declining (low stimulus)")
    print("  Phase 3 (24-48h): Resolution (no stimulus)")

    dt = 0.2
    phases = []

    print(f"\n{'Time (h)':<10} {'Phase':<15} {'Pro-Inflam':<15} {'Anti-Inflam':<15} {'Ratio':<10}")
    print("-"*70)

    for i in range(240):  # 48 hours
        t = i * dt

        # Determine phase and stimulus
        if t < 6.0:
            phase = "Acute"
            stimulus = 20.0
        elif t < 24.0:
            phase = "Declining"
            stimulus = 2.0
        else:
            phase = "Resolution"
            stimulus = 0.0

        state = network.step(t, state, dt, stimulus=stimulus)

        # Calculate pro- vs anti-inflammatory
        TNFa, IL1b, IL6, IL10, TGFb = state
        pro_inflam = TNFa + IL1b + IL6
        anti_inflam = IL10 + TGFb
        ratio = pro_inflam / anti_inflam if anti_inflam > 0 else 0.0

        if i % 20 == 0:
            print(f"{t:<10.1f} {phase:<15} {pro_inflam:<15.2f} {anti_inflam:<15.2f} {ratio:<10.2f}")


def main():
    """Run all immune response demos."""
    print("\n" + "="*70)
    print("IMMUNE RESPONSE & CYTOKINE NETWORK DEMONSTRATIONS")
    print("="*70)

    demo_inflammatory_cascade()
    demo_acute_phase_response()
    demo_drug_induced_inflammation()
    demo_resolution_phase()

    print("\n" + "="*70)
    print("ALL DEMONSTRATIONS COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
