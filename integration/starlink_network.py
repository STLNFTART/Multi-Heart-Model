#!/usr/bin/env python3
"""
Starlink Network Testing Integration
Tests Multi-Heart-Model performance over Starlink satellite network
Validates <100ms latency requirements for real-time physiological monitoring
"""

import time
import requests
import json
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class NetworkMetrics:
    """Network performance metrics"""
    latency_ms: float
    jitter_ms: float
    packet_loss_pct: float
    throughput_mbps: float
    timestamp: float


class StarlinkNetworkTester:
    """
    Test Multi-Heart-Model over Starlink network
    Validates real-time streaming performance
    """

    def __init__(self, starlink_api_endpoint: str = "http://starlink.local",
                 api_key: Optional[str] = None):
        """
        Initialize Starlink network tester

        Args:
            starlink_api_endpoint: Starlink API endpoint
            api_key: API key for Starlink services
        """
        self.endpoint = starlink_api_endpoint
        self.api_key = api_key
        self.metrics_history: List[NetworkMetrics] = []

    def measure_latency(self, num_samples: int = 100) -> Dict[str, float]:
        """
        Measure network latency to Starlink satellite

        Args:
            num_samples: Number of ping samples

        Returns:
            Latency statistics
        """
        print(f"Measuring Starlink latency ({num_samples} samples)...")

        latencies = []

        for i in range(num_samples):
            start = time.time()

            try:
                # Send ping to Starlink endpoint
                response = requests.get(
                    f"{self.endpoint}/ping",
                    headers={'Authorization': f'Bearer {self.api_key}'} if self.api_key else {},
                    timeout=5
                )

                if response.status_code == 200:
                    latency_ms = (time.time() - start) * 1000
                    latencies.append(latency_ms)
                else:
                    print(f"  Sample {i+1}: Request failed")

            except Exception as e:
                print(f"  Sample {i+1}: Error - {e}")

            if i % 20 == 0 and i > 0:
                print(f"  Progress: {i}/{num_samples}")

            time.sleep(0.01)  # 10ms between samples

        if not latencies:
            print("✗ No successful samples")
            return {}

        stats = {
            'min_ms': min(latencies),
            'max_ms': max(latencies),
            'avg_ms': statistics.mean(latencies),
            'median_ms': statistics.median(latencies),
            'stdev_ms': statistics.stdev(latencies) if len(latencies) > 1 else 0,
            'samples': len(latencies),
            'under_100ms_pct': 100 * sum(1 for l in latencies if l < 100) / len(latencies)
        }

        print(f"\nLatency Statistics:")
        print(f"  ├─ Min: {stats['min_ms']:.2f} ms")
        print(f"  ├─ Max: {stats['max_ms']:.2f} ms")
        print(f"  ├─ Avg: {stats['avg_ms']:.2f} ms")
        print(f"  ├─ Median: {stats['median_ms']:.2f} ms")
        print(f"  ├─ Stdev: {stats['stdev_ms']:.2f} ms")
        print(f"  └─ <100ms: {stats['under_100ms_pct']:.1f}%")

        return stats

    def test_hbcm_streaming(self, duration: float = 60.0,
                           packet_interval: float = 0.01) -> Dict[str, any]:
        """
        Test HBCM data streaming over Starlink

        Args:
            duration: Test duration in seconds
            packet_interval: Time between packets

        Returns:
            Performance statistics
        """
        print(f"\nTesting HBCM streaming over Starlink ({duration}s)...")

        # Import HBCM
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.coupling import HeartBrainCouplingModel

        hbcm = HeartBrainCouplingModel()
        state = (0.0, 0.0, 1.0, 0.0)

        latencies = []
        packet_count = 0
        failed_packets = 0

        start_time = time.time()
        t = 0.0
        dt = 0.001

        while t < duration:
            # Step HBCM
            state = hbcm.step(t, state, dt)

            # Send packet at interval
            if packet_count * packet_interval <= t:
                v, w, x, y = state

                packet_data = {
                    'timestamp': t,
                    'neural_v': float(v),
                    'neural_w': float(w),
                    'cardiac_x': float(x),
                    'cardiac_y': float(y)
                }

                # Measure send latency
                send_start = time.time()

                try:
                    response = requests.post(
                        f"{self.endpoint}/api/hbcm/data",
                        json=packet_data,
                        headers={'Authorization': f'Bearer {self.api_key}'} if self.api_key else {},
                        timeout=1
                    )

                    if response.status_code == 200:
                        latency_ms = (time.time() - send_start) * 1000
                        latencies.append(latency_ms)
                    else:
                        failed_packets += 1

                except Exception:
                    failed_packets += 1

                packet_count += 1

            t += dt

        total_time = time.time() - start_time

        # Calculate statistics
        if latencies:
            stats = {
                'duration_s': total_time,
                'total_packets': packet_count,
                'successful_packets': len(latencies),
                'failed_packets': failed_packets,
                'packet_loss_pct': 100 * failed_packets / packet_count if packet_count > 0 else 0,
                'avg_latency_ms': statistics.mean(latencies),
                'max_latency_ms': max(latencies),
                'min_latency_ms': min(latencies),
                'under_100ms_pct': 100 * sum(1 for l in latencies if l < 100) / len(latencies),
                'throughput_packets_per_sec': packet_count / total_time
            }

            print(f"\nStreaming Statistics:")
            print(f"  ├─ Total packets: {stats['total_packets']}")
            print(f"  ├─ Successful: {stats['successful_packets']}")
            print(f"  ├─ Packet loss: {stats['packet_loss_pct']:.2f}%")
            print(f"  ├─ Avg latency: {stats['avg_latency_ms']:.2f} ms")
            print(f"  ├─ Max latency: {stats['max_latency_ms']:.2f} ms")
            print(f"  ├─ <100ms: {stats['under_100ms_pct']:.1f}%")
            print(f"  └─ Throughput: {stats['throughput_packets_per_sec']:.1f} pkt/s")

            # Check if meets requirements
            meets_requirements = (
                stats['packet_loss_pct'] < 1.0 and
                stats['avg_latency_ms'] < 100.0 and
                stats['under_100ms_pct'] > 95.0
            )

            if meets_requirements:
                print("\n✓ Performance meets requirements for real-time streaming")
            else:
                print("\n✗ Performance does not meet requirements")

            return stats
        else:
            print("\n✗ No successful packets")
            return {}


def demo_starlink_testing():
    """Demonstration of Starlink network testing"""
    print("=" * 80)
    print("Starlink Network Testing for Multi-Heart-Model")
    print("=" * 80)
    print()

    # Note: This demo runs in offline mode as Starlink API may not be available
    print("NOTE: Running in demonstration mode (Starlink API not required)")
    print()

    tester = StarlinkNetworkTester(
        starlink_api_endpoint="http://starlink.local",
        api_key="demo_api_key"
    )

    # Simulate latency measurements
    print("Simulating Starlink latency test...")
    simulated_latencies = {
        'min_ms': 25.0,
        'max_ms': 95.0,
        'avg_ms': 45.0,
        'median_ms': 42.0,
        'stdev_ms': 15.0,
        'samples': 100,
        'under_100ms_pct': 98.5
    }

    print(f"\nSimulated Latency Statistics:")
    for key, value in simulated_latencies.items():
        print(f"  ├─ {key}: {value}")

    print("\n✓ Demo complete")
    print("\nTo run with real Starlink connection:")
    print("  1. Connect to Starlink terminal")
    print("  2. Configure API endpoint")
    print("  3. Run: python integration/starlink_network.py")


if __name__ == "__main__":
    demo_starlink_testing()
