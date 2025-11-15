"""Bridge module connecting BCI neural data to the heart-brain coupling model.

This module provides the interface between real-time neural recordings
(OpenBCI, Neuralink) and the FitzHugh-Nagumo neural oscillator, enabling
closed-loop brain-computer interfaces for cardiac modulation.
"""

from __future__ import annotations

import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass

from .openbci_interface import OpenBCIInterface, OpenBCIConfig
from .neuralink_adapter import NeuralinkAdapter, NeuralinkConfig
from ..coupling.hbcm import HeartBrainCouplingModel, CouplingParameters
from ..neural.fhn import FitzHughNagumo
from ..cardiac.van_der_pol import VanDerPolOscillator


@dataclass
class BCIBridgeConfig:
    """Configuration for BCI-to-model bridge.

    Parameters
    ----------
    bci_type : str
        Type of BCI: 'openbci' or 'neuralink'
    update_rate_hz : float
        How often to update model with BCI data
    neural_drive_method : str
        Method for extracting neural drive from BCI
    gain : float
        Scaling factor for BCI signal to model input
    use_adaptive_gain : bool
        Enable adaptive gain based on signal statistics
    """

    bci_type: str = "openbci"
    update_rate_hz: float = 10.0  # Update model 10x per second
    neural_drive_method: str = "alpha_beta_ratio"
    gain: float = 0.5
    use_adaptive_gain: bool = False


