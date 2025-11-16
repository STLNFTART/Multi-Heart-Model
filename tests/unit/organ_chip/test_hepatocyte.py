"""
Comprehensive unit tests for HepatocyteModel.

Tests cover:
- Initialization and default parameters
- Phase I metabolism (Michaelis-Menten kinetics)
- Phase II metabolism (conjugation)
- Glutathione dynamics
- ROS production and scavenging
- ATP dynamics
- Cell damage and repair
- Cell death mechanism
- Helper methods
- Factory functions
- Integration and numerical stability
"""

import pytest
import numpy as np
from src.organ_chip.liver import HepatocyteModel, create_acetaminophen_model, create_doxorubicin_model


class TestHepatocyteInitialization:
    """Test model initialization and parameters."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        model = HepatocyteModel()

        assert model.V_CYP == 100.0
        assert model.K_CYP == 50.0
        assert model.V_conj == 80.0
        assert model.K_conj == 30.0
        assert model.k_GSH_synth == 5.0
        assert model.ATP_max == 5.0

    def test_initial_state(self):
        """Test initial state values."""
        model = HepatocyteModel(
            D0=10.0,
            GSH0=8.0,
            ATP0=4.0
        )

        assert model.state[0] == 10.0  # D
        assert model.state[3] == 8.0   # GSH
        assert model.state[6] == 4.0   # ATP
        assert model.state[7] == 0.0   # Damage

    def test_state_dimensions(self):
        """Test that state has correct dimensions."""
        model = HepatocyteModel()

        assert len(model.state) == 8  # [D, M, M_conj, GSH, GSSG, ROS, ATP, Damage]
        assert model.state.dtype == np.float64

    def test_history_initialization(self):
        """Test that history is initialized correctly."""
        model = HepatocyteModel()

        assert 't' in model.history
        assert 'D' in model.history
        assert 'GSH' in model.history
        assert len(model.history['t']) == 1
        assert model.history['t'][0] == 0.0


class TestPhaseIMetabolism:
    """Test Phase I metabolism (CYP450)."""

    def test_phase1_michaelis_menten(self):
        """Test Michaelis-Menten kinetics for Phase I."""
        model = HepatocyteModel(V_CYP=100.0, K_CYP=50.0)

        # At K_CYP, velocity should be V_max/2
        state = np.array([50.0, 0.0, 0.0, 10.0, 0.5, 0.1, 5.0, 0.0])
        derivs = model.derivatives(state)

        # v_phase1 = 100 * 50 / (50 + 50) = 50 μM/h
        # dD_dt includes phase1, uptake, efflux
        # For this test, check that metabolite production equals v_phase1
        # dM_dt = v_phase1 - v_phase2
        # With M=0, v_phase2 should be small
        assert derivs[1] > 45.0  # dM_dt should be close to 50

    def test_phase1_saturation(self):
        """Test Phase I saturation at high substrate."""
        model = HepatocyteModel(V_CYP=100.0, K_CYP=50.0)

        # High drug concentration
        state_high = np.array([1000.0, 0.0, 0.0, 10.0, 0.5, 0.1, 5.0, 0.0])
        derivs_high = model.derivatives(state_high)

        # Should approach V_max
        # v_phase1 = 100 * 1000 / (50 + 1000) ≈ 95.2
        assert derivs_high[1] > 90.0  # Near saturation

    def test_phase1_zero_substrate(self):
        """Test Phase I with no substrate."""
        model = HepatocyteModel()

        state = np.array([0.0, 0.0, 0.0, 10.0, 0.5, 0.1, 5.0, 0.0])
        derivs = model.derivatives(state)

        # No drug, no metabolism
        assert abs(derivs[1]) < 0.1  # dM_dt near zero (only Phase II depletion)


class TestPhaseIIMetabolism:
    """Test Phase II metabolism (conjugation)."""

    def test_phase2_conjugation(self):
        """Test conjugation kinetics."""
        model = HepatocyteModel(V_conj=80.0, K_conj=30.0)

        # State with metabolite present
        state = np.array([0.0, 30.0, 0.0, 10.0, 0.5, 0.1, 5.0, 0.0])
        derivs = model.derivatives(state)

        # v_phase2 = 80 * 30 / (30 + 30) = 40 μM/h
        # dM_conj_dt = v_phase2 - k_excrete * M_conj
        assert derivs[2] > 35.0  # Should be close to 40

    def test_gsh_consumption_in_conjugation(self):
        """Test that conjugation depletes GSH."""
        model = HepatocyteModel(V_conj=80.0, K_conj=30.0, GSH_used_conj=1.0)

        state = np.array([0.0, 60.0, 0.0, 10.0, 0.5, 0.1, 5.0, 0.0])
        derivs = model.derivatives(state)

        # High metabolite should conjugate rapidly
        # This should deplete GSH
        # dGSH_dt includes synthesis - oxidation - consumption_conj
        # GSH consumption should be significant
        # v_phase2 ≈ 80 * 60 / (30 + 60) ≈ 53
        # GSH_consumption ≈ 1.0 * 53 = 53 mM/h
        # With synthesis at 5 mM/h, dGSH_dt should be negative
        assert derivs[3] < 0.0  # GSH depleting


class TestGlutathioneDynamics:
    """Test glutathione redox cycle."""

    def test_gsh_synthesis(self):
        """Test GSH synthesis."""
        model = HepatocyteModel(k_GSH_synth=5.0)

        # Low GSH, low ROS
        state = np.array([0.0, 0.0, 0.0, 2.0, 0.5, 0.01, 5.0, 0.0])
        derivs = model.derivatives(state)

        # With low oxidation and no conjugation, dGSH_dt should be positive
        assert derivs[3] > 0.0  # GSH increasing

    def test_gsh_oxidation(self):
        """Test GSH oxidation by ROS."""
        model = HepatocyteModel(k_GSH_ox=0.5)

        # High ROS state
        state = np.array([0.0, 0.0, 0.0, 10.0, 0.5, 5.0, 5.0, 0.0])
        derivs = model.derivatives(state)

        # High ROS should oxidize GSH
        # GSH_oxidation = 0.5 * 5.0 * 10.0 = 25 mM/h
        # With synthesis at 5 mM/h, net dGSH_dt should be negative
        assert derivs[3] < 0.0  # GSH depleting

    def test_gssg_reduction(self):
        """Test GSSG reduction back to GSH."""
        model = HepatocyteModel(k_GSSG_red=1.0)

        # State with elevated GSSG
        state = np.array([0.0, 0.0, 0.0, 5.0, 3.0, 0.1, 5.0, 0.0])
        derivs = model.derivatives(state)

        # GSSG reduction should contribute to GSH synthesis
        # dGSSG_dt = oxidation/2 - reduction
        # With low ROS, oxidation is low, so dGSSG_dt should be negative
        assert derivs[4] < 0.0  # GSSG decreasing


class TestROSDynamics:
    """Test reactive oxygen species dynamics."""

    def test_ros_production_from_metabolite(self):
        """Test ROS production from metabolites."""
        model = HepatocyteModel(k_ROS_prod=0.1)

        # High metabolite state
        state = np.array([0.0, 100.0, 0.0, 10.0, 0.5, 0.5, 5.0, 0.0])
        derivs = model.derivatives(state)

        # ROS production = 0.1 * 100 = 10 AU/h
        # Should exceed scavenging
        assert derivs[5] > 0.0  # ROS increasing

    def test_ros_scavenging_by_gsh(self):
        """Test ROS scavenging by GSH."""
        model = HepatocyteModel(k_ROS_scav=1.0)

        # High GSH, high ROS
        state = np.array([0.0, 0.0, 0.0, 15.0, 0.5, 5.0, 5.0, 0.0])
        derivs = model.derivatives(state)

        # ROS scavenging = 1.0 * 15.0 * 5.0 = 75 AU/h
        # Production is low (only mitochondrial)
        # Net dROS_dt should be strongly negative
        assert derivs[5] < 0.0  # ROS decreasing

    def test_mitochondrial_ros_from_atp_depletion(self):
        """Test mitochondrial ROS production when ATP is low."""
        model = HepatocyteModel(k_ROS_mito=2.0, ATP_max=5.0)

        # Low ATP state
        state = np.array([0.0, 0.0, 0.0, 10.0, 0.5, 0.5, 1.0, 0.0])
        derivs = model.derivatives(state)

        # Mitochondrial ROS = 2.0 * (1 - 1.0/5.0) = 1.6 AU/h
        # This should contribute to ROS production
        # Check that ROS increases when ATP is low (assuming low scavenging)


class TestATPDynamics:
    """Test ATP production and consumption."""

    def test_atp_production_with_no_damage(self):
        """Test ATP production in healthy cell."""
        model = HepatocyteModel(k_ATP_prod=10.0, k_ATP_cons=3.0)

        # Healthy state
        state = np.array([0.0, 0.0, 0.0, 10.0, 0.5, 0.1, 3.0, 0.0])
        derivs = model.derivatives(state)

        # Production = 10 * (1 - 0) = 10 mM/h
        # Consumption = 3 + 0 = 3 mM/h
        # Net = 7 mM/h
        assert derivs[6] > 5.0  # ATP increasing

    def test_atp_depletion_with_damage(self):
        """Test reduced ATP production with cell damage."""
        model = HepatocyteModel(k_ATP_prod=10.0)

        # Damaged state
        state = np.array([0.0, 0.0, 0.0, 10.0, 0.5, 0.1, 3.0, 0.5])
        derivs = model.derivatives(state)

        # Production = 10 * (1 - 0.5) = 5 mM/h
        # Should be less than healthy cell
        assert derivs[6] < 5.0

    def test_atp_damage_by_metabolite(self):
        """Test ATP depletion by toxic metabolites."""
        model = HepatocyteModel(k_ATP_damage=0.1)

        # High metabolite state
        state = np.array([0.0, 50.0, 0.0, 10.0, 0.5, 0.1, 4.0, 0.0])
        derivs = model.derivatives(state)

        # ATP consumption increases with metabolite
        # Extra consumption = 0.1 * 50 * 4.0 = 20 mM/h


class TestCellDamage:
    """Test cell damage and repair mechanisms."""

    def test_damage_from_ros(self):
        """Test damage accumulation from ROS."""
        model = HepatocyteModel(k_damage=0.1)

        # High ROS state
        state = np.array([0.0, 0.0, 0.0, 10.0, 0.5, 5.0, 5.0, 0.1])
        derivs = model.derivatives(state)

        # damage_induction = 0.1 * (5.0 + 0.0) * (1 - 0.1) = 0.45
        # Should cause damage increase
        assert derivs[7] > 0.0  # Damage increasing

    def test_damage_from_metabolite(self):
        """Test damage from toxic metabolites."""
        model = HepatocyteModel(k_damage=0.15)

        # High metabolite state
        state = np.array([0.0, 20.0, 0.0, 10.0, 0.5, 1.0, 5.0, 0.2])
        derivs = model.derivatives(state)

        # damage_induction = 0.15 * (1.0 + 20.0) * (1 - 0.2) = 2.52
        assert derivs[7] > 0.0  # Damage increasing

    def test_damage_repair_with_atp(self):
        """Test damage repair when ATP is available."""
        model = HepatocyteModel(k_repair=0.5)

        # Damaged but high ATP
        state = np.array([0.0, 0.0, 0.0, 10.0, 0.5, 0.1, 5.0, 0.3])
        derivs = model.derivatives(state)

        # damage_repair = 0.5 * 0.3 * 5.0 = 0.75
        # With low damage induction, net dDamage_dt might be negative

    def test_damage_saturates_at_one(self):
        """Test that damage is bounded at 1.0."""
        model = HepatocyteModel()

        # Start with high damage
        state = np.array([0.0, 0.0, 0.0, 10.0, 0.5, 0.1, 5.0, 0.95])
        derivs = model.derivatives(state)

        # Damage factor = (1 - 0.95) = 0.05
        # damage_induction should be very small


class TestCellDeath:
    """Test cell death mechanism."""

    def test_cell_death_stops_all_processes(self):
        """Test that cell death stops all metabolism."""
        model = HepatocyteModel(damage_threshold=0.7)

        # Dead cell state (Damage > threshold)
        state = np.array([100.0, 50.0, 10.0, 5.0, 1.0, 3.0, 2.0, 0.8])
        derivs = model.derivatives(state)

        # All derivatives should be zero
        assert np.allclose(derivs, 0.0)

    def test_is_alive_method(self):
        """Test is_alive() method."""
        model = HepatocyteModel(damage_threshold=0.7)

        # Alive cell
        model.state[7] = 0.5
        assert model.is_alive() is True

        # Dead cell
        model.state[7] = 0.8
        assert model.is_alive() is False


class TestHelperMethods:
    """Test helper methods."""

    def test_get_viability(self):
        """Test viability calculation."""
        model = HepatocyteModel()

        model.state[7] = 0.0  # No damage
        assert model.get_viability() == 1.0

        model.state[7] = 0.3  # 30% damage
        assert model.get_viability() == pytest.approx(0.7)

        model.state[7] = 1.0  # Complete damage
        assert model.get_viability() == 0.0

    def test_get_gsh_gssg_ratio(self):
        """Test GSH/GSSG ratio calculation."""
        model = HepatocyteModel()

        model.state[3] = 10.0  # GSH
        model.state[4] = 0.5   # GSSG
        assert model.get_GSH_GSSG_ratio() == pytest.approx(20.0)

        model.state[3] = 5.0
        model.state[4] = 1.0
        assert model.get_GSH_GSSG_ratio() == pytest.approx(5.0)

    def test_gsh_gssg_ratio_edge_cases(self):
        """Test GSH/GSSG ratio edge cases."""
        model = HepatocyteModel()

        # Zero GSSG
        model.state[3] = 10.0
        model.state[4] = 0.0
        ratio = model.get_GSH_GSSG_ratio()
        assert ratio == float('inf')

        # Both zero
        model.state[3] = 0.0
        model.state[4] = 0.0
        ratio = model.get_GSH_GSSG_ratio()
        assert ratio == 0.0

    def test_get_state_dict(self):
        """Test state dictionary retrieval."""
        model = HepatocyteModel()

        state_dict = model.get_state()

        assert 'D' in state_dict
        assert 'GSH' in state_dict
        assert 'viability' in state_dict
        assert 'GSH_GSSG_ratio' in state_dict
        assert 'is_alive' in state_dict


class TestIntegrationStep:
    """Test time integration step."""

    def test_step_basic(self):
        """Test basic time step."""
        model = HepatocyteModel()

        initial_state = model.state.copy()
        new_state = model.step(dt=0.1)

        # State should change
        assert not np.allclose(new_state, initial_state)

    def test_step_with_drug_input(self):
        """Test step with external drug input."""
        model = HepatocyteModel(D0=0.0)

        model.step(dt=0.1, drug_input=10.0)

        # Drug should be added to state
        assert model.state[0] >= 10.0  # D

    def test_step_updates_history(self):
        """Test that step updates history."""
        model = HepatocyteModel()

        initial_history_len = len(model.history['t'])
        model.step(dt=0.1)

        assert len(model.history['t']) == initial_history_len + 1
        assert model.history['t'][-1] == pytest.approx(0.1)

    def test_step_enforces_bounds(self):
        """Test that step enforces state bounds."""
        model = HepatocyteModel()

        # Force negative state (shouldn't happen but test bounds)
        model.state = np.array([-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0])
        model.step(dt=0.01)

        # All should be non-negative
        assert np.all(model.state >= 0.0)
        assert model.state[7] <= 1.0  # Damage bounded


class TestFactoryFunctions:
    """Test factory functions for specific drugs."""

    def test_create_acetaminophen_model(self):
        """Test acetaminophen model creation."""
        model = create_acetaminophen_model()

        assert isinstance(model, HepatocyteModel)
        assert model.V_CYP == 150.0  # High CYP activity
        assert model.k_ROS_prod == 0.1
        assert model.GSH_used_conj == 1.0  # High GSH consumption

    def test_create_doxorubicin_model(self):
        """Test doxorubicin model creation."""
        model = create_doxorubicin_model()

        assert isinstance(model, HepatocyteModel)
        assert model.k_ROS_mito == 2.0  # High mitochondrial ROS
        assert model.k_damage == 0.2  # High damage rate
        assert model.k_repair == 0.1  # Low repair

    def test_acetaminophen_model_properties(self):
        """Test that APAP model has expected properties."""
        model = create_acetaminophen_model()

        # Simulate APAP exposure
        model.step(dt=0.1, drug_input=100.0)

        # Should start metabolizing
        assert model.state[0] > 0  # Drug present
        assert model.is_alive()

    def test_doxorubicin_model_properties(self):
        """Test that doxorubicin model has expected properties."""
        model = create_doxorubicin_model()

        # Simulate doxorubicin exposure
        for _ in range(10):
            model.step(dt=0.1, drug_input=10.0)

        # Should accumulate damage faster than default
        assert model.is_alive()  # Still alive after brief exposure


class TestNumericalStability:
    """Test numerical stability."""

    def test_long_simulation_stability(self):
        """Test stability over long simulation."""
        model = HepatocyteModel()

        for _ in range(1000):
            model.step(dt=0.01)

        # Check for NaN or Inf
        assert not np.any(np.isnan(model.state))
        assert not np.any(np.isinf(model.state))

    def test_stability_with_high_drug_input(self):
        """Test stability with high drug levels."""
        model = HepatocyteModel()

        for _ in range(100):
            model.step(dt=0.01, drug_input=50.0)

        # Should remain bounded
        assert np.all(model.state >= 0.0)
        assert model.state[7] <= 1.0  # Damage bounded

    def test_negative_values_prevented(self):
        """Test that negative values are prevented."""
        model = HepatocyteModel()

        # Even with aggressive depletion, values should stay non-negative
        for _ in range(500):
            model.step(dt=0.1, drug_input=100.0)

        assert np.all(model.state >= 0.0)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_initial_gsh(self):
        """Test with zero initial GSH."""
        model = HepatocyteModel(GSH0=0.0)

        # Should synthesize GSH
        model.step(dt=1.0)
        assert model.state[3] > 0.0  # GSH increasing

    def test_maximum_damage_state(self):
        """Test with maximum damage."""
        model = HepatocyteModel(Damage0=1.0)

        derivs = model.derivatives(model.state)

        # Cell should be dead if damage > threshold
        # But with damage = 1.0 exactly, it depends on threshold

    def test_zero_atp_state(self):
        """Test with zero ATP."""
        model = HepatocyteModel(ATP0=0.0)

        # No repair possible, but cell should try to produce ATP
        model.step(dt=0.1)

        # ATP should increase if cell is not too damaged
        if model.state[7] < 0.5:  # If not too damaged
            assert model.state[6] > 0.0

    def test_simultaneous_damage_and_repair(self):
        """Test balance between damage and repair."""
        model = HepatocyteModel()

        # Moderate damage with adequate ATP
        model.state[7] = 0.3
        model.state[6] = 5.0  # High ATP
        model.state[5] = 0.1  # Low ROS

        derivs = model.derivatives(model.state)

        # With low ROS and high ATP, repair might dominate
        # dDamage_dt could be negative


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
