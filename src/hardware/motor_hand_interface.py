"""Serial interface for Motor Hand Pro Arduino controller."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

try:
    import serial
    import serial.tools.list_ports

    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    logging.warning("pyserial not installed. Motor Hand Pro interface will run in simulation mode.")

logger = logging.getLogger(__name__)


class Gesture(Enum):
    """Predefined hand gestures."""

    OPEN = "OPEN"
    FIST = "FIST"
    POINT = "POINT"
    PEACE = "PEACE"
    OK = "OK"


@dataclass
class MotorHandConfig:
    """Configuration for Motor Hand Pro serial connection."""

    port: str = "/dev/ttyUSB0"  # Linux/Mac default
    baud_rate: int = 115200
    timeout: float = 1.0
    auto_reconnect: bool = True
    reconnect_delay: float = 2.0
    simulation_mode: bool = False


class MotorHandPro:
    """Interface to Motor Hand Pro prosthetic hand via serial communication."""

    def __init__(self, config: Optional[MotorHandConfig] = None):
        """Initialize Motor Hand Pro interface.

        Args:
            config: Configuration object. If None, uses defaults.
        """
        self.config = config or MotorHandConfig()

        if not SERIAL_AVAILABLE and not self.config.simulation_mode:
            logger.warning("Forcing simulation mode - pyserial not available")
            self.config.simulation_mode = True

        self.serial_port: Optional[serial.Serial] = None
        self.connected = False
        self.lock = threading.Lock()

        # Current state tracking
        self.current_positions: Dict[str, int] = {
            "thumb": 90,
            "index": 90,
            "middle": 90,
            "ring": 90,
            "pinky": 90,
        }
        self.enabled = False

        if not self.config.simulation_mode:
            self.connect()
        else:
            logger.info("Motor Hand Pro running in SIMULATION mode")
            self.connected = True
            self.enabled = True

    def connect(self) -> bool:
        """Establish serial connection to Arduino.

        Returns:
            True if connection successful, False otherwise.
        """
        if self.config.simulation_mode:
            return True

        if not SERIAL_AVAILABLE:
            logger.error("Cannot connect: pyserial not installed")
            return False

        try:
            with self.lock:
                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.close()

                logger.info(f"Connecting to Motor Hand Pro on {self.config.port}")
                self.serial_port = serial.Serial(
                    port=self.config.port,
                    baudrate=self.config.baud_rate,
                    timeout=self.config.timeout,
                )

                # Wait for Arduino to reset
                time.sleep(2)

                # Flush buffers
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()

                self.connected = True
                logger.info("Motor Hand Pro connected successfully")

                # Get initial status
                status = self.get_status()
                if status:
                    logger.info(f"Initial status: {status}")

                return True

        except serial.SerialException as e:
            logger.error(f"Failed to connect: {e}")
            self.connected = False
            return False

    def disconnect(self) -> None:
        """Close serial connection."""
        if self.config.simulation_mode:
            logger.info("Simulation mode - disconnect simulated")
            return

        with self.lock:
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.close()
                    logger.info("Motor Hand Pro disconnected")
                except Exception as e:
                    logger.error(f"Error during disconnect: {e}")
            self.connected = False

    def _send_command(self, command: str) -> Optional[str]:
        """Send command to Arduino and wait for response.

        Args:
            command: Command string (without delimiters).

        Returns:
            Response string or None if error/timeout.
        """
        if self.config.simulation_mode:
            logger.debug(f"SIM: Sending command: {command}")
            cmd_type = command.split(',')[0]

            # Simulate proper responses for different command types
            if cmd_type == "STATUS":
                positions = self.current_positions
                status = "ENABLED" if self.enabled else "DISABLED"
                return f"<STATUS,{status},{positions['thumb']},{positions['index']},{positions['middle']},{positions['ring']},{positions['pinky']}>"
            else:
                return f"<ACK,{cmd_type}>"

        if not self.connected:
            if self.config.auto_reconnect:
                logger.warning("Not connected, attempting reconnect...")
                time.sleep(self.config.reconnect_delay)
                if not self.connect():
                    return None
            else:
                logger.error("Not connected and auto_reconnect disabled")
                return None

        with self.lock:
            try:
                # Format with delimiters
                formatted_command = f"<{command}>\n"
                self.serial_port.write(formatted_command.encode())
                logger.debug(f"Sent: {formatted_command.strip()}")

                # Read response
                response = self.serial_port.readline().decode().strip()
                logger.debug(f"Received: {response}")

                return response

            except serial.SerialException as e:
                logger.error(f"Serial communication error: {e}")
                self.connected = False
                return None
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return None

    def set_finger_positions(
        self, thumb: int, index: int, middle: int, ring: int, pinky: int
    ) -> bool:
        """Set individual finger positions.

        Args:
            thumb: Thumb angle (0-180 degrees).
            index: Index finger angle (0-180 degrees).
            middle: Middle finger angle (0-180 degrees).
            ring: Ring finger angle (0-180 degrees).
            pinky: Pinky finger angle (0-180 degrees).

        Returns:
            True if command successful, False otherwise.
        """
        # Validate inputs
        positions = [thumb, index, middle, ring, pinky]
        if not all(0 <= pos <= 180 for pos in positions):
            logger.error("Finger positions must be in range 0-180 degrees")
            return False

        command = f"SET,{thumb},{index},{middle},{ring},{pinky}"
        response = self._send_command(command)

        if response and "ACK" in response:
            self.current_positions = {
                "thumb": thumb,
                "index": index,
                "middle": middle,
                "ring": ring,
                "pinky": pinky,
            }
            return True

        logger.error(f"SET command failed: {response}")
        return False

    def set_grip_strength(self, strength: float) -> bool:
        """Set grip strength as percentage.

        Args:
            strength: Grip strength 0.0-1.0 (0=open, 1=fully closed).

        Returns:
            True if command successful, False otherwise.
        """
        if not 0.0 <= strength <= 1.0:
            logger.error("Grip strength must be in range 0.0-1.0")
            return False

        percentage = int(strength * 100)
        command = f"GRIP,{percentage}"
        response = self._send_command(command)

        if response and "ACK" in response:
            logger.info(f"Grip strength set to {percentage}%")
            return True

        logger.error(f"GRIP command failed: {response}")
        return False

    def execute_gesture(self, gesture: Gesture) -> bool:
        """Execute a predefined gesture.

        Args:
            gesture: Gesture enum value.

        Returns:
            True if command successful, False otherwise.
        """
        command = f"GESTURE,{gesture.value}"
        response = self._send_command(command)

        if response and "ACK" in response:
            logger.info(f"Executed gesture: {gesture.value}")
            return True

        logger.error(f"GESTURE command failed: {response}")
        return False

    def reset_to_neutral(self) -> bool:
        """Return all fingers to neutral (90 degree) position.

        Returns:
            True if command successful, False otherwise.
        """
        response = self._send_command("NEUTRAL")

        if response and "ACK" in response:
            self.current_positions = {k: 90 for k in self.current_positions}
            logger.info("Reset to neutral position")
            return True

        logger.error(f"NEUTRAL command failed: {response}")
        return False

    def enable(self) -> bool:
        """Enable the motor hand control system.

        Returns:
            True if command successful, False otherwise.
        """
        response = self._send_command("ENABLE")

        if response and "ACK" in response:
            self.enabled = True
            logger.info("Motor Hand Pro enabled")
            return True

        logger.error(f"ENABLE command failed: {response}")
        return False

    def disable(self) -> bool:
        """Disable the motor hand (returns to neutral and stops accepting movement commands).

        Returns:
            True if command successful, False otherwise.
        """
        response = self._send_command("DISABLE")

        if response and "ACK" in response:
            self.enabled = False
            logger.info("Motor Hand Pro disabled")
            return True

        logger.error(f"DISABLE command failed: {response}")
        return False

    def get_status(self) -> Optional[Dict[str, any]]:
        """Get current status and positions from the hand.

        Returns:
            Dictionary with status information or None if failed.
        """
        response = self._send_command("STATUS")

        if not response or "STATUS" not in response:
            return None

        try:
            # Parse response: <STATUS,ENABLED,thumb,index,middle,ring,pinky>
            parts = response.strip("<>").split(",")
            if len(parts) < 7:
                return None

            status = {
                "enabled": parts[1] == "ENABLED",
                "positions": {
                    "thumb": int(parts[2]),
                    "index": int(parts[3]),
                    "middle": int(parts[4]),
                    "ring": int(parts[5]),
                    "pinky": int(parts[6]),
                },
            }

            self.enabled = status["enabled"]
            self.current_positions = status["positions"]

            return status

        except (ValueError, IndexError) as e:
            logger.error(f"Failed to parse status response: {e}")
            return None

    def get_positions(self) -> Dict[str, int]:
        """Get current finger positions (cached values).

        Returns:
            Dictionary of finger positions.
        """
        return self.current_positions.copy()

    @staticmethod
    def list_available_ports() -> List[str]:
        """List available serial ports.

        Returns:
            List of port names.
        """
        if not SERIAL_AVAILABLE:
            logger.warning("pyserial not available")
            return []

        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def __del__(self):
        """Destructor."""
        if hasattr(self, "serial_port"):
            self.disconnect()


class HBCMMotorHandController:
    """Controller that maps HBCM physiological signals to Motor Hand Pro movements."""

    def __init__(self, motor_hand: MotorHandPro):
        """Initialize HBCM-driven controller.

        Args:
            motor_hand: MotorHandPro interface instance.
        """
        self.motor_hand = motor_hand

    def update_from_neural_state(self, neural_activation: float) -> bool:
        """Update hand based on neural activation level.

        Maps neural activation to grip strength.

        Args:
            neural_activation: Neural state value (typically -2 to 2 for FHN).

        Returns:
            True if update successful.
        """
        # Normalize neural activation to 0-1 range
        # Assume typical FHN range of -2 to 2
        normalized = (neural_activation + 2.0) / 4.0
        normalized = max(0.0, min(1.0, normalized))

        return self.motor_hand.set_grip_strength(normalized)

    def update_from_cardiac_state(self, cardiac_activation: float) -> bool:
        """Update hand based on cardiac activation level.

        Maps cardiac activation to grip strength.

        Args:
            cardiac_activation: Cardiac state value.

        Returns:
            True if update successful.
        """
        # Normalize cardiac activation to 0-1 range
        # Van der Pol typically oscillates around 0
        normalized = abs(cardiac_activation) / 3.0
        normalized = max(0.0, min(1.0, normalized))

        return self.motor_hand.set_grip_strength(normalized)

    def update_from_coupled_state(
        self, neural_activation: float, cardiac_activation: float, blend: float = 0.5
    ) -> bool:
        """Update hand based on blended neural and cardiac states.

        Args:
            neural_activation: Neural state value.
            cardiac_activation: Cardiac state value.
            blend: Blending factor (0=all neural, 1=all cardiac).

        Returns:
            True if update successful.
        """
        neural_norm = (neural_activation + 2.0) / 4.0
        neural_norm = max(0.0, min(1.0, neural_norm))

        cardiac_norm = abs(cardiac_activation) / 3.0
        cardiac_norm = max(0.0, min(1.0, cardiac_norm))

        combined = (1 - blend) * neural_norm + blend * cardiac_norm

        return self.motor_hand.set_grip_strength(combined)