class NeuralToBrainModelBridge:
    """Bridge connecting real-time BCI data to the heart-brain coupling model.

    This class enables closed-loop BCI control where:
    1. Neural activity is recorded via BCI (OpenBCI or Neuralink)
    2. Neural features are extracted (band power, firing rate, etc.)
    3. Features modulate the neural oscillator in the coupling model
    4. Model generates cardiac predictions
    5. Cardiac state can be used for biofeedback/control

    Examples
    --------
    >>> # Setup with OpenBCI
    >>> bci_config = OpenBCIConfig(sample_rate=250, num_channels=8)
    >>> bridge_config = BCIBridgeConfig(bci_type='openbci')
    >>> bridge = NeuralToBrainModelBridge(
    ...     bci_config=bci_config,
    ...     bridge_config=bridge_config,
    ... )
    >>>
    >>> # Start closed-loop system
    >>> bridge.start()
    >>>
    >>> # Run simulation step
    >>> neural_drive = bridge.get_current_neural_drive()
    >>> model_state = bridge.step_coupled_model(dt=0.01)
    >>>
    >>> bridge.stop()
    """

    def __init__(
        self,
        bci_config: Optional[OpenBCIConfig | NeuralinkConfig] = None,
        bridge_config: Optional[BCIBridgeConfig] = None,
        coupling_params: Optional[CouplingParameters] = None,
        mock_mode: bool = True,
    ):
        """Initialize BCI-to-model bridge.

        Parameters
        ----------
        bci_config : OpenBCIConfig or NeuralinkConfig
            BCI hardware configuration
        bridge_config : BCIBridgeConfig
            Bridge behavior configuration
        coupling_params : CouplingParameters
            Heart-brain coupling parameters
        mock_mode : bool
            Use synthetic data for testing
        """
        self.bridge_config = bridge_config or BCIBridgeConfig()
        self.mock_mode = mock_mode

        # Initialize BCI interface
        if self.bridge_config.bci_type == "openbci":
            if bci_config is None or isinstance(bci_config, OpenBCIConfig):
                self.bci = OpenBCIInterface(
                    config=bci_config or OpenBCIConfig(),
                    mock_mode=mock_mode,
                )
            else:
                raise ValueError("bci_config must be OpenBCIConfig for bci_type='openbci'")
        elif self.bridge_config.bci_type == "neuralink":
            if bci_config is None or isinstance(bci_config, NeuralinkConfig):
                self.bci = NeuralinkAdapter(
                    config=bci_config or NeuralinkConfig(),
                    mock_mode=mock_mode,
                )
            else:
                raise ValueError("bci_config must be NeuralinkConfig for bci_type='neuralink'")
        else:
            raise ValueError(f"Unknown bci_type: {self.bridge_config.bci_type}")

        # Initialize heart-brain coupling model
        self.coupling_model = HeartBrainCouplingModel(
            neural_model=FitzHughNagumo(),
            cardiac_model=VanDerPolOscillator(),
            coupling=coupling_params or CouplingParameters(),
        )

        # Current model state: (v, w, x, y)
        self.model_state: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 0.0)
        self.model_time: float = 0.0

        # BCI signal history
        self.neural_drive_history: List[Tuple[float, float]] = []  # (time, drive)

        # Adaptive gain
        self.current_gain = self.bridge_config.gain

        # Running flag
        self.is_running = False

    def start(self) -> None:
        """Start the BCI and begin data acquisition."""
        if self.is_running:
            print("Bridge already running")
            return

        # Start BCI
        if isinstance(self.bci, OpenBCIInterface):
            self.bci.start_stream()
        else:  # Neuralink
            self.bci.start_recording()

        self.is_running = True
        print(f"BCI-to-model bridge started ({self.bridge_config.bci_type})")

    def stop(self) -> None:
        """Stop the BCI and data acquisition."""
        if not self.is_running:
            return

        # Stop BCI
        if isinstance(self.bci, OpenBCIInterface):
            self.bci.stop_stream()
        else:  # Neuralink
            self.bci.stop_recording()

        self.is_running = False
        print("BCI-to-model bridge stopped")

    def get_current_neural_drive(self) -> float:
        """Extract current neural drive signal from BCI.

        Returns
        -------
        drive : float
            Neural drive signal (0-1 range)
        """
        if isinstance(self.bci, OpenBCIInterface):
            drive = self.bci.compute_neural_drive(
                channel=0,  # Could be made configurable
                method=self.bridge_config.neural_drive_method,
            )
        else:  # Neuralink
            drive = self.bci.compute_neural_drive_signal(
                method=self.bridge_config.neural_drive_method,
            )

        # Apply gain
        drive = drive * self.current_gain

        # Store in history
        self.neural_drive_history.append((self.model_time, drive))

        # Limit history size
        if len(self.neural_drive_history) > 10000:
            self.neural_drive_history = self.neural_drive_history[-5000:]

        return drive

    def update_adaptive_gain(self, neural_drive: float) -> None:
        """Update gain based on signal statistics.

        Parameters
        ----------
        neural_drive : float
            Current neural drive value
        """
        if not self.bridge_config.use_adaptive_gain:
            return

        # Simple adaptive scheme: adjust gain to keep drive in reasonable range
        target_range = (0.2, 0.8)  # Desired drive range

        if neural_drive < target_range[0]:
            # Increase gain if signal too weak
            self.current_gain *= 1.01
        elif neural_drive > target_range[1]:
            # Decrease gain if signal too strong
            self.current_gain *= 0.99

        # Limit gain range
        self.current_gain = np.clip(self.current_gain, 0.1, 2.0)

    def step_coupled_model(
        self,
        dt: float = 0.01,
        use_bci_drive: bool = True,
    ) -> Tuple[float, float, float, float]:
        """Advance the coupled heart-brain model by one timestep.

        Parameters
        ----------
        dt : float
            Integration timestep (seconds)
        use_bci_drive : bool
            If True, use BCI neural drive; if False, use model's internal dynamics

        Returns
        -------
        state : tuple
            (v, w, x, y) - neural and cardiac state
        """
        if use_bci_drive and self.is_running:
            # Get neural drive from BCI
            neural_drive = self.get_current_neural_drive()

            # Update adaptive gain
            self.update_adaptive_gain(neural_drive)

            # Inject drive into neural model
            # We'll temporarily override the neural model's stimulus
            original_stimulus = self.coupling_model.neural_model.stimulus_amplitude
            self.coupling_model.neural_model.stimulus_amplitude = neural_drive

            # Step model
            self.model_state = self.coupling_model.step(
                self.model_time,
                self.model_state,
                dt,
            )

            # Restore original stimulus
            self.coupling_model.neural_model.stimulus_amplitude = original_stimulus

        else:
            # Use model's internal dynamics only
            self.model_state = self.coupling_model.step(
                self.model_time,
                self.model_state,
                dt,
            )

        self.model_time += dt

        return self.model_state

    def get_cardiac_state(self) -> Tuple[float, float]:
        """Get current cardiac oscillator state.

        Returns
        -------
        cardiac_state : tuple
            (x, y) - cardiac position and velocity
        """
        return self.model_state[2], self.model_state[3]

    def get_neural_state(self) -> Tuple[float, float]:
        """Get current neural oscillator state.

        Returns
        -------
        neural_state : tuple
            (v, w) - neural voltage and recovery
        """
        return self.model_state[0], self.model_state[1]

    def run_closed_loop_simulation(
        self,
        duration: float,
        dt: float = 0.01,
    ) -> Tuple[List[float], List[Tuple[float, float, float, float]], List[float]]:
        """Run a closed-loop simulation with BCI feedback.

        Parameters
        ----------
        duration : float
            Simulation duration (seconds)
        dt : float
            Integration timestep (seconds)

        Returns
        -------
        times : List[float]
            Time points
        states : List[tuple]
            Model states (v, w, x, y)
        drives : List[float]
            Neural drive values from BCI
        """
        if not self.is_running:
            self.start()

        times = []
        states = []
        drives = []

        n_steps = int(duration / dt)

        for _ in range(n_steps):
            # Get neural drive
            drive = self.get_current_neural_drive()

            # Step model
            state = self.step_coupled_model(dt=dt, use_bci_drive=True)

            # Record
            times.append(self.model_time)
            states.append(state)
            drives.append(drive)

        return times, states, drives

    def reset_model_state(
        self,
        initial_state: Optional[Tuple[float, float, float, float]] = None,
    ) -> None:
        """Reset the coupling model to initial conditions.

        Parameters
        ----------
        initial_state : tuple, optional
            Initial (v, w, x, y); if None, uses default
        """
        if initial_state is None:
            initial_state = (0.0, 0.0, 1.0, 0.0)

        self.model_state = initial_state
        self.model_time = 0.0
        self.coupling_model.reset_history()
        self.neural_drive_history.clear()

        print("Model state reset")

    def close(self) -> None:
        """Close all connections."""
        self.stop()
        self.bci.close()
        print("Bridge closed")
