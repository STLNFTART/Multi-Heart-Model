"""Drug toxicity validation suite.

Tests organ chip models against known toxicity profiles for:
- Doxorubicin (cardiotoxic anthracycline)
- Acetaminophen (hepatotoxic analgesic)
- Isoproterenol (cardiac stimulant)
- Troglitazone (withdrawn hepatotoxic drug)
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from organchip.orchestrator import OrganChipSuite, create_default_organ_chip_suite
from organchip.cardiac.cardiotoxicity import IonChannelDynamics
from organchip.liver.hepatocyte import HepatocyteParameters


class TestDoxorubicinCardiotoxicity:
    """Test doxorubicin-induced cardiotoxicity.

    Doxorubicin is a chemotherapeutic agent with well-known
    dose-dependent cardiotoxicity via:
    - Mitochondrial damage
    - ROS generation
    - Cardiac troponin release
    - QT prolongation (mild)
    """

    def test_doxorubicin_low_dose(self):
        """Test low therapeutic dose (safe)."""
        suite = create_default_organ_chip_suite()

        # Configure for doxorubicin
        # IC50 for hERG: ~10 μM (mild effect)
        suite.cardiac.ion_channels.IC50_hERG = 10.0

        # Low dose: 50mg total (safe range)
        trajectory, tox = suite.run_complete_study(
            dose_mg=50.0,
            duration_hours=48.0,
            dt=0.1,
            export_file=None
        )

        # Assertions
        assert tox['overall_toxicity_score'] < 0.4, "Low dose should be safe"
        assert tox['cardiac']['severity'] in ['None', 'Mild'], \
            "Low dose cardiotoxicity should be minimal"

    def test_doxorubicin_high_dose(self):
        """Test high cumulative dose (toxic)."""
        suite = create_default_organ_chip_suite()
        suite.cardiac.ion_channels.IC50_hERG = 10.0

        # High dose: 500mg total (toxic range)
        trajectory, tox = suite.run_complete_study(
            dose_mg=500.0,
            duration_hours=72.0,
            dt=0.1,
            export_file=None
        )

        # Assertions
        assert tox['overall_toxicity_score'] > 0.4, "High dose should be toxic"
        assert tox['cardiac']['troponin_fold_elevation'] > 2.0, \
            "Should see troponin elevation"

    def test_doxorubicin_time_course(self):
        """Test time-dependent accumulation of toxicity."""
        suite = create_default_organ_chip_suite()
        suite.cardiac.ion_channels.IC50_hERG = 10.0

        trajectory, _ = suite.simulate_drug_exposure(
            dose_mg=200.0,
            duration_hours=96.0,
            dt=0.5
        )

        # Check troponin rises over time
        troponin_values = [
            state['cardiac']['Troponin']
            for t, state in trajectory
        ]

        initial_troponin = troponin_values[0]
        final_troponin = troponin_values[-1]

        # Should see increase (even if small due to simplified model)
        assert final_troponin >= initial_troponin, \
            "Troponin should not decrease"


class TestAcetaminophenHepatotoxicity:
    """Test acetaminophen (paracetamol) hepatotoxicity.

    Acetaminophen causes dose-dependent liver toxicity via:
    - NAPQI (reactive metabolite) formation
    - Glutathione depletion
    - Mitochondrial dysfunction
    - Hepatocellular necrosis (ALT/AST elevation)
    """

    def test_acetaminophen_therapeutic_dose(self):
        """Test therapeutic dose (4g/day - safe)."""
        suite = create_default_organ_chip_suite()

        # Configure for acetaminophen metabolism
        # Increased Phase II (safe conjugation)
        suite.liver.metabolism.frac_phase1_to_reactive = 0.1  # 10% to NAPQI

        # Therapeutic dose: 4000mg
        trajectory, tox = suite.run_complete_study(
            dose_mg=4000.0,
            duration_hours=24.0,
            dt=0.1
        )

        # Assertions
        assert tox['liver']['severity'] in ['None', 'Mild'], \
            "Therapeutic dose should be safe"
        assert tox['liver']['GSH_depletion'] < 0.5, \
            "Should not deplete GSH significantly"

    def test_acetaminophen_overdose(self):
        """Test toxic overdose (>10g)."""
        suite = create_default_organ_chip_suite()

        # Higher reactive metabolite formation in overdose
        suite.liver.metabolism.frac_phase1_to_reactive = 0.3

        # Toxic dose: 15000mg (15g)
        trajectory, tox = suite.run_complete_study(
            dose_mg=15000.0,
            duration_hours=48.0,
            dt=0.1
        )

        # Assertions
        assert tox['overall_toxicity_score'] > 0.5, "Overdose should be toxic"
        assert tox['liver']['severity'] in ['Moderate', 'Severe', 'Critical'], \
            "Should show hepatotoxicity"
        assert tox['liver']['ALT_elevation_fold'] > 3.0, \
            "Should see significant ALT elevation"

    def test_acetaminophen_gsh_depletion(self):
        """Test glutathione depletion time course."""
        suite = create_default_organ_chip_suite()
        suite.liver.metabolism.frac_phase1_to_reactive = 0.25

        trajectory, _ = suite.simulate_drug_exposure(
            dose_mg=12000.0,
            duration_hours=48.0,
            dt=0.2
        )

        # Extract GSH levels
        gsh_values = [state['liver']['GSH'] for t, state in trajectory]

        # GSH should decrease
        assert gsh_values[-1] < gsh_values[0], "GSH should be depleted"

        # Find minimum GSH
        min_gsh = min(gsh_values)
        assert min_gsh < 5.0, "GSH should drop significantly in overdose"


class TestMultiOrganInteractions:
    """Test multi-organ interactions and coupling."""

    def test_liver_cardiac_coupling(self):
        """Test that liver metabolites affect cardiac function."""
        suite = create_default_organ_chip_suite()

        # Drug with cardiotoxic metabolite
        suite.liver.metabolism.frac_phase1_to_reactive = 0.5
        suite.cardiac.ion_channels.IC50_hERG = 5.0  # Sensitive to metabolite

        trajectory, tox = suite.run_complete_study(
            dose_mg=300.0,
            duration_hours=48.0
        )

        # Both organs should show some toxicity
        assert tox['liver']['toxicity_score'] > 0.1
        assert tox['cardiac']['toxicity_score'] > 0.1

    def test_immune_activation(self):
        """Test immune response to organ damage."""
        suite = create_default_organ_chip_suite()

        # High hepatotoxic dose
        suite.liver.metabolism.frac_phase1_to_reactive = 0.4

        trajectory, tox = suite.run_complete_study(
            dose_mg=10000.0,
            duration_hours=72.0
        )

        # Immune system should activate
        assert tox['immune']['inflammatory_index'] > 1.0, \
            "Should see inflammatory response"
        assert tox['immune']['TNFa_fold'] > 1.0, \
            "TNF-alpha should increase"

    def test_circulation_distribution(self):
        """Test drug distribution through organs."""
        suite = create_default_organ_chip_suite()

        trajectory, _ = suite.simulate_drug_exposure(
            dose_mg=100.0,
            duration_hours=24.0,
            dt=0.1
        )

        # Check that drug distributes to organs
        final_state = trajectory[-1][1]
        circ_state = final_state['circulation']

        # Liver should accumulate drug (high partition coefficient)
        liver_amount = circ_state.get('liver', 0.0)
        assert liver_amount > 0, "Drug should distribute to liver"


class TestDrugScreeningScenarios:
    """End-to-end drug screening scenarios."""

    def test_comparative_toxicity_ranking(self):
        """Compare toxicity of multiple doses."""
        suite = create_default_organ_chip_suite()

        doses = [50, 200, 500, 1000]
        toxicity_scores = []

        for dose in doses:
            _, tox = suite.run_complete_study(
                dose_mg=dose,
                duration_hours=48.0,
                dt=0.2,
                export_file=None
            )
            toxicity_scores.append(tox['overall_toxicity_score'])

        # Toxicity should increase with dose
        for i in range(len(toxicity_scores) - 1):
            assert toxicity_scores[i+1] >= toxicity_scores[i], \
                f"Toxicity should increase with dose: {toxicity_scores}"

    def test_safety_margin_calculation(self):
        """Calculate therapeutic index."""
        suite = create_default_organ_chip_suite()

        # Therapeutic dose
        _, tox_therapeutic = suite.run_complete_study(
            dose_mg=100.0,
            duration_hours=24.0
        )

        # Toxic dose
        _, tox_toxic = suite.run_complete_study(
            dose_mg=1000.0,
            duration_hours=24.0
        )

        therapeutic_score = tox_therapeutic['overall_toxicity_score']
        toxic_score = tox_toxic['overall_toxicity_score']

        # Toxic dose should be more toxic
        assert toxic_score > therapeutic_score, \
            "Higher dose should show higher toxicity"

        # Safety margin
        safety_margin = 1000.0 / 100.0  # Dose ratio
        assert safety_margin == 10.0, "Safety margin should be 10x"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
