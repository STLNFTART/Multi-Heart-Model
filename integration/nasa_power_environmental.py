#!/usr/bin/env python3
"""
NASA POWER Environmental Data Integration
Integrates environmental data from NASA POWER API with Multi-Heart-Model
Analyzes physiological responses to environmental conditions
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class EnvironmentalConditions:
    """Environmental conditions from NASA POWER"""
    timestamp: str
    latitude: float
    longitude: float
    temperature_c: float
    humidity_pct: float
    pressure_kpa: float
    solar_radiation: float  # W/m²
    wind_speed: float  # m/s


class NASAPowerIntegration:
    """
    Integration with NASA POWER API
    https://power.larc.nasa.gov/docs/services/api/
    """

    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NASA POWER integration

        Args:
            api_key: Optional API key (not required for public access)
        """
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})

    def get_environmental_data(self,
                              latitude: float,
                              longitude: float,
                              start_date: str,
                              end_date: str) -> Optional[List[Dict]]:
        """
        Fetch environmental data from NASA POWER

        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            start_date: Start date (YYYYMMDD)
            end_date: End date (YYYYMMDD)

        Returns:
            List of daily environmental data
        """
        parameters = [
            'T2M',        # Temperature at 2 meters
            'RH2M',       # Relative Humidity at 2 meters
            'PS',         # Surface Pressure
            'ALLSKY_SFC_SW_DWN',  # Solar radiation
            'WS10M'       # Wind Speed at 10 meters
        ]

        params = {
            'parameters': ','.join(parameters),
            'community': 'RE',
            'longitude': longitude,
            'latitude': latitude,
            'start': start_date,
            'end': end_date,
            'format': 'JSON'
        }

        try:
            print(f"Fetching NASA POWER data for ({latitude}, {longitude})...")
            response = self.session.get(self.BASE_URL, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self._parse_nasa_response(data, latitude, longitude)
            else:
                print(f"Error: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"Error fetching NASA POWER data: {e}")
            return None

    def _parse_nasa_response(self, data: Dict, lat: float, lon: float) -> List[Dict]:
        """Parse NASA POWER API response"""
        parameters = data.get('properties', {}).get('parameter', {})

        # Get dates
        dates = list(parameters.get('T2M', {}).keys())

        results = []
        for date_str in dates:
            env_data = {
                'date': date_str,
                'latitude': lat,
                'longitude': lon,
                'temperature_c': parameters.get('T2M', {}).get(date_str, 20.0),
                'humidity_pct': parameters.get('RH2M', {}).get(date_str, 50.0),
                'pressure_kpa': parameters.get('PS', {}).get(date_str, 101.3),
                'solar_radiation': parameters.get('ALLSKY_SFC_SW_DWN', {}).get(date_str, 200.0),
                'wind_speed': parameters.get('WS10M', {}).get(date_str, 5.0)
            }
            results.append(env_data)

        return results

    def analyze_physiological_response(self,
                                      env_data: Dict,
                                      baseline_state: Tuple[float, ...] = (0.0, 0.0, 1.0, 0.0)) -> Dict:
        """
        Analyze how environmental conditions affect physiological state

        Args:
            env_data: Environmental data dictionary
            baseline_state: Baseline HBCM state

        Returns:
            Analysis results
        """
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.coupling import HeartBrainCouplingModel

        # Calculate environmental stress index
        temp = env_data['temperature_c']
        humidity = env_data['humidity_pct']
        pressure = env_data['pressure_kpa']

        # Heat index calculation (simplified)
        heat_stress = 0.0
        if temp > 26.7:  # 80°F
            heat_stress = (temp - 26.7) / 20.0
            if humidity > 60:
                heat_stress *= (1 + (humidity - 60) / 40.0)

        # Cold stress
        cold_stress = max(0, (10.0 - temp) / 20.0) if temp < 10 else 0.0

        # Pressure stress (deviation from 101.3 kPa)
        pressure_stress = abs(pressure - 101.3) / 10.0

        # Overall environmental stress
        total_stress = np.clip(heat_stress + cold_stress + pressure_stress, 0, 1)

        # Create HBCM with stress-modulated parameters
        hbcm = HeartBrainCouplingModel()

        # Adjust stimulus based on environmental stress
        stimulus_amplitude = 0.3 + 0.5 * total_stress
        hbcm.neural_model.stimulus_amplitude = stimulus_amplitude

        # Simulate response
        trajectory = hbcm.simulate(
            initial_state=baseline_state,
            t_span=(0.0, 60.0),  # 1 minute
            dt=0.001
        )

        times, neural, cardiac = hbcm.extract_series(trajectory)

        # Analyze response
        neural_v = np.array([v for v, w in neural])
        cardiac_x = np.array([x for x, y in cardiac])

        analysis = {
            'environmental_data': env_data,
            'stress_indices': {
                'heat_stress': float(heat_stress),
                'cold_stress': float(cold_stress),
                'pressure_stress': float(pressure_stress),
                'total_stress': float(total_stress)
            },
            'physiological_response': {
                'neural_amplitude': float(np.max(np.abs(neural_v))),
                'cardiac_amplitude': float(np.max(np.abs(cardiac_x))),
                'neural_mean': float(np.mean(neural_v)),
                'cardiac_mean': float(np.mean(cardiac_x)),
                'estimated_hr_increase_pct': float(total_stress * 20)  # Up to 20% increase
            },
            'stimulus_amplitude': float(stimulus_amplitude)
        }

        return analysis


def demo_nasa_power_integration():
    """Demonstration of NASA POWER integration"""
    print("=" * 80)
    print("NASA POWER Environmental Data Integration")
    print("=" * 80)
    print()

    integration = NASAPowerIntegration()

    # Example: Kennedy Space Center, Florida
    latitude = 28.5728
    longitude = -80.6489
    location_name = "Kennedy Space Center, FL"

    print(f"Location: {location_name}")
    print(f"Coordinates: ({latitude}, {longitude})")
    print()

    # Get last 7 days of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    # Fetch data
    env_data_list = integration.get_environmental_data(
        latitude, longitude, start_str, end_str
    )

    if env_data_list:
        print(f"✓ Retrieved {len(env_data_list)} days of environmental data\n")

        # Analyze most recent day
        latest_data = env_data_list[-1]

        print(f"Latest Conditions ({latest_data['date']}):")
        print(f"  ├─ Temperature: {latest_data['temperature_c']:.1f}°C")
        print(f"  ├─ Humidity: {latest_data['humidity_pct']:.1f}%")
        print(f"  ├─ Pressure: {latest_data['pressure_kpa']:.1f} kPa")
        print(f"  ├─ Solar Radiation: {latest_data['solar_radiation']:.1f} W/m²")
        print(f"  └─ Wind Speed: {latest_data['wind_speed']:.1f} m/s")

        # Analyze physiological response
        print("\nAnalyzing physiological response to environmental conditions...")
        analysis = integration.analyze_physiological_response(latest_data)

        print(f"\nEnvironmental Stress Indices:")
        stress = analysis['stress_indices']
        print(f"  ├─ Heat Stress: {stress['heat_stress']:.3f}")
        print(f"  ├─ Cold Stress: {stress['cold_stress']:.3f}")
        print(f"  ├─ Pressure Stress: {stress['pressure_stress']:.3f}")
        print(f"  └─ Total Stress: {stress['total_stress']:.3f}")

        print(f"\nPhysiological Response:")
        response = analysis['physiological_response']
        print(f"  ├─ Neural Amplitude: {response['neural_amplitude']:.3f}")
        print(f"  ├─ Cardiac Amplitude: {response['cardiac_amplitude']:.3f}")
        print(f"  └─ Estimated HR Increase: {response['estimated_hr_increase_pct']:.1f}%")

        print("\n✓ Analysis complete")

    else:
        print("✗ Could not retrieve environmental data")
        print("\nUsing simulated data for demonstration...")

        simulated_data = {
            'date': datetime.now().strftime("%Y%m%d"),
            'latitude': latitude,
            'longitude': longitude,
            'temperature_c': 32.0,
            'humidity_pct': 75.0,
            'pressure_kpa': 101.3,
            'solar_radiation': 850.0,
            'wind_speed': 5.5
        }

        analysis = integration.analyze_physiological_response(simulated_data)

        print(f"\nSimulated Environmental Conditions:")
        print(f"  ├─ Temperature: {simulated_data['temperature_c']:.1f}°C")
        print(f"  ├─ Humidity: {simulated_data['humidity_pct']:.1f}%")
        print(f"  └─ Total Stress: {analysis['stress_indices']['total_stress']:.3f}")

        print("\n✓ Simulation complete")


if __name__ == "__main__":
    demo_nasa_power_integration()
