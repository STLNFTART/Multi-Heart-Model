"""
BCI Data Adapter Base Classes

Provides standardized interfaces for integrating external BCI repositories
with the Multi-Heart-Model framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import numpy as np
from datetime import datetime
import threading
import queue


class SignalType(Enum):
    """Types of physiological signals."""
    EEG = "eeg"
    ECG = "ecg"
    EMG = "emg"
    EOG = "eog"
    RESP = "resp"
    PPG = "ppg"
    MIXED = "mixed"


@dataclass
class BCIDataPacket:
    """
    Standardized data packet for BCI signals.

    Attributes:
        timestamp: UTC timestamp of acquisition
        signal_type: Type of physiological signal
        channels: Channel names/IDs
        data: NumPy array of shape (n_channels, n_samples)
        sampling_rate: Sampling frequency in Hz
        metadata: Additional information (device info, quality metrics, etc.)
    """
    timestamp: float
    signal_type: SignalType
    channels: List[str]
    data: np.ndarray
    sampling_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate data dimensions."""
        if self.data.ndim != 2:
            raise ValueError(f"Data must be 2D (channels, samples), got {self.data.ndim}D")
        if self.data.shape[0] != len(self.channels):
            raise ValueError(
                f"Channel count mismatch: {len(self.channels)} names "
                f"but {self.data.shape[0]} data channels"
            )

    @property
    def n_channels(self) -> int:
        """Number of channels."""
        return self.data.shape[0]

    @property
    def n_samples(self) -> int:
        """Number of samples per channel."""
        return self.data.shape[1]

    @property
    def duration(self) -> float:
        """Duration of data packet in seconds."""
        return self.n_samples / self.sampling_rate


