"""
EEGNet Deep Learning Model Integration Tests

Tests Multi-Heart-Model against EEGNet CNN-based BCI classification.

Repository: https://github.com/vlawhern/arl-eegmodels
"""

import sys
from pathlib import Path
import time
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validation.framework import ValidationTestBase, BenchmarkResult, PerformanceBenchmark


class EEGNetValidationTests(ValidationTestBase):
    """Validation tests for EEGNet integration."""

    def __init__(self):
        super().__init__("EEGNet")

    def test_installation(self) -> BenchmarkResult:
        """Test if TensorFlow/Keras is installed for EEGNet."""
        start = time.time()

        try:
            import tensorflow as tf
            from tensorflow import keras

            metrics = {
                'tensorflow_version': tf.__version__,
                'keras_version': keras.__version__,
                'gpu_available': len(tf.config.list_physical_devices('GPU')) > 0
            }

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
                error_message=f"TensorFlow not installed: {e}. Install with: pip install tensorflow"
            )

    def test_import(self) -> BenchmarkResult:
        """Test importing EEGNet model definition."""
        start = time.time()

        try:
            # EEGNet model definition (from paper)
            from tensorflow.keras.models import Model
            from tensorflow.keras.layers import Dense, Activation, Permute, Dropout
            from tensorflow.keras.layers import Conv2D, MaxPooling2D, AveragePooling2D
            from tensorflow.keras.layers import SeparableConv2D, DepthwiseConv2D
            from tensorflow.keras.layers import BatchNormalization
            from tensorflow.keras.layers import SpatialDropout2D
            from tensorflow.keras.layers import Input, Flatten
            from tensorflow.keras.constraints import max_norm

            return BenchmarkResult(
                test_name="Import Test",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics={'keras_layers_imported': True}
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
        """Test building and compiling EEGNet model."""
        start = time.time()

        try:
            model = self._build_eegnet(
                nb_classes=2,
                Chans=8,
                Samples=128,
                dropoutRate=0.5
            )

            # Compile model
            model.compile(
                loss='categorical_crossentropy',
                optimizer='adam',
                metrics=['accuracy']
            )

            metrics = {
                'total_params': model.count_params(),
                'trainable_params': sum([np.prod(v.get_shape()) for v in model.trainable_weights]),
                'input_shape': model.input_shape,
                'output_shape': model.output_shape
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
        """Test EEGNet predictions integrated with HBCM."""
        start = time.time()

        try:
            from src.coupling import HeartBrainCouplingModel
            from src.neural import FitzHughNagumo
            from src.cardiac import VanDerPolOscillator
            from src.coupling import CouplingParameters

            # Create synthetic EEG data
            n_trials = 10
            n_channels = 8
            n_samples = 128
            X = np.random.randn(n_trials, n_channels, n_samples, 1)
            y = np.random.randint(0, 2, (n_trials, 2))  # One-hot encoded

            # Build and train EEGNet (minimal training)
            model = self._build_eegnet(nb_classes=2, Chans=n_channels, Samples=n_samples)
            model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

            # Quick training (just to test, not for accuracy)
            history = model.fit(X, y, epochs=2, verbose=0, validation_split=0.2)

            # Get predictions
            predictions = model.predict(X[:1])

            # Use prediction confidence to modulate HBCM
            confidence = float(np.max(predictions[0]))

            # Create HBCM
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(stimulus_amplitude=confidence),
                cardiac_model=VanDerPolOscillator(),
                coupling=CouplingParameters()
            )

            # Run simulation
            trajectory = hbcm.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, 1.0),
                dt=0.01
            )

            metrics = {
                'eegnet_params': model.count_params(),
                'training_loss': float(history.history['loss'][-1]),
                'prediction_confidence': confidence,
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

    def _build_eegnet(self, nb_classes, Chans=64, Samples=128,
                     dropoutRate=0.5, kernLength=64, F1=8, D=2, F2=16,
                     norm_rate=0.25, dropoutType='Dropout'):
        """
        Build EEGNet model architecture.

        Based on: https://github.com/vlawhern/arl-eegmodels

        Args:
            nb_classes: Number of classes
            Chans: Number of EEG channels
            Samples: Number of time samples
            dropoutRate: Dropout rate
            kernLength: Length of temporal convolution
            F1: Number of temporal filters
            D: Depth multiplier (spatial filters)
            F2: Number of pointwise filters
            norm_rate: Max norm constraint
            dropoutType: 'Dropout' or 'SpatialDropout2D'

        Returns:
            Keras model
        """
        from tensorflow.keras.models import Model
        from tensorflow.keras.layers import Dense, Activation, Permute, Dropout
        from tensorflow.keras.layers import Conv2D, AveragePooling2D
        from tensorflow.keras.layers import SeparableConv2D, DepthwiseConv2D
        from tensorflow.keras.layers import BatchNormalization
        from tensorflow.keras.layers import SpatialDropout2D
        from tensorflow.keras.layers import Input, Flatten
        from tensorflow.keras.constraints import max_norm

        if dropoutType == 'SpatialDropout2D':
            dropoutType = SpatialDropout2D
        elif dropoutType == 'Dropout':
            dropoutType = Dropout
        else:
            raise ValueError('dropoutType must be one of SpatialDropout2D or Dropout')

        input1 = Input(shape=(Chans, Samples, 1))

        # Block 1
        block1 = Conv2D(F1, (1, kernLength), padding='same',
                       input_shape=(Chans, Samples, 1),
                       use_bias=False)(input1)
        block1 = BatchNormalization()(block1)
        block1 = DepthwiseConv2D((Chans, 1), use_bias=False,
                                depth_multiplier=D,
                                depthwise_constraint=max_norm(1.))(block1)
        block1 = BatchNormalization()(block1)
        block1 = Activation('elu')(block1)
        block1 = AveragePooling2D((1, 4))(block1)
        block1 = dropoutType(dropoutRate)(block1)

        # Block 2
        block2 = SeparableConv2D(F2, (1, 16),
                                use_bias=False, padding='same')(block1)
        block2 = BatchNormalization()(block2)
        block2 = Activation('elu')(block2)
        block2 = AveragePooling2D((1, 8))(block2)
        block2 = dropoutType(dropoutRate)(block2)

        flatten = Flatten(name='flatten')(block2)

        dense = Dense(nb_classes, name='dense',
                     kernel_constraint=max_norm(norm_rate))(flatten)
        softmax = Activation('softmax', name='softmax')(dense)

        return Model(inputs=input1, outputs=softmax)

    def benchmark_inference_latency(self) -> BenchmarkResult:
        """Benchmark EEGNet inference latency."""
        start = time.time()

        try:
            # Build model
            model = self._build_eegnet(nb_classes=2, Chans=8, Samples=128)

            # Create test data
            X = np.random.randn(1, 8, 128, 1).astype(np.float32)

            # Benchmark inference
            latency_stats = PerformanceBenchmark.measure_latency(
                model.predict,
                X,
                iterations=100,
                verbose=0
            )

            metrics = {
                **latency_stats,
                'model_params': model.count_params(),
                'note': 'Single sample inference (batch_size=1)'
            }

            return BenchmarkResult(
                test_name="Inference Latency Benchmark",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )

        except Exception as e:
            return BenchmarkResult(
                test_name="Inference Latency Benchmark",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )


def run_eegnet_tests():
    """Run all EEGNet validation tests."""
    tester = EEGNetValidationTests()
    results = tester.run_all_tests()

    # Run latency benchmark
    print("\nRunning inference latency benchmark...", end=' ')
    benchmark = tester.benchmark_inference_latency()
    results.append(benchmark)
    print(f"[{benchmark.status.upper()}] ({benchmark.execution_time:.3f}s)")
    if benchmark.status == 'pass':
        print(f"  Mean latency: {benchmark.metrics.get('mean_ms', 0):.2f}ms")
        print(f"  P95 latency: {benchmark.metrics.get('p95_ms', 0):.2f}ms")

    # Print summary
    summary = tester.get_summary()
    print(f"\n{'='*70}")
    print("EEGNet Validation Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Success Rate: {summary['success_rate']:.1f}%")
    print(f"{'='*70}\n")

    return results


if __name__ == '__main__':
    run_eegnet_tests()
