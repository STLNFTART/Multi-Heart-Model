"""Signal processing utilities for BCI neural data."""

from __future__ import annotations

import numpy as np
from typing import Tuple
from dataclasses import dataclass


@dataclass
class BandpassFilter:
    """Simple bandpass filter for neural signals.

    Parameters
    ----------
    low_freq : float
        Low cutoff frequency (Hz)
    high_freq : float
        High cutoff frequency (Hz)
    sample_rate : float
        Sampling frequency (Hz)
    order : int
        Filter order
    """

    low_freq: float
    high_freq: float
    sample_rate: float
    order: int = 4

    def apply(self, signal: np.ndarray) -> np.ndarray:
        """Apply bandpass filter to signal.

        Parameters
        ----------
        signal : np.ndarray
            Input signal

        Returns
        -------
        filtered : np.ndarray
            Bandpass filtered signal
        """
        # Simplified filter using FFT method
        # In production, would use scipy.signal.butter + filtfilt

        # FFT
        fft = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(len(signal), 1.0 / self.sample_rate)

        # Create frequency mask
        mask = (freqs >= self.low_freq) & (freqs <= self.high_freq)
        fft[~mask] = 0

        # Inverse FFT
        filtered = np.fft.irfft(fft, n=len(signal))

        return filtered


class SignalProcessor:
    """Signal processing pipeline for neural data.

    Provides:
    - Filtering (bandpass, notch)
    - Artifact removal
    - Feature extraction
    - Normalization
    """

    def __init__(self, sample_rate: float):
        """Initialize signal processor.

        Parameters
        ----------
        sample_rate : float
            Sampling frequency (Hz)
        """
        self.sample_rate = sample_rate

    def remove_dc_offset(self, signal: np.ndarray) -> np.ndarray:
        """Remove DC offset from signal.

        Parameters
        ----------
        signal : np.ndarray
            Input signal

        Returns
        -------
        centered : np.ndarray
            Zero-mean signal
        """
        return signal - np.mean(signal)

    def notch_filter(
        self,
        signal: np.ndarray,
        notch_freq: float,
        bandwidth: float = 2.0,
    ) -> np.ndarray:
        """Apply notch filter to remove line noise.

        Parameters
        ----------
        signal : np.ndarray
            Input signal
        notch_freq : float
            Frequency to remove (e.g., 50 or 60 Hz)
        bandwidth : float
            Notch bandwidth (Hz)

        Returns
        -------
        filtered : np.ndarray
            Notch-filtered signal
        """
        # FFT-based notch filter
        fft = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(len(signal), 1.0 / self.sample_rate)

        # Create notch mask
        notch_mask = np.abs(freqs - notch_freq) > bandwidth / 2
        fft[~notch_mask] = 0

        # Inverse FFT
        filtered = np.fft.irfft(fft, n=len(signal))

        return filtered

    def compute_rms(self, signal: np.ndarray) -> float:
        """Compute root-mean-square amplitude.

        Parameters
        ----------
        signal : np.ndarray
            Input signal

        Returns
        -------
        rms : float
            RMS amplitude
        """
        return np.sqrt(np.mean(signal ** 2))

    def normalize_signal(
        self,
        signal: np.ndarray,
        method: str = "zscore",
    ) -> np.ndarray:
        """Normalize signal.

        Parameters
        ----------
        signal : np.ndarray
            Input signal
        method : str
            Normalization method:
            - 'zscore': Zero mean, unit variance
            - 'minmax': Scale to [0, 1]
            - 'rms': Divide by RMS

        Returns
        -------
        normalized : np.ndarray
            Normalized signal
        """
        if method == "zscore":
            mean = np.mean(signal)
            std = np.std(signal)
            return (signal - mean) / (std + 1e-9)

        elif method == "minmax":
            min_val = np.min(signal)
            max_val = np.max(signal)
            return (signal - min_val) / (max_val - min_val + 1e-9)

        elif method == "rms":
            rms = self.compute_rms(signal)
            return signal / (rms + 1e-9)

        else:
            raise ValueError(f"Unknown normalization method: {method}")
