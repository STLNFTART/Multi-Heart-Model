"""Neuralink-style high-bandwidth neural interface adapter.

This module provides an interface compatible with high-density neural recording
systems like Neuralink, Utah arrays, and other invasive BCIs with 100+ channels.
"""

from __future__ import annotations

import numpy as np
from collections import deque
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Deque
import time


@dataclass
class NeuralinkConfig:
    """Configuration for high-bandwidth neural interface.

    Parameters
    ----------
    sample_rate : float
        Sampling frequency (typical: 20-30 kHz for spike detection)
    num_channels : int
        Number of recording electrodes (e.g., 1024 for Neuralink N1)
    spike_threshold : float
        Threshold for spike detection (in standard deviations)
    spike_window_ms : float
        Time window for spike waveform extraction (milliseconds)
    neural_decode_method : str
        Method for decoding neural activity:
        - 'spike_rate': Firing rate estimation
        - 'lfp': Local field potential analysis
        - 'multiunit': Multi-unit activity
    target_brain_region : str
        Brain region being recorded (for interpretation)
    """

    sample_rate: float = 20000.0  # Hz (20 kHz)
    num_channels: int = 1024  # Neuralink N1 electrode count
    spike_threshold: float = 4.0  # Standard deviations
    spike_window_ms: float = 2.0  # milliseconds
    neural_decode_method: str = "spike_rate"
    target_brain_region: str = "motor_cortex"


@dataclass
class SpikeEvent:
    """Represents a detected action potential spike.

    Attributes
    ----------
    timestamp : float
        Time of spike occurrence (seconds)
    channel : int
        Recording channel index
    amplitude : float
        Peak spike amplitude (microvolts)
    waveform : np.ndarray
        Spike waveform snippet
    """

    timestamp: float
    channel: int
    amplitude: float
    waveform: np.ndarray


