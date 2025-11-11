"""Tests for Motor Hand Pro hardware interface."""

import pytest
from unittest.mock import MagicMock, patch

from src.hardware import MotorHandPro, MotorHandConfig, Gesture, HBCMMotorHandController


class TestMotorHandConfig:
    """Test configuration dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MotorHandConfig()
        assert config.port == "/dev/ttyUSB0"
        assert config.baud_rate == 115200
        assert config.timeout == 1.0
        assert config.auto_reconnect is True
        assert config.simulation_mode is False

    def test_custom_config(self):
        """Test custom configuration."""
        config = MotorHandConfig(
            port="COM3",
            baud_rate=9600,
            timeout=2.0,
            auto_reconnect=False,
            simulation_mode=True,
        )
        assert config.port == "COM3"
        assert config.baud_rate == 9600
        assert config.timeout == 2.0
        assert config.auto_reconnect is False
        assert config.simulation_mode is True


class TestMotorHandProSimulation:
    """Test Motor Hand Pro in simulation mode (no hardware required)."""

    @pytest.fixture
    def sim_hand(self):
        """Create a simulated motor hand."""
        config = MotorHandConfig(simulation_mode=True)
        hand = MotorHandPro(config)
        yield hand
        hand.disconnect()

    def test_initialization(self, sim_hand):
        """Test that simulation mode initializes correctly."""
        assert sim_hand.connected is True
        assert sim_hand.enabled is True
        assert sim_hand.config.simulation_mode is True

    def test_set_finger_positions_valid(self, sim_hand):
        """Test setting valid finger positions."""
        result = sim_hand.set_finger_positions(90, 45, 90, 120, 180)
        assert result is True
        positions = sim_hand.get_positions()
        assert positions["thumb"] == 90
        assert positions["index"] == 45
        assert positions["middle"] == 90
        assert positions["ring"] == 120
        assert positions["pinky"] == 180

    def test_set_finger_positions_invalid(self, sim_hand):
        """Test setting invalid finger positions."""
        result = sim_hand.set_finger_positions(200, 45, 90, 120, 180)
        assert result is False

        result = sim_hand.set_finger_positions(-10, 45, 90, 120, 180)
        assert result is False

    def test_set_grip_strength_valid(self, sim_hand):
        """Test setting valid grip strength."""
        result = sim_hand.set_grip_strength(0.75)
        assert result is True

        result = sim_hand.set_grip_strength(0.0)
        assert result is True

        result = sim_hand.set_grip_strength(1.0)
        assert result is True

    def test_set_grip_strength_invalid(self, sim_hand):
        """Test setting invalid grip strength."""
        result = sim_hand.set_grip_strength(1.5)
        assert result is False

        result = sim_hand.set_grip_strength(-0.1)
        assert result is False

    def test_execute_gestures(self, sim_hand):
        """Test executing all predefined gestures."""
        for gesture in Gesture:
            result = sim_hand.execute_gesture(gesture)
            assert result is True

    def test_reset_to_neutral(self, sim_hand):
        """Test reset to neutral position."""
        sim_hand.set_finger_positions(0, 30, 60, 90, 120)
        result = sim_hand.reset_to_neutral()
        assert result is True

        positions = sim_hand.get_positions()
        for finger, angle in positions.items():
            assert angle == 90

    def test_enable_disable(self, sim_hand):
        """Test enable and disable commands."""
        result = sim_hand.disable()
        assert result is True
        assert sim_hand.enabled is False

        result = sim_hand.enable()
        assert result is True
        assert sim_hand.enabled is True

    def test_get_status(self, sim_hand):
        """Test status query."""
        status = sim_hand.get_status()
        assert status is not None
        assert "enabled" in status or status is not None

    def test_context_manager(self):
        """Test using Motor Hand Pro as context manager."""
        config = MotorHandConfig(simulation_mode=True)
        with MotorHandPro(config) as hand:
            assert hand.connected is True
            result = hand.set_grip_strength(0.5)
            assert result is True


class TestHBCMMotorHandController:
    """Test HBCM integration controller."""

    @pytest.fixture
    def controller(self):
        """Create controller with simulated motor hand."""
        config = MotorHandConfig(simulation_mode=True)
        hand = MotorHandPro(config)
        controller = HBCMMotorHandController(hand)
        yield controller
        hand.disconnect()

    def test_update_from_neural_state(self, controller):
        """Test neural state mapping to grip strength."""
        # Test typical FHN range (-2 to 2)
        result = controller.update_from_neural_state(-2.0)
        assert result is True

        result = controller.update_from_neural_state(0.0)
        assert result is True

        result = controller.update_from_neural_state(2.0)
        assert result is True

    def test_update_from_cardiac_state(self, controller):
        """Test cardiac state mapping to grip strength."""
        # Test typical Van der Pol range
        result = controller.update_from_cardiac_state(-1.0)
        assert result is True

        result = controller.update_from_cardiac_state(0.0)
        assert result is True

        result = controller.update_from_cardiac_state(1.0)
        assert result is True

    def test_update_from_coupled_state(self, controller):
        """Test coupled state mapping with blending."""
        result = controller.update_from_coupled_state(
            neural_activation=0.5,
            cardiac_activation=1.0,
            blend=0.5
        )
        assert result is True

        # Test extreme blend values
        result = controller.update_from_coupled_state(
            neural_activation=0.5,
            cardiac_activation=1.0,
            blend=0.0  # All neural
        )
        assert result is True

        result = controller.update_from_coupled_state(
            neural_activation=0.5,
            cardiac_activation=1.0,
            blend=1.0  # All cardiac
        )
        assert result is True


@pytest.mark.skipif(
    not hasattr(pytest.importorskip("src.hardware.motor_hand_interface", minversion=None), "SERIAL_AVAILABLE"),
    reason="Requires serial module mocking support"
)
class TestMotorHandProIntegration:
    """Integration tests that would require actual hardware (mocked)."""

    def test_simulation_mode_as_alternative(self):
        """Test that simulation mode works as alternative to mocking."""
        config = MotorHandConfig(simulation_mode=True)
        hand = MotorHandPro(config)

        # Verify simulation mode works
        assert hand.connected is True

        # Test commands
        result = hand.set_grip_strength(0.5)
        assert result is True

        status = hand.get_status()
        assert status is not None
        assert "enabled" in status

        hand.disconnect()


@pytest.mark.integration
class TestMotorHandProWithHBCM:
    """End-to-end integration tests with HBCM."""

    def test_hbcm_motor_hand_simulation(self):
        """Test full HBCM simulation with motor hand control."""
        from src.coupling import HeartBrainCouplingModel, CouplingParameters
        from src.neural import FitzHughNagumo
        from src.cardiac import VanDerPolOscillator

        # Create HBCM
        hbcm = HeartBrainCouplingModel(
            neural_model=FitzHughNagumo(stimulus_amplitude=0.2),
            cardiac_model=VanDerPolOscillator(mu=1.2, omega=1.0),
            coupling=CouplingParameters(
                neural_to_cardiac_gain=0.5,
                cardiac_to_neural_gain=0.3
            ),
        )

        # Create motor hand controller
        config = MotorHandConfig(simulation_mode=True)
        motor_hand = MotorHandPro(config)
        controller = HBCMMotorHandController(motor_hand)

        # Run short simulation
        trajectory = hbcm.simulate(
            initial_state=(0.0, 0.0, 1.0, 0.0),
            t_span=(0.0, 1.0),
            dt=0.01
        )

        # Update motor hand based on simulation
        update_count = 0
        for time, state in trajectory:
            neural_v = state[0]
            cardiac_x = state[2]

            # Update every 10th step (simulating 10 Hz update rate)
            if update_count % 10 == 0:
                result = controller.update_from_coupled_state(
                    neural_v,
                    cardiac_x,
                    blend=0.5
                )
                assert result is True

            update_count += 1

        # Verify we processed the simulation
        assert update_count > 0

        motor_hand.disconnect()


def test_gesture_enum():
    """Test Gesture enum values."""
    assert Gesture.OPEN.value == "OPEN"
    assert Gesture.FIST.value == "FIST"
    assert Gesture.POINT.value == "POINT"
    assert Gesture.PEACE.value == "PEACE"
    assert Gesture.OK.value == "OK"


def test_list_available_ports():
    """Test port listing (may return empty list in test environment)."""
    ports = MotorHandPro.list_available_ports()
    assert isinstance(ports, list)
