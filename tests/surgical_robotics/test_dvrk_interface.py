"""
Tests for dVRK (da Vinci Research Kit) interface
"""

import pytest
import numpy as np
from src.surgical_robotics import (
    DVRKInterface,
    DVRKConfiguration,
    DVRKArmType,
    DVRKCartesianCommand,
    DVRKJointCommand,
    DVRKOperatingState,
)


@pytest.fixture
def dvrk_config():
    """Create default dVRK configuration"""
    return DVRKConfiguration(
        arm_type=DVRKArmType.PSM1,
        arm_name="PSM1",
        enable_physio_feedback=True,
    )


@pytest.fixture
def dvrk_interface(dvrk_config):
    """Create dVRK interface instance"""
    return DVRKInterface(dvrk_config)


def test_dvrk_initialization(dvrk_interface):
    """Test dVRK interface initialization"""
    assert dvrk_interface is not None
    assert dvrk_interface.config.arm_name == "PSM1"
    assert dvrk_interface._operating_state == DVRKOperatingState.DISABLED


def test_dvrk_enable(dvrk_interface):
    """Test enabling dVRK arm"""
    result = dvrk_interface.enable()
    assert result is True
    assert dvrk_interface._operating_state == DVRKOperatingState.ENABLED


def test_dvrk_home(dvrk_interface):
    """Test homing dVRK arm"""
    dvrk_interface.enable()
    result = dvrk_interface.home()
    assert result is True
    assert np.allclose(dvrk_interface._sim_joint_positions, 0.0)


def test_dvrk_cartesian_motion(dvrk_interface):
    """Test Cartesian motion command"""
    dvrk_interface.enable()

    target_pos = np.array([0.02, 0.01, -0.12])
    target_ori = np.array([0, 0, 0, 1])
    cmd = DVRKCartesianCommand(target_pos, target_ori)

    result = dvrk_interface.move_cartesian(cmd)
    assert result is True

    state = dvrk_interface.get_measured_state()
    assert np.allclose(state.cartesian_position, target_pos)


def test_dvrk_workspace_limits(dvrk_interface):
    """Test workspace limit checking"""
    dvrk_interface.enable()

    # Valid position
    valid_pos = np.array([0.05, 0.05, -0.10])
    assert dvrk_interface._check_workspace_limits(valid_pos) is True

    # Invalid position (outside limits)
    invalid_pos = np.array([0.5, 0.5, 0.5])
    assert dvrk_interface._check_workspace_limits(invalid_pos) is False


def test_dvrk_physiological_integration(dvrk_interface):
    """Test physiological feedback integration"""
    # Normal state
    velocity_scale = dvrk_interface.integrate_physiological_feedback(
        heart_rate=70.0,
        blood_pressure=90.0,
        stress_level=0.2
    )
    assert 0.8 <= velocity_scale <= 1.0

    # Elevated heart rate
    velocity_scale = dvrk_interface.integrate_physiological_feedback(
        heart_rate=120.0,
        blood_pressure=90.0,
        stress_level=0.5
    )
    assert velocity_scale < 0.7


def test_dvrk_gripper_control(dvrk_interface):
    """Test gripper control"""
    dvrk_interface.enable()

    result = dvrk_interface.open_gripper(40.0)
    assert result is True

    result = dvrk_interface.close_gripper()
    assert result is True


def test_dvrk_joint_motion(dvrk_interface):
    """Test joint space motion"""
    dvrk_interface.enable()

    joint_positions = np.array([0.1, 0.2, 0.15, 0.0, 0.0, 0.0, 0.0])
    cmd = DVRKJointCommand(joint_positions)

    result = dvrk_interface.move_joint(cmd)
    assert result is True


def test_dvrk_ros2_export(dvrk_interface):
    """Test ROS2 message export"""
    dvrk_interface.enable()
    state = dvrk_interface.get_measured_state()

    ros2_msg = dvrk_interface.export_state_to_ros2_msg(state)

    assert 'measured_cp' in ros2_msg
    assert 'measured_jp' in ros2_msg
    assert 'header' in ros2_msg['measured_cp']
    assert 'pose' in ros2_msg['measured_cp']