class BCIAdapterBase(ABC):
    """
    Abstract base class for BCI hardware/software adapters.

    All BCI repository integrations should inherit from this class
    to ensure consistent interface with the HBCM system.
    """

    def __init__(self, adapter_name: str, config: Optional[Dict] = None):
        """
        Initialize BCI adapter.

        Args:
            adapter_name: Unique identifier for this adapter
            config: Configuration dictionary
        """
        self.adapter_name = adapter_name
        self.config = config or {}
        self._is_streaming = False
        self._stream_thread: Optional[threading.Thread] = None
        self._data_queue: queue.Queue = queue.Queue(maxsize=1000)
        self._callbacks: List[callable] = []

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to BCI hardware/software.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to BCI hardware/software.

        Returns:
            True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def start_stream(self) -> bool:
        """
        Start streaming data from BCI source.

        Returns:
            True if streaming started successfully, False otherwise
        """
        pass

    @abstractmethod
    def stop_stream(self) -> bool:
        """
        Stop streaming data from BCI source.

        Returns:
            True if streaming stopped successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_channel_info(self) -> Dict[str, Any]:
        """
        Get information about available channels.

        Returns:
            Dictionary with channel names, types, sampling rates, etc.
        """
        pass

    @abstractmethod
    def _acquire_data(self) -> Optional[BCIDataPacket]:
        """
        Internal method to acquire one packet of data.

        Returns:
            BCIDataPacket if data available, None otherwise
        """
        pass

    def register_callback(self, callback: callable):
        """
        Register a callback function to be called on new data.

        Args:
            callback: Function that takes BCIDataPacket as argument
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: callable):
        """Remove a registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_latest_data(self, timeout: float = 1.0) -> Optional[BCIDataPacket]:
        """
        Get the latest data packet from the queue.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            BCIDataPacket if available, None if timeout
        """
        try:
            return self._data_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _streaming_loop(self):
        """Internal loop for continuous data acquisition."""
        while self._is_streaming:
            try:
                packet = self._acquire_data()
                if packet is not None:
                    # Add to queue
                    try:
                        self._data_queue.put_nowait(packet)
                    except queue.Full:
                        # Remove oldest packet and add new one
                        try:
                            self._data_queue.get_nowait()
                            self._data_queue.put_nowait(packet)
                        except queue.Empty:
                            pass

                    # Call registered callbacks
                    for callback in self._callbacks:
                        try:
                            callback(packet)
                        except Exception as e:
                            print(f"Callback error: {e}")
            except Exception as e:
                print(f"Streaming error: {e}")
                if not self._is_streaming:
                    break

    @property
    def is_streaming(self) -> bool:
        """Check if adapter is currently streaming data."""
        return self._is_streaming

    @property
    def queue_size(self) -> int:
        """Get current number of packets in queue."""
        return self._data_queue.qsize()


@dataclass
class BCIStreamConfig:
    """Configuration for BCI data streaming."""
    buffer_duration: float = 5.0  # seconds
    chunk_duration: float = 0.1   # seconds
    channels: Optional[List[str]] = None
    sampling_rate: float = 250.0  # Hz
    signal_type: SignalType = SignalType.EEG
    enable_lsl: bool = True
    enable_file_recording: bool = False
    recording_path: Optional[str] = None


class CircularBuffer:
    """
    Circular buffer for efficient BCI data storage.

    Maintains a sliding window of recent data for processing.
    """

    def __init__(self, n_channels: int, buffer_duration: float, sampling_rate: float):
        """
        Initialize circular buffer.

        Args:
            n_channels: Number of data channels
            buffer_duration: Duration of buffer in seconds
            sampling_rate: Sampling frequency in Hz
        """
        self.n_channels = n_channels
        self.buffer_duration = buffer_duration
        self.sampling_rate = sampling_rate

        self.buffer_size = int(buffer_duration * sampling_rate)
        self.buffer = np.zeros((n_channels, self.buffer_size), dtype=np.float32)
        self.timestamps = np.zeros(self.buffer_size, dtype=np.float64)
        self.write_index = 0
        self.is_full = False
        self._lock = threading.Lock()

    def add_data(self, data: np.ndarray, timestamp: float):
        """
        Add new data to the buffer.

        Args:
            data: NumPy array of shape (n_channels, n_samples)
            timestamp: Timestamp of first sample
        """
        with self._lock:
            n_samples = data.shape[1]

            for i in range(n_samples):
                self.buffer[:, self.write_index] = data[:, i]
                self.timestamps[self.write_index] = timestamp + i / self.sampling_rate

                self.write_index = (self.write_index + 1) % self.buffer_size
                if self.write_index == 0:
                    self.is_full = True

    def get_latest(self, duration: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get the most recent data.

        Args:
            duration: Duration of data to retrieve in seconds

        Returns:
            Tuple of (data, timestamps) arrays
        """
        with self._lock:
            n_samples = min(int(duration * self.sampling_rate), self.buffer_size)

            if not self.is_full and self.write_index < n_samples:
                # Not enough data yet
                n_samples = self.write_index

            if n_samples == 0:
                return np.array([]), np.array([])

            # Get indices
            start_idx = (self.write_index - n_samples) % self.buffer_size

            if start_idx < self.write_index:
                # Contiguous slice
                data = self.buffer[:, start_idx:self.write_index].copy()
                timestamps = self.timestamps[start_idx:self.write_index].copy()
            else:
                # Wrap around
                data = np.concatenate([
                    self.buffer[:, start_idx:],
                    self.buffer[:, :self.write_index]
                ], axis=1)
                timestamps = np.concatenate([
                    self.timestamps[start_idx:],
                    self.timestamps[:self.write_index]
                ])

            return data, timestamps

    def get_all(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get all available data in buffer.

        Returns:
            Tuple of (data, timestamps) arrays
        """
        return self.get_latest(self.buffer_duration)

    def clear(self):
        """Clear the buffer."""
        with self._lock:
            self.buffer.fill(0)
            self.timestamps.fill(0)
            self.write_index = 0
            self.is_full = False


class DataQualityMetrics:
    """Calculate and track data quality metrics for BCI signals."""

    @staticmethod
    def compute_snr(signal: np.ndarray, noise_floor: float = 1e-6) -> float:
        """
        Compute signal-to-noise ratio.

        Args:
            signal: Input signal array
            noise_floor: Estimated noise floor level

        Returns:
            SNR in dB
        """
        signal_power = np.mean(signal ** 2)
        noise_power = max(noise_floor, 1e-12)  # Avoid division by zero
        snr_db = 10 * np.log10(signal_power / noise_power)
        return snr_db

    @staticmethod
    def detect_artifacts(signal: np.ndarray, threshold: float = 5.0) -> np.ndarray:
        """
        Detect artifacts using simple threshold method.

        Args:
            signal: Input signal array
            threshold: Number of standard deviations for artifact detection

        Returns:
            Boolean array marking artifact samples
        """
        z_scores = np.abs((signal - np.mean(signal)) / (np.std(signal) + 1e-12))
        artifacts = z_scores > threshold
        return artifacts

    @staticmethod
    def compute_quality_score(signal: np.ndarray) -> float:
        """
        Compute overall quality score (0-1).

        Args:
            signal: Input signal array

        Returns:
            Quality score between 0 and 1
        """
        # Check for flatline
        if np.std(signal) < 1e-6:
            return 0.0

        # Check for excessive artifacts
        artifacts = DataQualityMetrics.detect_artifacts(signal)
        artifact_ratio = np.mean(artifacts)

        if artifact_ratio > 0.3:
            return 0.0

        # Combine metrics
        snr = DataQualityMetrics.compute_snr(signal)
        snr_score = np.clip(snr / 20.0, 0, 1)  # Normalize to 0-1
        artifact_score = 1.0 - artifact_ratio

        quality = 0.6 * snr_score + 0.4 * artifact_score
        return float(quality)
