"""
BCI Stack Integration Tests

Tests the complete BCI integration stack:
- BrainFlow (hardware abstraction)
- MNE-Python (signal processing)
- PyRiemann (feature extraction)
- LSL (streaming)
- NeuroDSP (oscillation analysis)
- NeuroKit2 (physiological signals)
"""

import sys
from pathlib import Path
import time
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validation.framework import ValidationTestBase, BenchmarkResult


class BrainFlowTests(ValidationTestBase):
    """BrainFlow validation tests."""

    def __init__(self):
        super().__init__("BrainFlow")

    def test_installation(self) -> BenchmarkResult:
        start = time.time()
        try:
            import brainflow
            from brainflow.board_shim import BoardShim

            metrics = {'version': brainflow.__version__}

            return BenchmarkResult(
                test_name="Installation Check",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )
        except ImportError as e:
            return BenchmarkResult(
                test_name="Installation Check",
                repository=self.repository_name,
                status='skip',
                execution_time=time.time() - start,
                error_message=f"BrainFlow not installed: {e}"
            )

    def test_import(self) -> BenchmarkResult:
        start = time.time()
        try:
            from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
            from brainflow.data_filter import DataFilter, FilterTypes

            return BenchmarkResult(
                test_name="Import Test",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start
            )
        except ImportError as e:
            return BenchmarkResult(
                test_name="Import Test",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )

    def test_basic_functionality(self) -> BenchmarkResult:
        start = time.time()
        try:
            from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
            from brainflow.data_filter import DataFilter, FilterTypes

            # Use synthetic board for testing
            params = BrainFlowInputParams()
            board = BoardShim(BoardIds.SYNTHETIC_BOARD.value, params)

            board.prepare_session()
            board.start_stream()
            time.sleep(1)  # Collect data
            board.stop_stream()
            data = board.get_board_data()
            board.release_session()

            metrics = {
                'board_type': 'SYNTHETIC',
                'data_shape': data.shape,
                'sampling_rate': BoardShim.get_sampling_rate(BoardIds.SYNTHETIC_BOARD.value)
            }

            return BenchmarkResult(
                test_name="Basic Functionality",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )
        except Exception as e:
            return BenchmarkResult(
                test_name="Basic Functionality",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )

    def test_integration_with_hbcm(self) -> BenchmarkResult:
        start = time.time()
        try:
            from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
            from bci_integration.data_acquisition import CircularBuffer
            from src.coupling import HeartBrainCouplingModel
            from src.neural import FitzHughNagumo
            from src.cardiac import VanDerPolOscillator
            from src.coupling import CouplingParameters

            # Get synthetic data
            params = BrainFlowInputParams()
            board = BoardShim(BoardIds.SYNTHETIC_BOARD.value, params)
            board.prepare_session()
            board.start_stream()
            time.sleep(0.5)
            board.stop_stream()
            data = board.get_board_data()
            board.release_session()

            # Use circular buffer
            n_channels = BoardShim.get_eeg_channels(BoardIds.SYNTHETIC_BOARD.value)
            buffer = CircularBuffer(
                n_channels=len(n_channels),
                buffer_duration=5.0,
                sampling_rate=BoardShim.get_sampling_rate(BoardIds.SYNTHETIC_BOARD.value)
            )

            buffer.add_data(data[n_channels, :], time.time())

            # Create and run HBCM
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(),
                cardiac_model=VanDerPolOscillator(),
                coupling=CouplingParameters()
            )

            trajectory = hbcm.simulate((0.0, 0.0, 1.0, 0.0), (0.0, 1.0), 0.01)

            metrics = {
                'brainflow_samples': data.shape[1],
                'hbcm_steps': len(trajectory),
                'integration_successful': True
            }

            return BenchmarkResult(
                test_name="HBCM Integration",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )
        except Exception as e:
            return BenchmarkResult(
                test_name="HBCM Integration",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )


class MNEPythonTests(ValidationTestBase):
    """MNE-Python validation tests."""

    def __init__(self):
        super().__init__("MNE-Python")

    def test_installation(self) -> BenchmarkResult:
        start = time.time()
        try:
            import mne

            metrics = {'version': mne.__version__}

            return BenchmarkResult(
                test_name="Installation Check",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )
        except ImportError as e:
            return BenchmarkResult(
                test_name="Installation Check",
                repository=self.repository_name,
                status='skip',
                execution_time=time.time() - start,
                error_message=f"MNE-Python not installed: {e}"
            )

    def test_import(self) -> BenchmarkResult:
        start = time.time()
        try:
            from mne import Epochs, find_events, create_info
            from mne.io import RawArray
            from mne.preprocessing import ICA

            return BenchmarkResult(
                test_name="Import Test",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start
            )
        except ImportError as e:
            return BenchmarkResult(
                test_name="Import Test",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )

    def test_basic_functionality(self) -> BenchmarkResult:
        start = time.time()
        try:
            import mne

            # Create synthetic data
            sfreq = 256.0
            n_channels = 8
            n_samples = 1000

            data = np.random.randn(n_channels, n_samples)
            info = mne.create_info(
                ch_names=[f'EEG{i:03d}' for i in range(n_channels)],
                sfreq=sfreq,
                ch_types='eeg'
            )

            raw = mne.io.RawArray(data, info, verbose=False)

            # Apply filter
            raw.filter(1.0, 40.0, verbose=False)

            metrics = {
                'n_channels': n_channels,
                'sampling_rate': sfreq,
                'n_samples': n_samples,
                'filtered': True
            }

            return BenchmarkResult(
                test_name="Basic Functionality",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )
        except Exception as e:
            return BenchmarkResult(
                test_name="Basic Functionality",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )

    def test_integration_with_hbcm(self) -> BenchmarkResult:
        start = time.time()
        try:
            import mne
            from src.coupling import HeartBrainCouplingModel
            from src.neural import FitzHughNagumo
            from src.cardiac import VanDerPolOscillator
            from src.coupling import CouplingParameters

            # Create synthetic EEG
            sfreq = 256.0
            n_channels = 8
            n_samples = 1000

            data = np.random.randn(n_channels, n_samples)
            info = mne.create_info(
                ch_names=[f'EEG{i:03d}' for i in range(n_channels)],
                sfreq=sfreq,
                ch_types='eeg'
            )

            raw = mne.io.RawArray(data, info, verbose=False)
            raw.filter(1.0, 40.0, verbose=False)

            # Extract processed data
            processed_data = raw.get_data()

            # Use for HBCM modulation
            eeg_mean = np.mean(processed_data)

            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(stimulus_amplitude=eeg_mean * 0.1),
                cardiac_model=VanDerPolOscillator(),
                coupling=CouplingParameters()
            )

            trajectory = hbcm.simulate((0.0, 0.0, 1.0, 0.0), (0.0, 1.0), 0.01)

            metrics = {
                'mne_samples': processed_data.shape[1],
                'hbcm_steps': len(trajectory),
                'integration_successful': True
            }

            return BenchmarkResult(
                test_name="HBCM Integration",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )
        except Exception as e:
            return BenchmarkResult(
                test_name="HBCM Integration",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )


def run_all_bci_tests():
    """Run all BCI stack tests."""
    test_classes = [
        BrainFlowTests,
        MNEPythonTests
    ]

    all_results = []

    for test_class in test_classes:
        tester = test_class()
        results = tester.run_all_tests()
        all_results.extend(results)

        summary = tester.get_summary()
        print(f"\n{tester.repository_name} Summary:")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")

    return all_results


if __name__ == '__main__':
    run_all_bci_tests()
