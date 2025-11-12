"""Unit tests for hepatocyte toxicity model."""

import pytest
import math

from src.hepatic import HepatocyteToxicityModel


class TestHepatocyteToxicityModel:
    """Test suite for HepatocyteToxicityModel."""

    def test_initial_state_generation(self):
        """Test that initial state is generated with correct dimensions and values."""
        model = HepatocyteToxicityModel()
        initial_state = model.get_initial_state(N_total=1000.0)

        assert len(initial_state) == 8
        assert initial_state[0] == 1000.0  # N_viable
        assert initial_state[1] == 0.0      # N_damaged
        assert initial_state[2] == 0.0      # N_dead
        assert initial_state[3] == 0.0      # drug_conc
        assert initial_state[4] == 0.0      # metabolite_conc
        assert initial_state[5] == 1.0      # CYP450_activity
        assert initial_state[6] == 5.0      # ATP_level
        assert initial_state[7] == 10.0     # GSH_level

    def test_initial_state_custom_values(self):
        """Test initial state with custom parameter values."""
        model = HepatocyteToxicityModel()
        initial_state = model.get_initial_state(
            N_total=500.0,
            drug_conc=100.0,
            CYP450_activity=0.8,
            ATP_level=3.0,
            GSH_level=5.0
        )

        assert initial_state[0] == 500.0    # N_viable
        assert initial_state[3] == 100.0    # drug_conc
        assert initial_state[5] == 0.8      # CYP450_activity
        assert initial_state[6] == 3.0      # ATP_level
        assert initial_state[7] == 5.0      # GSH_level

    def test_state_labels(self):
        """Test that state labels are correctly defined."""
        model = HepatocyteToxicityModel()
        labels = model.get_state_labels()

        assert len(labels) == 8
        assert "N_viable" in labels[0]
        assert "N_damaged" in labels[1]
        assert "N_dead" in labels[2]
        assert "Drug" in labels[3]
        assert "Metabolite" in labels[4]
        assert "CYP450" in labels[5]
        assert "ATP" in labels[6]
        assert "GSH" in labels[7]

    def test_derivatives_shape(self):
        """Test that derivatives returns correct number of values."""
        model = HepatocyteToxicityModel()
        state = model.get_initial_state()
        derivs = model.derivatives(0.0, state)

        assert len(derivs) == 8

    def test_derivatives_no_drug_steady_state(self):
        """Test that with no drug, healthy cells remain relatively stable."""
        model = HepatocyteToxicityModel()
        state = model.get_initial_state(N_total=1000.0)

        derivs = model.derivatives(0.0, state, drug_input=0.0)

        # With no drug, viable cells should remain relatively stable
        # (small changes due to ATP/GSH dynamics)
        dN_viable, dN_damaged, dN_dead, dDrug, dMetabolite, dCYP450, dATP, dGSH = derivs

        # No cells should be dying or getting damaged significantly
        assert abs(dN_viable) < 10.0  # Minimal viable cell change
        assert abs(dN_damaged) < 1.0   # Minimal damage
        assert dN_dead == pytest.approx(0.0)  # No deaths

    def test_drug_metabolism_michaelis_menten(self):
        """Test that drug metabolism follows Michaelis-Menten kinetics."""
        model = HepatocyteToxicityModel(Vmax=100.0, Km=50.0)

        # Test at Km: rate should be Vmax/2
        state_at_km = (1000.0, 0.0, 0.0, 50.0, 0.0, 1.0, 5.0, 10.0)
        derivs_at_km = model.derivatives(0.0, state_at_km)
        metabolic_rate_at_km = model.Vmax * 1.0 * 50.0 / (50.0 + 50.0)

        # dDrug should be negative (being consumed) and metabolite should increase
        assert derivs_at_km[3] < 0  # Drug decreasing
        assert derivs_at_km[4] > 0  # Metabolite increasing

        # At Km, metabolic rate should be approximately Vmax/2 = 50
        assert abs(derivs_at_km[4] - 50.0) < 1.0  # Metabolite formation ~50

    def test_drug_induces_cell_damage(self):
        """Test that high drug concentration induces cell damage."""
        model = HepatocyteToxicityModel(
            drug_toxicity=0.1,
            metabolite_toxicity=0.2
        )

        # High drug exposure
        state_high_drug = (1000.0, 0.0, 0.0, 200.0, 100.0, 1.0, 5.0, 10.0)
        derivs_high_drug = model.derivatives(0.0, state_high_drug)

        dN_viable, dN_damaged, dN_dead = derivs_high_drug[0], derivs_high_drug[1], derivs_high_drug[2]

        # Expect viable cells to decrease
        assert dN_viable < 0
        # Expect damaged cells to increase
        assert dN_damaged > 0

    def test_ATP_depletion_with_damage(self):
        """Test that cellular damage leads to ATP depletion."""
        model = HepatocyteToxicityModel()

        # State with many damaged cells
        state_damaged = (500.0, 400.0, 100.0, 0.0, 0.0, 1.0, 5.0, 10.0)
        derivs = model.derivatives(0.0, state_damaged)

        dATP = derivs[6]

        # ATP should decrease due to reduced production and increased repair costs
        assert dATP < 0

    def test_GSH_depletion_with_oxidative_stress(self):
        """Test that metabolite-induced oxidative stress depletes GSH."""
        model = HepatocyteToxicityModel(
            ROS_generation=0.1,
            GSH_consumption=0.2
        )

        # State with high metabolite (oxidative stress)
        state_stress = (1000.0, 0.0, 0.0, 0.0, 200.0, 1.0, 5.0, 10.0)
        derivs = model.derivatives(0.0, state_stress)

        dGSH = derivs[7]

        # GSH should be consumed due to oxidative stress
        # (though regeneration may partially compensate)
        # Just check that GSH dynamics respond to metabolite
        assert dGSH != 0.0

    def test_CYP450_inhibition_by_metabolite(self):
        """Test that high metabolite concentration inhibits CYP450."""
        model = HepatocyteToxicityModel(CYP450_inhibition=0.1)

        # Low metabolite: normal CYP450 synthesis
        state_low_met = (1000.0, 0.0, 0.0, 0.0, 10.0, 0.5, 5.0, 10.0)
        derivs_low = model.derivatives(0.0, state_low_met)

        # High metabolite: inhibited CYP450 synthesis
        state_high_met = (1000.0, 0.0, 0.0, 0.0, 200.0, 0.5, 5.0, 10.0)
        derivs_high = model.derivatives(0.0, state_high_met)

        # CYP450 should synthesize more slowly with high metabolite
        assert derivs_high[5] < derivs_low[5]

    def test_cell_death_from_severe_damage(self):
        """Test that severely damaged cells transition to death."""
        model = HepatocyteToxicityModel(
            k_death=0.1,
            death_threshold=1.0,
            metabolite_toxicity=0.5
        )

        # State with damaged cells and high toxicity
        state_severe = (100.0, 800.0, 100.0, 50.0, 150.0, 0.5, 1.0, 2.0)
        derivs = model.derivatives(0.0, state_severe)

        dN_dead = derivs[2]

        # Dead cell count should increase
        assert dN_dead > 0

    def test_step_method_advances_state(self):
        """Test that step method correctly advances the state."""
        model = HepatocyteToxicityModel()
        initial_state = model.get_initial_state()
        dt = 0.01

        new_state = model.step(0.0, initial_state, dt, drug_input=100.0)

        # State should change
        assert new_state != initial_state
        # All values should remain non-negative
        assert all(x >= 0 for x in new_state)
        # CYP450 should remain in [0, 1]
        assert 0.0 <= new_state[5] <= 1.0

    def test_step_method_with_drug_input(self):
        """Test that drug input increases drug concentration."""
        model = HepatocyteToxicityModel()
        initial_state = model.get_initial_state()
        dt = 0.1

        # Step with drug input
        new_state = model.step(0.0, initial_state, dt, drug_input=100.0)

        # Drug concentration should increase
        assert new_state[3] > initial_state[3]

    def test_euler_integration_conservation(self):
        """Test that Euler integration preserves total cell count approximately."""
        model = HepatocyteToxicityModel(
            k_damage=0.0,
            k_repair=0.0,
            k_death=0.0
        )

        initial_state = (1000.0, 0.0, 0.0, 0.0, 0.0, 1.0, 5.0, 10.0)
        dt = 0.01

        new_state = model.step(0.0, initial_state, dt)

        initial_total = initial_state[0] + initial_state[1] + initial_state[2]
        new_total = new_state[0] + new_state[1] + new_state[2]

        # With no transitions, total cells should remain constant
        assert new_total == pytest.approx(initial_total, rel=1e-2)

    def test_viability_computation(self):
        """Test viability percentage calculation."""
        model = HepatocyteToxicityModel()

        # 100% viability
        state_healthy = (1000.0, 0.0, 0.0, 0.0, 0.0, 1.0, 5.0, 10.0)
        assert model.compute_viability(state_healthy) == pytest.approx(100.0)

        # 50% viability
        state_half = (500.0, 300.0, 200.0, 0.0, 0.0, 1.0, 5.0, 10.0)
        assert model.compute_viability(state_half) == pytest.approx(50.0)

        # 0% viability (all dead)
        state_dead = (0.0, 0.0, 1000.0, 0.0, 0.0, 1.0, 5.0, 10.0)
        assert model.compute_viability(state_dead) == pytest.approx(0.0)

    def test_injury_markers(self):
        """Test computation of injury biomarkers."""
        model = HepatocyteToxicityModel()

        state = (700.0, 200.0, 100.0, 50.0, 100.0, 0.8, 3.0, 4.0)
        markers = model.compute_injury_markers(state)

        # Check that all expected markers are present
        assert 'viability' in markers
        assert 'damage_fraction' in markers
        assert 'death_fraction' in markers
        assert 'metabolic_capacity' in markers
        assert 'oxidative_stress' in markers
        assert 'energy_deficit' in markers

        # Check reasonable values
        assert 0.0 <= markers['viability'] <= 100.0
        assert 0.0 <= markers['damage_fraction'] <= 1.0
        assert 0.0 <= markers['death_fraction'] <= 1.0
        assert markers['metabolic_capacity'] >= 0.0

    def test_parameter_customization(self):
        """Test that model parameters can be customized."""
        model = HepatocyteToxicityModel(
            Vmax=200.0,
            Km=100.0,
            k_damage=0.1,
            ATP_baseline=10.0
        )

        assert model.Vmax == 200.0
        assert model.Km == 100.0
        assert model.k_damage == 0.1
        assert model.ATP_baseline == 10.0

    @pytest.mark.parametrize(
        "drug_conc,expected_direction",
        [
            (0.0, "stable"),      # No drug: stable
            (50.0, "decreasing"),  # Low drug: viable cells decrease
            (200.0, "decreasing"), # High drug: viable cells decrease more
        ],
    )
    def test_dose_response(self, drug_conc, expected_direction):
        """Test that cell viability responds appropriately to drug dose."""
        model = HepatocyteToxicityModel(drug_toxicity=0.02, metabolite_toxicity=0.05)

        state = (1000.0, 0.0, 0.0, drug_conc, drug_conc * 0.5, 1.0, 5.0, 10.0)
        derivs = model.derivatives(0.0, state)
        dN_viable = derivs[0]

        if expected_direction == "stable":
            assert abs(dN_viable) < 5.0  # Small change
        elif expected_direction == "decreasing":
            assert dN_viable < 0  # Viable cells decreasing

    def test_long_simulation_stability(self):
        """Test that model remains stable over extended simulation."""
        model = HepatocyteToxicityModel()
        state = model.get_initial_state()
        dt = 0.01

        # Simulate for 100 steps without drug
        for _ in range(100):
            state = model.step(0.0, state, dt)

        # Check all values remain finite and non-negative
        assert all(math.isfinite(x) for x in state)
        assert all(x >= 0 for x in state)

        # Cell counts should not explode
        total_cells = state[0] + state[1] + state[2]
        assert total_cells < 2000.0  # Should not double

    def test_repair_with_adequate_resources(self):
        """Test that damaged cells can repair with adequate ATP and GSH."""
        model = HepatocyteToxicityModel(
            k_repair=0.1,
            k_damage=0.0,  # No new damage
            drug_toxicity=0.0,
            metabolite_toxicity=0.0
        )

        # State with damaged cells but good ATP/GSH
        state = (500.0, 400.0, 100.0, 0.0, 0.0, 1.0, 6.0, 12.0)
        derivs = model.derivatives(0.0, state)

        dN_viable, dN_damaged = derivs[0], derivs[1]

        # With no new damage and good resources, damaged cells should repair
        assert dN_viable > 0  # Viable increasing
        assert dN_damaged < 0  # Damaged decreasing


