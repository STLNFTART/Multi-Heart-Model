"""OpenBCI hardware interface for real-time neural signal acquisition.

This module provides a standardized interface to OpenBCI hardware platforms
including Cyton, Ganglion, and WiFi Shield variants.
"""

from __future__ import annotations

import numpy as np
from collections import deque
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Deque
import time


@dataclass
class OpenBCIConfig:
    """Configuration parameters for OpenBCI data acquisition.

    Parameters
    ----------
    sample_rate : float
        Sampling frequency in Hz (default: 250 Hz for Cyton)
    num_channels : int
        Number of EEG channels (8 for Cyton, 4 for Ganglion)
    gain : int
        Amplifier gain setting (1, 2, 4, 6, 8, 12, 24)
    use_aux : bool
        Whether to read auxiliary channels (accelerometer)
    impedance_check : bool
        Enable automatic impedance checking
    notch_filter : Optional[float]
        Notch filter frequency (50 or 60 Hz for line noise)
    bandpass_low : float
        High-pass filter cutoff (Hz)
    bandpass_high : float
        Low-pass filter cutoff (Hz)
    """

    sample_rate: float = 250.0  # Hz
    num_channels: int = 8
    gain: int = 24
    use_aux: bool = True
    impedance_check: bool = False
    notch_filter: Optional[float] = 60.0  # Hz (US line frequency)
    bandpass_low: float = 0.5  # Hz
    bandpass_high: float = 50.0  # Hz


