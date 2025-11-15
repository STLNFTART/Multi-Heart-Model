"""
Synthetic BCI Data Adapter

Generates synthetic EEG/ECG data for testing and development without hardware.
"""

from typing import Dict, Optional, Any
import numpy as np
import time
import threading
from .bci_adapter_base import BCIAdapterBase, BCIDataPacket, SignalType


class SyntheticAdapter(BCIAdapterBase):
    """
    Generates synthetic physiological signals for testing.

    Produces realistic-looking EEG/ECG waveforms with configurable properties.
    """

    def __init__(self, n_channels: int = 8, sampling_rate: float = 250.0,
                 signal_type: str = "eeg", config: Optional[Dict] = None):
        """
        Initialize synthetic adapter.

        Args:
            n_channels: Number of channels to generate
            sampling_rate: Sampling rate in Hz
            signal_type: Type of signal ('eeg', 'ecg', 'mixed')
            config: Additional configuration
        """
        super().__init__(f"Synthetic_{signal_type.upper()}", config)

        self.n_channels = n_channels
        self.sampling_rate = sampling_rate
        self.signal_type_str = signal_type.lower()

        # Map string to enum
        if signal_type.upper() in SignalType.__members__:
            self.signal_type = SignalType[signal_type.upper()]
        else:
            self.signal_type = SignalType.EEG

        self.channel_names = [f"{signal_type.upper()}{i+1}" for i in range(n_channels)]

        # Signal generation parameters
        self.phase = np.random.rand(n_channels) * 2 * np.pi
        self.frequencies = np.random.uniform(0.5, 40.0, n_channels)  # Hz
        self.amplitudes = np.random.uniform(10.0, 100.0, n_channels)  # microvolts

        # Noise parameters
        self.noise_level = 5.0  # microvolts

        # Timing
        self.start_time = None
        self.sample_count = 0
        self.chunk_size = int(sampling_rate * 0.04)  # 40ms chunks

    def connect(self) -> bool:
        """Initialize synthetic data generator."""
        self.start_time = time.time()
        self.sample_count = 0
        print(f"Synthetic {self.signal_type_str.upper()} adapter initialized: "
              f"{self.n_channels} channels @ {self.sampling_rate} Hz")
        return True

    def disconnect(self) -> bool:
        """Stop synthetic data generation."""
        if self._is_streaming:
            self.stop_stream()
        print("Synthetic adapter disconnected")
        return True

    def start_stream(self) -> bool:
        """Start generating synthetic data."""
        if self.start_time is None:
            self.connect()

        self._is_streaming = True

        # Start streaming thread
        self._stream_thread = threading.Thread(target=self._streaming_loop, daemon=True)
        self._stream_thread.start()

        print("Synthetic data streaming started")
        return True

    def stop_stream(self) -> bool:
        """Stop generating synthetic data."""
        self._is_streaming = False

        if self._stream_thread is not None:
            self._stream_thread.join(timeout=2.0)
            self._stream_thread = None

        print("Synthetic data streaming stopped")
        return True

    def _acquire_data(self) -> Optional[BCIDataPacket]:
        """Generate one chunk of synthetic data."""
        if self.start_time is None:
            return None

        # Generate time points
        t_start = self.sample_count / self.sampling_rate
        t_end = (self.sample_count + self.chunk_size) / self.sampling_rate
        t = np.linspace(t_start, t_end, self.chunk_size, endpoint=False)

        # Generate signals based on type
        if self.signal_type_str == "eeg":
            data = self._generate_eeg(t)
        elif self.signal_type_str == "ecg":
            data = self._generate_ecg(t)
        else:
            data = self._generate_mixed(t)

        # Add noise
        noise = np.random.randn(self.n_channels, self.chunk_size) * self.noise_level
        data += noise

        # Update counters
        self.sample_count += self.chunk_size
        timestamp = time.time()

        # Create packet
        packet = BCIDataPacket(
            timestamp=timestamp,
            signal_type=self.signal_type,
            channels=self.channel_names,
            data=data.astype(np.float32),
            sampling_rate=self.sampling_rate,
            metadata={
                'synthetic': True,
                'signal_type': self.signal_type_str,
                'chunk_size': self.chunk_size
            }
        )

        # Small delay to match real-time
        time.sleep(self.chunk_size / self.sampling_rate * 0.8)

        return packet

    def _generate_eeg(self, t: np.ndarray) -> np.ndarray:
        """
        Generate synthetic EEG signals.

        Combines multiple frequency bands (delta, theta, alpha, beta, gamma).
        """
        data = np.zeros((self.n_channels, len(t)))

        # Frequency bands with typical amplitudes
        bands = {
            'delta': (0.5, 4.0, 50.0),    # 0.5-4 Hz, 50 μV
            'theta': (4.0, 8.0, 30.0),    # 4-8 Hz, 30 μV
            'alpha': (8.0, 13.0, 50.0),   # 8-13 Hz, 50 μV (dominant when relaxed)
            'beta': (13.0, 30.0, 20.0),   # 13-30 Hz, 20 μV
            'gamma': (30.0, 100.0, 10.0)  # 30-100 Hz, 10 μV
        }

        for ch in range(self.n_channels):
            signal = np.zeros_like(t)

            for band, (f_low, f_high, amp) in bands.items():
                # Random frequency within band
                f = np.random.uniform(f_low, f_high)
                # Random phase
                phase = np.random.rand() * 2 * np.pi
                # Add component
                signal += amp * np.sin(2 * np.pi * f * t + phase)

            # Add spontaneous "spikes" occasionally
            if np.random.rand() < 0.01:  # 1% chance per chunk
                spike_idx = np.random.randint(0, len(t))
                spike_width = int(0.05 * self.sampling_rate)  # 50ms
                spike_amp = np.random.uniform(100, 200)

                # Gaussian spike
                for i in range(max(0, spike_idx - spike_width), min(len(t), spike_idx + spike_width)):
                    signal[i] += spike_amp * np.exp(-((i - spike_idx) ** 2) / (2 * (spike_width / 4) ** 2))

            data[ch] = signal

        return data

    def _generate_ecg(self, t: np.ndarray) -> np.ndarray:
        """
        Generate synthetic ECG signals.

        Simulates QRS complexes with realistic morphology.
        """
        data = np.zeros((self.n_channels, len(t)))

        # Heart rate: 60-100 bpm
        heart_rate = 75  # bpm
        rr_interval = 60.0 / heart_rate  # seconds

        for ch in range(self.n_channels):
            signal = np.zeros_like(t)

            # Find R-peak locations
            current_time = t[0]
            last_r_peak = current_time - (current_time % rr_interval)

            while last_r_peak < t[-1]:
                r_time = last_r_peak + rr_interval

                if t[0] <= r_time <= t[-1]:
                    # Find index
                    r_idx = np.argmin(np.abs(t - r_time))

                    # Generate QRS complex
                    # P wave (before QRS)
                    p_time = r_time - 0.16
                    if t[0] <= p_time <= t[-1]:
                        p_idx = np.argmin(np.abs(t - p_time))
                        signal += self._gaussian_wave(t, p_time, 0.08, 0.15)

                    # Q wave
                    signal += self._gaussian_wave(t, r_time - 0.02, 0.01, -0.2)

                    # R wave (dominant)
                    signal += self._gaussian_wave(t, r_time, 0.02, 1.5)

                    # S wave
                    signal += self._gaussian_wave(t, r_time + 0.02, 0.01, -0.3)

                    # T wave (after QRS)
                    t_time = r_time + 0.25
                    if t[0] <= t_time <= t[-1]:
                        signal += self._gaussian_wave(t, t_time, 0.12, 0.3)

                last_r_peak += rr_interval

            # Baseline wander (low frequency drift)
            baseline = 0.05 * np.sin(2 * np.pi * 0.3 * t + self.phase[ch])

            data[ch] = (signal + baseline) * 500  # Scale to microvolts

        return data

    def _gaussian_wave(self, t: np.ndarray, center: float, width: float, amplitude: float) -> np.ndarray:
        """Generate Gaussian wave component."""
        return amplitude * np.exp(-((t - center) ** 2) / (2 * width ** 2))

    def _generate_mixed(self, t: np.ndarray) -> np.ndarray:
        """Generate mixed EEG and ECG signals."""
        data = np.zeros((self.n_channels, len(t)))

        # Half EEG, half ECG
        n_eeg = self.n_channels // 2
        data[:n_eeg] = self._generate_eeg(t)[:n_eeg]
        data[n_eeg:] = self._generate_ecg(t)[:self.n_channels - n_eeg]

        return data

    def get_channel_info(self) -> Dict[str, Any]:
        """Get channel information."""
        return {
            'adapter_type': 'synthetic',
            'n_channels': self.n_channels,
            'channel_names': self.channel_names,
            'sampling_rate': self.sampling_rate,
            'signal_type': self.signal_type_str,
            'units': 'microvolts',
            'synthetic': True
        }

    def set_noise_level(self, noise_level: float):
        """Set noise level in microvolts."""
        self.noise_level = noise_level

    def set_frequencies(self, frequencies: np.ndarray):
        """Set base frequencies for each channel."""
        if len(frequencies) == self.n_channels:
            self.frequencies = frequencies

    def set_amplitudes(self, amplitudes: np.ndarray):
        """Set amplitudes for each channel."""
        if len(amplitudes) == self.n_channels:
            self.amplitudes = amplitudes