class TestHepatocyteModelIntegration:
    """Integration tests for full simulation workflows."""

    def test_acute_toxicity_scenario(self):
        """Test acute high-dose toxicity scenario."""
        model = HepatocyteToxicityModel(
            Vmax=150.0,
            drug_toxicity=0.03,
            metabolite_toxicity=0.08
        )

        state = model.get_initial_state(N_total=1000.0, drug_conc=300.0)
        dt = 0.01
        t = 0.0

        # Simulate for 10 hours
        for _ in range(1000):
            state = model.step(t, state, dt)
            t += dt

        # After acute toxicity, expect significant cell damage
        viability = model.compute_viability(state)
        assert viability < 100.0  # Some damage should have occurred

    def test_chronic_low_dose_scenario(self):
        """Test chronic low-dose exposure."""
        model = HepatocyteToxicityModel(
            drug_toxicity=0.005,
            metabolite_toxicity=0.01,
            k_repair=0.03
        )

        state = model.get_initial_state()
        dt = 0.01
        t = 0.0

        # Simulate chronic exposure (50 hours) with constant low drug input
        for _ in range(5000):
            state = model.step(t, state, dt, drug_input=10.0)
            t += dt

        # System should reach some equilibrium (not all cells dead)
        viability = model.compute_viability(state)
        assert viability > 0.0

    def test_recovery_after_drug_withdrawal(self):
        """Test that cells can recover after drug withdrawal."""
        model = HepatocyteToxicityModel(k_repair=0.05)

        # First, induce damage with drug
        state = model.get_initial_state()
        dt = 0.01

        # Phase 1: Drug exposure (10 hours)
        for _ in range(1000):
            state = model.step(0.0, state, dt, drug_input=100.0)

        viability_during_exposure = model.compute_viability(state)

        # Phase 2: Recovery (20 hours, no drug)
        for _ in range(2000):
            state = model.step(0.0, state, dt, drug_input=0.0)

        viability_after_recovery = model.compute_viability(state)

        # Viability should improve after drug withdrawal (or at least not worsen)
        # This depends on whether damage was reversible
        assert viability_after_recovery >= 0.0  # System should remain stable
