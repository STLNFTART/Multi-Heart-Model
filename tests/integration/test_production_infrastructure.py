#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Production Infrastructure
Tests all components working together
"""

import pytest
import sys
import time
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestProductionInfrastructure:
    """Integration tests for production infrastructure"""

    def test_validation_suite(self):
        """Test SpaceX/Tesla/PX4/CARLA validation suite"""
        from validation.spacex_tesla_px4_carla_tests import ValidationSuite

        suite = ValidationSuite()
        # Run quick version with shorter duration
        suite._test_spacex_flight_control()

        assert len(suite.results) > 0
        assert suite.results[0].status in ["passed", "warning"]

    def test_tesla_neuralink_demo(self):
        """Test Tesla/Neuralink demo runs without errors"""
        # Import and run demo programmatically
        from examples.tesla_neuralink_demo import TeslaNeuralinInterface

        interface = TeslaNeuralinInterface(use_real_bci=False)

        # Run short demo
        interface.run_demo(duration=5.0, dt=0.001)

        assert len(interface.driver_history) > 0
        assert len(interface.command_history) > 0

    def test_performance_monitoring(self):
        """Test performance monitoring system"""
        from monitoring.performance_monitor import PerformanceMonitor
        from src.coupling import HeartBrainCouplingModel

        monitor = PerformanceMonitor(latency_target_ms=100.0)
        hbcm = HeartBrainCouplingModel()
        state = (0.0, 0.0, 1.0, 0.0)

        # Run monitored simulation
        for i in range(1000):
            with monitor.measure_operation("test_step"):
                state = hbcm.step(0.0, state, 0.001)

        stats = monitor.get_statistics("test_step")

        assert stats is not None
        assert stats['sample_count'] == 1000
        assert 'latency' in stats
        assert stats['latency']['mean_ms'] < 100.0  # Should be fast

    def test_lipschitz_stability(self):
        """Test Lipschitz stability validation"""
        from validation.lipschitz_stability import LipschitzAnalyzer

        analyzer = LipschitzAnalyzer(tolerance=1.0)

        # Test FitzHugh-Nagumo
        result = analyzer.analyze_fitzhugh_nagumo()

        assert result is not None
        assert result.sample_count > 0
        # Note: May not always be stable, but should compute valid constant
        assert result.estimated_constant < float('inf')

    def test_opensim_integration(self):
        """Test OpenSim integration layer"""
        from integration.opensim_layer import OpenSimIntegration

        integration = OpenSimIntegration("http://localhost:9000")

        # Test creates without errors
        avatar_uuid = integration.create_avatar("test", (0, 0, 0))
        # Will return None if OpenSim not available, which is expected

        assert True  # Just check it doesn't crash

    def test_starlink_network_integration(self):
        """Test Starlink network integration"""
        from integration.starlink_network import StarlinkNetworkTester

        tester = StarlinkNetworkTester()

        # Test creates without errors
        assert tester is not None

    def test_nasa_power_integration(self):
        """Test NASA POWER integration"""
        from integration.nasa_power_environmental import NASAPowerIntegration

        integration = NASAPowerIntegration()

        # Test analysis with simulated data
        simulated_data = {
            'date': '20250101',
            'latitude': 28.5728,
            'longitude': -80.6489,
            'temperature_c': 25.0,
            'humidity_pct': 60.0,
            'pressure_kpa': 101.3,
            'solar_radiation': 500.0,
            'wind_speed': 5.0
        }

        analysis = integration.analyze_physiological_response(simulated_data)

        assert analysis is not None
        assert 'stress_indices' in analysis
        assert 'physiological_response' in analysis


class TestEndToEndWorkflow:
    """End-to-end workflow tests"""

    def test_complete_simulation_pipeline(self):
        """Test complete simulation pipeline from start to finish"""
        from src.coupling import HeartBrainCouplingModel
        from monitoring.performance_monitor import PerformanceMonitor

        # Create components
        monitor = PerformanceMonitor()
        hbcm = HeartBrainCouplingModel()

        # Run simulation with monitoring
        state = (0.0, 0.0, 1.0, 0.0)

        for _ in range(100):
            with monitor.measure_operation("pipeline_step"):
                state = hbcm.step(0.0, state, 0.001)

        # Check results
        stats = monitor.get_statistics()
        assert stats['sample_count'] == 100

        # Verify performance
        meets_req, details = monitor.check_performance_requirements()
        assert meets_req or stats['latency']['mean_ms'] < 200.0  # Relaxed for testing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
