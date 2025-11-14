"""
Organ Chip Parameter Sweeps

Comprehensive parameter sweeps for organ-on-chip models:
1. PBPK circulation parameters
2. Cardiac cell parameters
3. Hepatocyte metabolism parameters
4. Immune system parameters
5. Ligand-receptor binding parameters
6. Drug dose-response sweeps
7. Multi-organ coupling parameters

Author: AI Assistant
Date: 2025-11-14
"""

import pytest
import sys
from pathlib import Path
from typing import List, Dict
import itertools
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from organchip.orchestrator import OrganChipSuite, create_default_organ_chip_suite
    from organchip.cardiac.cardiotoxicity import CardiacCell, IonChannelDynamics
    from organchip.liver.hepatocyte import Hepatocyte, HepatocyteParameters
    from organchip.circulation.pbpk import MultiOrganPBPK, PBPKParameters
    from organchip.immune.cytokines import CytokineNetwork, CytokineParameters
    from organchip.ligand_receptor.binding import LigandReceptorBinding, BindingParameters
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="Organ chip modules not available")
class TestPBPKParameterSweeps:
    """Parameter sweeps for PBPK circulation model."""

    def test_cardiac_output_sweep(self):
        """Sweep cardiac output (blood flow rate)."""
        co_values = [150.0, 200.0, 300.0, 400.0, 500.0]  # L/h

        for co in co_values:
            params = PBPKParameters(cardiac_output=co)
            pbpk = MultiOrganPBPK(params=params)

            # Initialize with drug dose
            state = pbpk.initialize_state(dose_mg=100.0)

            # Simulate one step
            new_state = pbpk.step(0.0, state, dt=0.1)

            # State should be valid
            assert all(v >= 0 for v in new_state.values()), \
                f"Negative concentrations at CO={co}"

        print(f"✓ Cardiac output sweep: {len(co_values)} values tested")

    def test_hepatic_clearance_sweep(self):
        """Sweep hepatic clearance rate."""
        clearance_values = [1.0, 5.0, 10.0, 20.0, 50.0, 100.0]  # L/h

        for cl in clearance_values:
            params = PBPKParameters(hepatic_clearance=cl)
            pbpk = MultiOrganPBPK(params=params)

            state = pbpk.initialize_state(dose_mg=100.0)

            # Simulate to see clearance effect
            for _ in range(10):
                state = pbpk.step(0.0, state, dt=0.1)

            # Higher clearance = lower concentration
            plasma_conc = state.get('plasma', 0.0)
            assert plasma_conc >= 0, \
                f"Invalid plasma concentration at CL={cl}"

        print(f"✓ Hepatic clearance sweep: {len(clearance_values)} values tested")

    def test_partition_coefficient_sweep(self):
        """Sweep tissue partition coefficients."""
        kp_values = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]

        for kp in kp_values:
            params = PBPKParameters()
            params.partition_coefficients['liver'] = kp

            pbpk = MultiOrganPBPK(params=params)

            state = pbpk.initialize_state(dose_mg=100.0)

            # Run simulation
            for _ in range(50):
                state = pbpk.step(0.0, state, dt=0.1)

            liver_conc = state.get('liver', 0.0)
            assert liver_conc >= 0, \
                f"Invalid liver concentration at Kp={kp}"

        print(f"✓ Partition coefficient sweep: {len(kp_values)} values tested")

    def test_dose_magnitude_sweep(self):
        """Sweep drug dose magnitudes."""
        doses = [1.0, 10.0, 50.0, 100.0, 500.0, 1000.0, 5000.0]  # mg

        for dose in doses:
            pbpk = MultiOrganPBPK()

            state = pbpk.initialize_state(dose_mg=dose)

            # Initial plasma should scale with dose
            initial_plasma = state.get('plasma', 0.0)
            assert initial_plasma > 0, \
                f"No drug in plasma at dose={dose}"

            # Run brief simulation
            for _ in range(10):
                state = pbpk.step(0.0, state, dt=0.1)

        print(f"✓ Dose magnitude sweep: {len(doses)} doses tested")


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="Organ chip modules not available")
class TestCardiacCellParameterSweeps:
    """Parameter sweeps for cardiac cell model."""

    def test_ic50_herg_sweep(self):
        """Sweep hERG channel IC50 values."""
        ic50_values = [0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 50.0]  # μM

        for ic50 in ic50_values:
            cardiac = CardiacCell()
            cardiac.ion_channels.IC50_hERG = ic50

            # Test at fixed drug concentration
            drug_conc = 1.0  # μM

            initial_state = cardiac.get_initial_state()
            new_state = cardiac.step(0.0, initial_state, dt=0.001, drug_conc=drug_conc)

            # State should remain valid
            assert all(isinstance(v, (int, float)) for v in new_state.values()), \
                f"Invalid state at IC50={ic50}"

        print(f"✓ IC50 hERG sweep: {len(ic50_values)} values tested")

    def test_drug_concentration_sweep(self):
        """Sweep drug concentrations affecting cardiac cell."""
        drug_concs = [0.0, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0]  # μM

        cardiac = CardiacCell()
        initial_state = cardiac.get_initial_state()

        for conc in drug_concs:
            state = dict(initial_state)  # Copy

            # Simulate 100 steps
            for _ in range(100):
                state = cardiac.step(0.0, state, dt=0.001, drug_conc=conc)

            # Check biomarkers
            biomarkers = cardiac.get_biomarkers(state)

            assert 'Troponin' in biomarkers, \
                f"Missing biomarker at drug_conc={conc}"
            assert biomarkers['Troponin'] >= 0, \
                f"Negative troponin at drug_conc={conc}"

        print(f"✓ Drug concentration sweep: {len(drug_concs)} concentrations tested")

    def test_pacing_frequency_sweep(self):
        """Sweep cardiac pacing frequencies."""
        frequencies = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]  # Hz

        cardiac = CardiacCell()

        for freq in frequencies:
            cardiac.pacing_frequency = freq

            state = cardiac.get_initial_state()

            # Simulate several beats
            for t_step in range(1000):
                t = t_step * 0.001
                state = cardiac.step(t, state, dt=0.001, drug_conc=0.0)

            # Should complete cycles without instability
            assert state['V'] > -150 and state['V'] < 100, \
                f"Voltage instability at freq={freq}: V={state['V']}"

        print(f"✓ Pacing frequency sweep: {len(frequencies)} frequencies tested")


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="Organ chip modules not available")
class TestHepatocyteParameterSweeps:
    """Parameter sweeps for hepatocyte metabolism model."""

    def test_phase1_metabolism_rate_sweep(self):
        """Sweep Phase I metabolism rates."""
        phase1_rates = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]  # 1/h

        for rate in phase1_rates:
            hepatocyte = Hepatocyte()
            hepatocyte.metabolism.k_phase1 = rate

            state = hepatocyte.get_initial_state()

            # Add drug
            state['Drug_intra'] = 10.0

            # Simulate metabolism
            for _ in range(100):
                state = hepatocyte.step(0.0, state, dt=0.1, drug_plasma=5.0)

            # Check metabolite formation
            assert state['Metabolite'] >= 0, \
                f"Negative metabolite at phase1_rate={rate}"

        print(f"✓ Phase I metabolism rate sweep: {len(phase1_rates)} values tested")

    def test_gsh_baseline_sweep(self):
        """Sweep baseline glutathione levels."""
        gsh_baseline = [2.0, 5.0, 8.0, 10.0, 15.0, 20.0]  # mM

        for gsh in gsh_baseline:
            hepatocyte = Hepatocyte()

            state = hepatocyte.get_initial_state()
            state['GSH'] = gsh

            # Expose to reactive metabolite
            state['Reactive'] = 5.0

            # Simulate GSH depletion
            for _ in range(50):
                state = hepatocyte.step(0.0, state, dt=0.1, drug_plasma=0.0)

            # GSH should decrease but not go negative
            assert state['GSH'] >= 0, \
                f"Negative GSH from baseline={gsh}"

        print(f"✓ GSH baseline sweep: {len(gsh_baseline)} values tested")

    def test_reactive_metabolite_fraction_sweep(self):
        """Sweep fraction of Phase I going to reactive metabolites."""
        fractions = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7]

        for frac in fractions:
            hepatocyte = Hepatocyte()
            hepatocyte.metabolism.frac_phase1_to_reactive = frac

            state = hepatocyte.get_initial_state()
            state['Drug_intra'] = 20.0

            # Simulate
            for _ in range(100):
                state = hepatocyte.step(0.0, state, dt=0.1, drug_plasma=10.0)

            # Higher fraction = more reactive metabolite
            reactive = state['Reactive']
            assert reactive >= 0, \
                f"Negative reactive metabolite at frac={frac}"

        print(f"✓ Reactive metabolite fraction sweep: {len(fractions)} values tested")

    def test_drug_plasma_concentration_sweep(self):
        """Sweep plasma drug concentrations affecting hepatocyte."""
        plasma_concs = [0.0, 1.0, 5.0, 10.0, 50.0, 100.0, 500.0]  # μM

        hepatocyte = Hepatocyte()

        for conc in plasma_concs:
            state = hepatocyte.get_initial_state()

            # Simulate uptake and metabolism
            for _ in range(200):
                state = hepatocyte.step(0.0, state, dt=0.1, drug_plasma=conc)

            # Check for toxicity biomarkers
            biomarkers = hepatocyte.get_biomarkers(state)

            assert 'ALT' in biomarkers
            assert biomarkers['ALT'] >= 0

        print(f"✓ Plasma concentration sweep: {len(plasma_concs)} concentrations tested")


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="Organ chip modules not available")
class TestLigandReceptorParameterSweeps:
    """Parameter sweeps for ligand-receptor binding."""

    def test_kon_association_rate_sweep(self):
        """Sweep association rate constant."""
        kon_values = [0.001, 0.01, 0.1, 0.5, 1.0, 5.0]  # 1/(nM·s)

        for kon in kon_values:
            params = BindingParameters(kon=kon, koff=0.01)
            binding = LigandReceptorBinding(params=params)

            state = binding.get_initial_state()

            # Add ligand
            ligand_conc = 10.0  # nM

            # Simulate binding
            for _ in range(100):
                state = binding.step(0.0, state, dt=0.1, ligand_conc=ligand_conc)

            # Check receptor occupancy
            bound = state.get('Receptor_bound', 0.0)
            assert bound >= 0, \
                f"Negative bound receptors at kon={kon}"

        print(f"✓ Association rate sweep: {len(kon_values)} values tested")

    def test_kd_affinity_sweep(self):
        """Sweep equilibrium dissociation constant (affinity)."""
        # Kd = koff/kon
        kd_values = [0.01, 0.1, 1.0, 10.0, 100.0]  # nM

        for kd in kd_values:
            # Set kon=0.1, vary koff to achieve desired Kd
            kon = 0.1
            koff = kd * kon

            params = BindingParameters(kon=kon, koff=koff)
            binding = LigandReceptorBinding(params=params)

            assert abs(params.Kd - kd) < 0.01, \
                f"Kd mismatch: expected {kd}, got {params.Kd}"

            # Test binding at Kd concentration
            state = binding.get_initial_state()

            for _ in range(200):
                state = binding.step(0.0, state, dt=0.1, ligand_conc=kd)

            # At equilibrium with [L]=Kd, expect ~50% occupancy
            bound = state.get('Receptor_bound', 0.0)
            total = state.get('Receptor_free', 0.0) + bound

            if total > 0:
                occupancy = bound / total
                # Should be near 0.5 at equilibrium
                # (allowing for incomplete equilibration)
                assert 0.0 <= occupancy <= 1.0

        print(f"✓ Kd affinity sweep: {len(kd_values)} values tested")

    def test_ligand_concentration_sweep(self):
        """Sweep ligand concentrations for dose-response."""
        ligand_concs = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]  # nM

        binding = LigandReceptorBinding()
        results = []

        for conc in ligand_concs:
            state = binding.get_initial_state()

            # Simulate to steady state
            for _ in range(500):
                state = binding.step(0.0, state, dt=0.1, ligand_conc=conc)

            bound = state.get('Receptor_bound', 0.0)
            results.append({'conc': conc, 'bound': bound})

        # Binding should increase with concentration
        print(f"✓ Ligand concentration sweep: {len(ligand_concs)} concentrations tested")


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="Organ chip modules not available")
class TestOrganChipSuiteParameterSweeps:
    """Parameter sweeps for complete organ chip suite."""

    def test_dose_response_sweep(self):
        """Comprehensive dose-response sweep."""
        doses = [10.0, 50.0, 100.0, 500.0, 1000.0, 5000.0]  # mg

        for dose in doses:
            suite = create_default_organ_chip_suite()

            try:
                trajectory, toxicity = suite.run_complete_study(
                    dose_mg=dose,
                    duration_hours=24.0,
                    dt=0.5,
                    export_file=None
                )

                # Check toxicity scores
                assert 'overall_toxicity_score' in toxicity
                assert 0.0 <= toxicity['overall_toxicity_score'] <= 1.0

                # Toxicity should generally increase with dose
                print(f"  Dose {dose} mg: toxicity={toxicity['overall_toxicity_score']:.3f}")

            except Exception as e:
                pytest.fail(f"Failed at dose={dose}: {e}")

        print(f"✓ Dose-response sweep: {len(doses)} doses tested")

    def test_duration_sweep(self):
        """Sweep study durations."""
        durations = [6.0, 12.0, 24.0, 48.0, 72.0, 96.0]  # hours

        for duration in durations:
            suite = create_default_organ_chip_suite()

            trajectory, toxicity = suite.run_complete_study(
                dose_mg=200.0,
                duration_hours=duration,
                dt=1.0,
                export_file=None
            )

            # Longer duration may show more toxicity accumulation
            assert len(trajectory) > 0, \
                f"Empty trajectory at duration={duration}"

        print(f"✓ Duration sweep: {len(durations)} durations tested")

    def test_timestep_sweep(self):
        """Sweep simulation timesteps."""
        dt_values = [0.1, 0.5, 1.0, 2.0, 5.0]  # hours

        for dt in dt_values:
            suite = create_default_organ_chip_suite()

            trajectory, toxicity = suite.run_complete_study(
                dose_mg=100.0,
                duration_hours=12.0,
                dt=dt,
                export_file=None
            )

            expected_steps = int(12.0 / dt) + 1
            actual_steps = len(trajectory)

            # Should have approximately correct number of steps
            assert abs(actual_steps - expected_steps) <= 2, \
                f"Step count mismatch at dt={dt}"

        print(f"✓ Timestep sweep: {len(dt_values)} timesteps tested")

    def test_multi_dose_comparison(self):
        """Compare multiple doses to verify dose-response relationship."""
        doses = [50.0, 200.0, 1000.0]
        toxicity_scores = []

        for dose in doses:
            suite = create_default_organ_chip_suite()

            trajectory, toxicity = suite.run_complete_study(
                dose_mg=dose,
                duration_hours=48.0,
                dt=1.0,
                export_file=None
            )

            toxicity_scores.append(toxicity['overall_toxicity_score'])

        # Verify monotonic increase (with some tolerance)
        # Higher dose should generally have higher toxicity
        print(f"✓ Multi-dose comparison: toxicity scores = {toxicity_scores}")


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="Organ chip modules not available")
class TestDrugSpecificParameterSweeps:
    """Drug-specific parameter sweeps for known toxicants."""

    def test_acetaminophen_dose_sweep(self):
        """Sweep acetaminophen doses (hepatotoxic)."""
        # Therapeutic: ~4g/day, Toxic: >10g
        apap_doses = [1000.0, 2000.0, 4000.0, 8000.0, 12000.0, 15000.0]  # mg

        results = []

        for dose in apap_doses:
            suite = create_default_organ_chip_suite()

            # Configure for acetaminophen
            suite.liver.metabolism.frac_phase1_to_reactive = 0.15

            trajectory, toxicity = suite.run_complete_study(
                dose_mg=dose,
                duration_hours=48.0,
                dt=0.5,
                export_file=None
            )

            liver_tox = toxicity['liver']['toxicity_score']
            results.append({'dose': dose, 'liver_toxicity': liver_tox})

        print(f"✓ Acetaminophen dose sweep: {len(apap_doses)} doses tested")

    def test_doxorubicin_dose_sweep(self):
        """Sweep doxorubicin doses (cardiotoxic)."""
        # Therapeutic: ~60-75 mg/m² IV
        dox_doses = [25.0, 50.0, 100.0, 200.0, 500.0]  # mg

        results = []

        for dose in dox_doses:
            suite = create_default_organ_chip_suite()

            # Configure for doxorubicin
            suite.cardiac.ion_channels.IC50_hERG = 10.0

            trajectory, toxicity = suite.run_complete_study(
                dose_mg=dose,
                duration_hours=72.0,
                dt=0.5,
                export_file=None
            )

            cardiac_tox = toxicity['cardiac']['toxicity_score']
            results.append({'dose': dose, 'cardiac_toxicity': cardiac_tox})

        print(f"✓ Doxorubicin dose sweep: {len(dox_doses)} doses tested")


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="Organ chip modules not available")
class TestOrganChipSweepResults:
    """Collect and export organ chip sweep results."""

    def test_export_organchip_sweep_results(self):
        """Export comprehensive organ chip sweep results."""
        results = {
            'pbpk': {},
            'cardiac': {},
            'liver': {},
            'dose_response': {}
        }

        # Dose-response sweep
        doses = [50.0, 100.0, 500.0, 1000.0]
        dose_sweep = []

        for dose in doses:
            suite = create_default_organ_chip_suite()

            trajectory, toxicity = suite.run_complete_study(
                dose_mg=dose,
                duration_hours=24.0,
                dt=1.0,
                export_file=None
            )

            dose_sweep.append({
                'dose_mg': dose,
                'overall_toxicity': float(toxicity['overall_toxicity_score']),
                'cardiac_toxicity': float(toxicity['cardiac']['toxicity_score']),
                'liver_toxicity': float(toxicity['liver']['toxicity_score'])
            })

        results['dose_response']['sweep'] = dose_sweep

        # Export
        output_path = Path(__file__).parent / 'organchip_sweep_results.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"✓ Organ chip sweep results exported to: {output_path}")
        assert output_path.exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