class OpenBCIInterface:
    """Interface to OpenBCI hardware for real-time neural data acquisition.

    This class provides methods to:
    - Initialize and configure OpenBCI boards
    - Stream real-time EEG data
    - Apply basic signal processing
    - Interface with the heart-brain coupling model

    Examples
    --------
    >>> config = OpenBCIConfig(sample_rate=250.0, num_channels=8)
    >>> bci = OpenBCIInterface(config=config)
    >>> bci.start_stream()
    >>> data = bci.get_latest_samples(n_samples=100)
    >>> bci.stop_stream()
    """

    def __init__(
        self,
        config: Optional[OpenBCIConfig] = None,
        port: Optional[str] = None,
        mock_mode: bool = True,  # Default to mock for testing
    ):
        """Initialize OpenBCI interface.

        Parameters
        ----------
        config : OpenBCIConfig, optional
            Hardware configuration parameters
        port : str, optional
            Serial port for board communication (e.g., '/dev/ttyUSB0')
        mock_mode : bool
            If True, generate synthetic data for testing (default: True)
        """
        self.config = config or OpenBCIConfig()
        self.port = port
        self.mock_mode = mock_mode

        # Data buffers
        self.buffer_size = int(self.config.sample_rate * 10)  # 10 seconds
        self.data_buffer: Deque[np.ndarray] = deque(maxlen=self.buffer_size)
        self.timestamp_buffer: Deque[float] = deque(maxlen=self.buffer_size)

        # Streaming state
        self.is_streaming = False
        self.sample_count = 0

        # Hardware handle (would be actual board connection)
        self.board = None

        if not mock_mode:
            self._connect_to_board()

    def _connect_to_board(self) -> None:
        """Establish connection to physical OpenBCI board.

        In production, this would use the OpenBCI Python library:
        from brainflow.board_shim import BoardShim, BrainFlowInputParams

        For now, this is a placeholder for the actual hardware interface.
        """
        if self.port is None:
            raise ValueError("Serial port must be specified for hardware mode")

        # Placeholder for actual hardware initialization
        # self.board = BoardShim(board_id, params)
        # self.board.prepare_session()
        print(f"Connected to OpenBCI board on {self.port}")

    def start_stream(self) -> None:
        """Begin streaming data from the OpenBCI board."""
        if self.is_streaming:
            print("Warning: Stream already active")
            return

        if self.mock_mode:
            print(f"Starting mock data stream at {self.config.sample_rate} Hz")
        else:
            print("Starting hardware data stream")
            # self.board.start_stream()

        self.is_streaming = True
        self.sample_count = 0

    def stop_stream(self) -> None:
        """Stop streaming data from the OpenBCI board."""
        if not self.is_streaming:
            return

        if not self.mock_mode:
            # self.board.stop_stream()
            pass

        self.is_streaming = False
        print("Data stream stopped")

    def _generate_mock_sample(self) -> np.ndarray:
        """Generate synthetic EEG-like data for testing.

        Returns
        -------
        sample : np.ndarray
            Single multi-channel sample (shape: num_channels,)
        """
        t = self.sample_count / self.config.sample_rate

        # Simulate realistic EEG with multiple frequency components
        sample = np.zeros(self.config.num_channels)

        for ch in range(self.config.num_channels):
            # Alpha rhythm (8-12 Hz)
            alpha = 20.0 * np.sin(2 * np.pi * 10.0 * t + ch * 0.5)

            # Beta rhythm (13-30 Hz)
            beta = 10.0 * np.sin(2 * np.pi * 20.0 * t + ch * 0.3)

            # Delta rhythm (0.5-4 Hz)
            delta = 30.0 * np.sin(2 * np.pi * 2.0 * t + ch * 0.1)

            # Noise
            noise = np.random.normal(0, 5.0)

            # Combine components (units: microvolts)
            sample[ch] = alpha + beta + delta + noise

        return sample

    def get_latest_sample(self) -> Optional[Tuple[float, np.ndarray]]:
        """Retrieve the most recent data sample.

        Returns
        -------
        timestamp : float
            Sample acquisition time
        data : np.ndarray
            Multi-channel data sample (shape: num_channels,)
        """
        if not self.is_streaming:
            print("Warning: Stream not active")
            return None

        if self.mock_mode:
            timestamp = time.time()
            data = self._generate_mock_sample()
            self.sample_count += 1
        else:
            # Read from actual hardware
            # data = self.board.get_current_board_data(1)
            # timestamp = data[-1]  # Last column is timestamp
            # data = data[1:self.config.num_channels+1, 0]  # EEG channels
            return None  # Placeholder

        # Store in buffer
        self.data_buffer.append(data)
        self.timestamp_buffer.append(timestamp)

        return timestamp, data

    def get_latest_samples(self, n_samples: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """Retrieve the N most recent samples.

        Parameters
        ----------
        n_samples : int
            Number of samples to retrieve

        Returns
        -------
        timestamps : np.ndarray
            Sample timestamps (shape: n_samples,)
        data : np.ndarray
            Multi-channel data (shape: n_samples, num_channels)
        """
        for _ in range(n_samples):
            self.get_latest_sample()

        if len(self.data_buffer) < n_samples:
            n_samples = len(self.data_buffer)

        timestamps = np.array(list(self.timestamp_buffer)[-n_samples:])
        data = np.array(list(self.data_buffer)[-n_samples:])

        return timestamps, data

    def get_channel_data(self, channel: int, n_samples: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """Get time series data for a specific channel.

        Parameters
        ----------
        channel : int
            Channel index (0 to num_channels-1)
        n_samples : int
            Number of samples to retrieve

        Returns
        -------
        timestamps : np.ndarray
            Sample timestamps
        channel_data : np.ndarray
            Single-channel time series
        """
        timestamps, data = self.get_latest_samples(n_samples)

        if channel >= self.config.num_channels:
            raise ValueError(f"Channel {channel} out of range (0-{self.config.num_channels-1})")

        return timestamps, data[:, channel]

    def compute_band_power(
        self,
        channel: int,
        freq_band: Tuple[float, float],
        n_samples: int = 250,
    ) -> float:
        """Compute spectral power in a frequency band.

        Parameters
        ----------
        channel : int
            Channel index
        freq_band : tuple
            (low_freq, high_freq) in Hz
        n_samples : int
            Number of samples for FFT

        Returns
        -------
        power : float
            Band power in microvolts^2
        """
        timestamps, data = self.get_channel_data(channel, n_samples)

        # Compute FFT
        fft = np.fft.rfft(data)
        freqs = np.fft.rfftfreq(len(data), 1.0 / self.config.sample_rate)
        power_spectrum = np.abs(fft) ** 2

        # Extract band power
        low_freq, high_freq = freq_band
        band_mask = (freqs >= low_freq) & (freqs <= high_freq)
        band_power = np.sum(power_spectrum[band_mask])

        return band_power

    def get_alpha_power(self, channel: int = 0) -> float:
        """Get alpha band (8-12 Hz) power for a channel."""
        return self.compute_band_power(channel, (8.0, 12.0))

    def get_beta_power(self, channel: int = 0) -> float:
        """Get beta band (13-30 Hz) power for a channel."""
        return self.compute_band_power(channel, (13.0, 30.0))

    def get_theta_power(self, channel: int = 0) -> float:
        """Get theta band (4-8 Hz) power for a channel."""
        return self.compute_band_power(channel, (4.0, 8.0))

    def get_delta_power(self, channel: int = 0) -> float:
        """Get delta band (0.5-4 Hz) power for a channel."""
        return self.compute_band_power(channel, (0.5, 4.0))

    def compute_neural_drive(
        self,
        channel: int = 0,
        method: str = "alpha_beta_ratio",
    ) -> float:
        """Compute a scalar neural drive signal for coupling to the heart model.

        This extracts a physiologically meaningful signal from EEG that can
        modulate the cardiac oscillator in the heart-brain coupling model.

        Parameters
        ----------
        channel : int
            EEG channel to use
        method : str
            Method for computing drive signal:
            - 'alpha_beta_ratio': alpha / (alpha + beta) power
            - 'alpha_power': raw alpha band power
            - 'raw': raw EEG amplitude

        Returns
        -------
        drive : float
            Neural drive signal (normalized to approximately 0-1)
        """
        if method == "alpha_beta_ratio":
            alpha = self.get_alpha_power(channel)
            beta = self.get_beta_power(channel)
            # Ratio indicates relaxation vs. arousal
            drive = alpha / (alpha + beta + 1e-6)

        elif method == "alpha_power":
            # Alpha power as direct measure of cortical idling
            alpha = self.get_alpha_power(channel)
            # Normalize (typical range 0-10000 uV^2)
            drive = np.clip(alpha / 10000.0, 0.0, 1.0)

        elif method == "raw":
            # Use raw EEG amplitude
            _, data = self.get_channel_data(channel, n_samples=10)
            drive = np.mean(data) / 100.0  # Normalize to ~0-1

        else:
            raise ValueError(f"Unknown method: {method}")

        return drive

    def close(self) -> None:
        """Close the connection to the OpenBCI board."""
        self.stop_stream()

        if not self.mock_mode and self.board is not None:
            # self.board.release_session()
            print("Board connection closed")
