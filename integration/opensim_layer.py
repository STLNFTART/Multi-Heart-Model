#!/usr/bin/env python3
"""
OpenSim Integration Layer
Connects Multi-Heart-Model to OpenSimulator virtual environment
"""

import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class OpenSimAvatar:
    """OpenSim avatar representation"""
    uuid: str
    name: str
    position: Tuple[float, float, float]
    heart_rate: float
    neural_activity: float


class OpenSimIntegration:
    """
    Integration with OpenSimulator for virtual environment testing
    Streams physiological data to virtual avatars
    """

    def __init__(self, opensim_url: str = "http://localhost:9000",
                 api_key: Optional[str] = None):
        """
        Initialize OpenSim integration

        Args:
            opensim_url: OpenSim REST API endpoint
            api_key: API key for authentication
        """
        self.opensim_url = opensim_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })

    def connect(self) -> bool:
        """Test connection to OpenSim"""
        try:
            response = self.session.get(f"{self.opensim_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"OpenSim connection error: {e}")
            return False

    def create_avatar(self, name: str, initial_position: Tuple[float, float, float]) -> Optional[str]:
        """Create new avatar in OpenSim"""
        try:
            payload = {
                "name": name,
                "position": list(initial_position),
                "avatar_type": "physiological_monitor"
            }

            response = self.session.post(
                f"{self.opensim_url}/api/avatars",
                json=payload,
                timeout=10
            )

            if response.status_code == 201:
                data = response.json()
                return data.get('uuid')
            return None

        except Exception as e:
            print(f"Error creating avatar: {e}")
            return None

    def update_avatar_physiology(self, avatar_uuid: str,
                                heart_rate: float,
                                neural_activity: float,
                                stress_level: float) -> bool:
        """
        Update avatar's physiological state in OpenSim

        Args:
            avatar_uuid: Avatar UUID
            heart_rate: Heart rate in BPM
            neural_activity: Neural activity level (0-1)
            stress_level: Stress level (0-1)

        Returns:
            Success status
        """
        try:
            payload = {
                "heart_rate_bpm": heart_rate,
                "neural_activity": neural_activity,
                "stress_level": stress_level,
                "timestamp": time.time()
            }

            response = self.session.put(
                f"{self.opensim_url}/api/avatars/{avatar_uuid}/physiology",
                json=payload,
                timeout=5
            )

            return response.status_code == 200

        except Exception as e:
            print(f"Error updating avatar physiology: {e}")
            return False

    def get_avatar_position(self, avatar_uuid: str) -> Optional[Tuple[float, float, float]]:
        """Get avatar's current position in virtual world"""
        try:
            response = self.session.get(
                f"{self.opensim_url}/api/avatars/{avatar_uuid}",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                pos = data.get('position', [0, 0, 0])
                return tuple(pos)
            return None

        except Exception as e:
            print(f"Error getting avatar position: {e}")
            return None

    def stream_hbcm_data(self, avatar_uuid: str, hbcm_model,
                        duration: float = 60.0, dt: float = 0.001,
                        update_interval: float = 0.1):
        """
        Stream HBCM data to OpenSim avatar

        Args:
            avatar_uuid: Avatar to update
            hbcm_model: HeartBrainCouplingModel instance
            duration: Stream duration in seconds
            dt: HBCM timestep
            update_interval: OpenSim update interval
        """
        print(f"Streaming HBCM data to OpenSim avatar {avatar_uuid}...")

        state = (0.0, 0.0, 1.0, 0.0)
        last_update = 0.0
        t = 0.0

        while t < duration:
            # Step HBCM
            state = hbcm_model.step(t, state, dt)

            # Update OpenSim at specified interval
            if t - last_update >= update_interval:
                v, w, x, y = state

                # Convert to physiological metrics
                neural_activity = float(np.clip(np.abs(v) / 2.0, 0, 1))
                heart_rate = 60.0 + 40.0 * np.abs(x)  # Estimate
                stress_level = float(np.clip((np.abs(v) + np.abs(x)) / 4.0, 0, 1))

                # Update avatar
                success = self.update_avatar_physiology(
                    avatar_uuid, heart_rate, neural_activity, stress_level
                )

                if not success:
                    print(f"Warning: Failed to update at t={t:.1f}s")

                last_update = t

            t += dt

        print("✓ Streaming complete")


def demo_opensim_integration():
    """Demonstration of OpenSim integration"""
    print("=" * 80)
    print("OpenSim Integration Demonstration")
    print("=" * 80)
    print()

    # Import HBCM
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.coupling import HeartBrainCouplingModel

    # Create integration (will use mock if OpenSim not available)
    integration = OpenSimIntegration(opensim_url="http://localhost:9000")

    # Test connection
    print("Testing OpenSim connection...")
    if integration.connect():
        print("✓ Connected to OpenSim")
    else:
        print("✗ OpenSim not available - using mock mode")

    # Create avatar
    print("\nCreating test avatar...")
    avatar_uuid = integration.create_avatar("TestSubject", (128, 128, 25))

    if avatar_uuid:
        print(f"✓ Avatar created: {avatar_uuid}")

        # Create HBCM model
        hbcm = HeartBrainCouplingModel()

        # Stream data
        print("\nStreaming HBCM data to avatar...")
        integration.stream_hbcm_data(avatar_uuid, hbcm, duration=10.0)

        print("\n✓ Demo complete")
    else:
        print("✗ Could not create avatar")


if __name__ == "__main__":
    demo_opensim_integration()