class NeuralinkAdapter:
    """Interface to Neuralink-style high-bandwidth neural recording systems.

    This adapter provides:
    - High-frequency multi-channel neural data acquisition
    - Real-time spike detection and sorting
    - Local field potential (LFP) extraction
    - Population neural decoding for heart-brain coupling

    Examples
    --------
    >>> config = NeuralinkConfig(sample_rate=20000, num_channels=1024)
    >>> neuralink = NeuralinkAdapter(config=config)
    >>> neuralink.start_recording()
    >>> firing_rate = neuralink.get_population_firing_rate()
    >>> lfp_power = neuralink.get_lfp_band_power(4.0, 8.0)  # Theta band
    """

    def __init__(
        self,
        config: Optional[NeuralinkConfig] = None,
        mock_mode: bool = True,  # Default to mock for testing
    ):
        """Initialize Neuralink adapter.

        Parameters
        ----------
        config : NeuralinkConfig, optional
            Hardware configuration
        mock_mode : bool
            Generate synthetic data for testing
        """
        self.config = config or NeuralinkConfig()
        self.mock_mode = mock_mode

        # Spike detection buffers
        self.spike_buffer: List[SpikeEvent] = []
        self.spike_buffer_max_size = 100000  # Store last 100k spikes

        # LFP data buffer (downsampled to 1 kHz)
        self.lfp_sample_rate = 1000.0  # Hz
        self.lfp_downsample_factor = int(self.config.sample_rate / self.lfp_sample_rate)
        self.lfp_buffer: Deque[np.ndarray] = deque(maxlen=10000)  # 10 sec at 1 kHz

        # Population statistics
        self.channel_firing_rates: np.ndarray = np.zeros(self.config.num_channels)
        self.last_rate_update: float = 0.0

        # Recording state
        self.is_recording = False
        self.sample_count = 0
        self.start_time = 0.0

        # Hardware interface
        self.device = None

        if not mock_mode:
            self._connect_to_device()

    def _connect_to_device(self) -> None:
        """Connect to Neuralink hardware.

        In production, this would interface with the actual Neuralink API.
        For now, this is a placeholder.
        """
        print("Connecting to Neuralink device...")
        # self.device = NeuralinkDevice()
        # self.device.initialize()
        print("Connected to Neuralink implant")

    def start_recording(self) -> None:
        """Begin high-bandwidth neural recording."""
        if self.is_recording:
            print("Warning: Recording already active")
            return

        self.is_recording = True
        self.start_time = time.time()
        self.sample_count = 0

        if self.mock_mode:
            print(f"Starting mock neural recording at {self.config.sample_rate} Hz")
        else:
            print("Starting Neuralink recording")
            # self.device.start_stream()

    def stop_recording(self) -> None:
        """Stop neural recording."""
        if not self.is_recording:
            return

        self.is_recording = False

        if not self.mock_mode:
            # self.device.stop_stream()
            pass

        print("Recording stopped")

    def _generate_mock_spike_train(self, channel: int, duration_samples: int) -> np.ndarray:
        """Generate synthetic spike train with realistic statistics.

        Parameters
        ----------
        channel : int
            Channel index
        duration_samples : int
            Number of samples to generate

        Returns
        -------
        signal : np.ndarray
            Simulated neural signal with spikes and noise
        """
        signal = np.random.normal(0, 10.0, duration_samples)  # Baseline noise (microvolts)

        # Base firing rate varies by channel (realistic range: 1-50 Hz)
        base_rate = 5.0 + (channel % 40)  # Hz
        # Modulate with slow oscillation (to simulate attention, arousal, etc.)
        t = (self.sample_count + np.arange(duration_samples)) / self.config.sample_rate
        modulation = 1.0 + 0.5 * np.sin(2 * np.pi * 0.1 * t)  # 0.1 Hz modulation
        instantaneous_rate = base_rate * modulation

        # Generate Poisson spike times
        dt = 1.0 / self.config.sample_rate
        spike_prob = instantaneous_rate * dt
        spike_times = np.random.random(duration_samples) < spike_prob

        # Add spike waveforms
        spike_template = self._generate_spike_template()
        for i in np.where(spike_times)[0]:
            # Add spike waveform (with some jitter in amplitude)
            amplitude = 100.0 + np.random.normal(0, 20.0)  # microvolts
            spike_len = len(spike_template)
            if i + spike_len < duration_samples:
                signal[i:i+spike_len] += amplitude * spike_template

        return signal

    def _generate_spike_template(self) -> np.ndarray:
        """Generate a realistic action potential waveform template."""
        duration_samples = int(self.config.spike_window_ms * self.config.sample_rate / 1000.0)
        t = np.linspace(0, self.config.spike_window_ms, duration_samples)

        # Biphasic spike shape (simplified Hodgkin-Huxley-like)
        spike = -np.exp(-t / 0.3) * np.sin(2 * np.pi * t / 1.0)

        # Normalize
        spike = spike / np.max(np.abs(spike))

        return spike

    def _detect_spikes(self, signal: np.ndarray, channel: int) -> List[SpikeEvent]:
        """Detect action potential spikes in a signal segment.

        Parameters
        ----------
        signal : np.ndarray
            Raw neural signal
        channel : int
            Channel index

        Returns
        -------
        spikes : List[SpikeEvent]
            Detected spikes
        """
        # Compute threshold (median absolute deviation method)
        mad = np.median(np.abs(signal - np.median(signal)))
        threshold = self.config.spike_threshold * mad / 0.6745

        spikes = []
        spike_window_samples = int(
            self.config.spike_window_ms * self.config.sample_rate / 1000.0
        )

        # Find threshold crossings
        crossings = np.where((signal[:-1] < -threshold) & (signal[1:] >= -threshold))[0]

        for cross_idx in crossings:
            # Extract spike waveform
            start = max(0, cross_idx - spike_window_samples // 2)
            end = min(len(signal), cross_idx + spike_window_samples // 2)
            waveform = signal[start:end]

            # Peak amplitude
            amplitude = np.min(waveform)  # Negative peak

            # Timestamp
            timestamp = self.start_time + (self.sample_count + cross_idx) / self.config.sample_rate

            spike = SpikeEvent(
                timestamp=timestamp,
                channel=channel,
                amplitude=amplitude,
                waveform=waveform,
            )
            spikes.append(spike)

        return spikes

    def acquire_batch(self, batch_size_ms: float = 10.0) -> None:
        """Acquire and process a batch of neural data.

        Parameters
        ----------
        batch_size_ms : float
            Duration of data batch in milliseconds
        """
        if not self.is_recording:
            return

        batch_samples = int(batch_size_ms * self.config.sample_rate / 1000.0)

        if self.mock_mode:
            # Generate mock data for subset of channels (to save computation)
            # In production, would read from all channels
            n_active_channels = min(64, self.config.num_channels)

            for ch in range(n_active_channels):
                signal = self._generate_mock_spike_train(ch, batch_samples)

                # Detect spikes
                spikes = self._detect_spikes(signal, ch)
                self.spike_buffer.extend(spikes)

                # Downsample for LFP (every Nth sample)
                lfp_signal = signal[::self.lfp_downsample_factor]
                self.lfp_buffer.append(lfp_signal)

            # Trim spike buffer if too large
            if len(self.spike_buffer) > self.spike_buffer_max_size:
                self.spike_buffer = self.spike_buffer[-self.spike_buffer_max_size:]

        else:
            # Read from actual hardware
            # data = self.device.read_batch(batch_samples)
            # Process each channel...
            pass

        self.sample_count += batch_samples

    def get_population_firing_rate(
        self,
        time_window_sec: float = 1.0,
        region_channels: Optional[List[int]] = None,
    ) -> float:
        """Compute population firing rate across channels.

        Parameters
        ----------
        time_window_sec : float
            Time window for rate estimation (seconds)
        region_channels : List[int], optional
            Specific channels to analyze (if None, use all)

        Returns
        -------
        firing_rate : float
            Population-averaged firing rate (spikes/second)
        """
        current_time = time.time()
        window_start = current_time - time_window_sec

        # Filter spikes in time window
        recent_spikes = [
            s for s in self.spike_buffer
            if s.timestamp >= window_start
        ]

        if region_channels is not None:
            recent_spikes = [s for s in recent_spikes if s.channel in region_channels]

        # Compute rate
        n_channels = len(region_channels) if region_channels else self.config.num_channels
        total_spikes = len(recent_spikes)
        firing_rate = total_spikes / (time_window_sec * n_channels)

        return firing_rate

    def get_lfp_band_power(
        self,
        low_freq: float,
        high_freq: float,
        channel: int = 0,
    ) -> float:
        """Compute LFP power in a frequency band.

        Parameters
        ----------
        low_freq : float
            Lower frequency bound (Hz)
        high_freq : float
            Upper frequency bound (Hz)
        channel : int
            LFP channel index

        Returns
        -------
        power : float
            Band power
        """
        if len(self.lfp_buffer) == 0:
            return 0.0

        # Get LFP data
        lfp_data = np.array(list(self.lfp_buffer))
        if lfp_data.ndim == 2:
            # Extract specific channel if multi-channel
            if channel < lfp_data.shape[1]:
                lfp_data = lfp_data[:, channel]
            else:
                lfp_data = lfp_data[:, 0]

        # Compute FFT
        fft = np.fft.rfft(lfp_data.flatten())
        freqs = np.fft.rfftfreq(len(lfp_data.flatten()), 1.0 / self.lfp_sample_rate)
        power_spectrum = np.abs(fft) ** 2

        # Extract band
        band_mask = (freqs >= low_freq) & (freqs <= high_freq)
        band_power = np.sum(power_spectrum[band_mask])

        return band_power

    def compute_neural_drive_signal(
        self,
        method: str = "firing_rate",
        region_channels: Optional[List[int]] = None,
    ) -> float:
        """Compute neural drive signal for heart-brain coupling.

        This extracts a scalar control signal from population neural activity
        that can modulate the cardiac oscillator.

        Parameters
        ----------
        method : str
            Method for computing drive:
            - 'firing_rate': Population firing rate
            - 'theta_power': LFP theta band (4-8 Hz) power
            - 'beta_power': LFP beta band (13-30 Hz) power
            - 'gamma_power': LFP gamma band (30-100 Hz) power
        region_channels : List[int], optional
            Specific channels for region-specific analysis

        Returns
        -------
        drive : float
            Neural drive signal (normalized approximately 0-1)
        """
        # Acquire latest batch
        self.acquire_batch(batch_size_ms=10.0)

        if method == "firing_rate":
            # Use population firing rate
            rate = self.get_population_firing_rate(
                time_window_sec=0.5,
                region_channels=region_channels,
            )
            # Normalize (typical range: 0-50 Hz)
            drive = np.clip(rate / 50.0, 0.0, 1.0)

        elif method == "theta_power":
            # Theta band LFP power (associated with arousal, memory)
            power = self.get_lfp_band_power(4.0, 8.0)
            drive = np.clip(power / 1000.0, 0.0, 1.0)  # Normalize

        elif method == "beta_power":
            # Beta band (motor preparation, attention)
            power = self.get_lfp_band_power(13.0, 30.0)
            drive = np.clip(power / 1000.0, 0.0, 1.0)

        elif method == "gamma_power":
            # Gamma band (high-frequency synchronization)
            power = self.get_lfp_band_power(30.0, 100.0)
            drive = np.clip(power / 1000.0, 0.0, 1.0)

        else:
            raise ValueError(f"Unknown method: {method}")

        return drive

    def get_spike_statistics(self) -> Dict[str, float]:
        """Compute summary statistics of recent spiking activity.

        Returns
        -------
        stats : dict
            Dictionary with keys:
            - 'total_spikes': Total spike count
            - 'mean_firing_rate': Average rate across channels
            - 'cv_isi': Coefficient of variation of inter-spike intervals
        """
        if len(self.spike_buffer) == 0:
            return {
                'total_spikes': 0,
                'mean_firing_rate': 0.0,
                'cv_isi': 0.0,
            }

        total_spikes = len(self.spike_buffer)
        mean_rate = self.get_population_firing_rate(time_window_sec=1.0)

        # Compute ISI CV (measure of spike regularity)
        spike_times = [s.timestamp for s in self.spike_buffer[-1000:]]  # Last 1000 spikes
        if len(spike_times) > 1:
            isis = np.diff(sorted(spike_times))
            cv_isi = np.std(isis) / (np.mean(isis) + 1e-9)
        else:
            cv_isi = 0.0

        return {
            'total_spikes': total_spikes,
            'mean_firing_rate': mean_rate,
            'cv_isi': cv_isi,
        }

    def close(self) -> None:
        """Close connection to Neuralink device."""
        self.stop_recording()

        if not self.mock_mode and self.device is not None:
            # self.device.shutdown()
            print("Neuralink device connection closed")
