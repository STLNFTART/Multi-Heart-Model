"""
Space API Integration Layer - Interface Boundary

This module provides clean dataclass interfaces between external space APIs
(NASA, SpaceX, Starlink) and internal Multi-Heart-Model systems.

Key Principle: api_integrations is a pure data provider.
This layer transforms raw API data into domain-specific objects.

Author: Multi-Heart-Model Team
Date: 2025-11-15
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
import numpy as np


@dataclass
class EnvContext:
    """
    Environmental context from NASA POWER and EPIC data.

    Used for:
    - Drone/UAV environment models
    - AV/road condition priors
    - Energy/thermal models
    - Multi-Heart simulation metadata
    """

    # Location and time
    latitude: float
    longitude: float
    timestamp: datetime

    # Solar irradiance (W/m²)
    global_horizontal_irradiance: Optional[float] = None  # GHI
    direct_normal_irradiance: Optional[float] = None      # DNI
    diffuse_horizontal_irradiance: Optional[float] = None # DHI

    # Temperature (Kelvin)
    temperature_2m: Optional[float] = None
    temperature_range: Optional[tuple[float, float]] = None  # (min, max)

    # Pressure and wind
    surface_pressure: Optional[float] = None  # kPa
    wind_speed: Optional[float] = None        # m/s
    wind_direction: Optional[float] = None    # degrees

    # Humidity
    relative_humidity: Optional[float] = None  # %

    # Metadata
    source: str = "nasa_power"
    data_quality: str = "unknown"

    @classmethod
    def from_power(cls, power_data: Dict[str, Any], lat: float, lon: float,
                   timestamp: datetime) -> 'EnvContext':
        """
        Transform NASA POWER API response to EnvContext.

        Args:
            power_data: Raw response from NASA POWER API
            lat: Latitude
            lon: Longitude
            timestamp: Timestamp of data

        Returns:
            EnvContext instance

        Example:
            >>> from api_integrations import APIManager
            >>> api = APIManager()
            >>> power = api.nasa_power.get_hourly(lat=38.63, lon=-90.20, ...)
            >>> env = EnvContext.from_power(power, 38.63, -90.20, datetime.now())
        """
        params = power_data.get('properties', {}).get('parameter', {})

        return cls(
            latitude=lat,
            longitude=lon,
            timestamp=timestamp,
            global_horizontal_irradiance=params.get('ALLSKY_SFC_SW_DWN'),
            temperature_2m=params.get('T2M'),
            surface_pressure=params.get('PS'),
            wind_speed=params.get('WS10M'),
            wind_direction=params.get('WD10M'),
            relative_humidity=params.get('RH2M'),
            source='nasa_power',
            data_quality='validated'
        )

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary for JSON serialization."""
        return {
            'location': [self.latitude, self.longitude],
            'timestamp': self.timestamp.isoformat(),
            'solar': {
                'ghi': self.global_horizontal_irradiance,
                'dni': self.direct_normal_irradiance,
                'dhi': self.diffuse_horizontal_irradiance
            },
            'temperature': {
                'current': self.temperature_2m,
                'range': self.temperature_range
            },
            'wind': {
                'speed': self.wind_speed,
                'direction': self.wind_direction
            },
            'pressure': self.surface_pressure,
            'humidity': self.relative_humidity,
            'source': self.source,
            'quality': self.data_quality
        }

    def get_thermal_stress_factor(self) -> float:
        """
        Calculate thermal stress factor for control systems.

        Returns:
            Float in [0, 1] where 0=no stress, 1=extreme stress
        """
        if self.temperature_2m is None:
            return 0.0

        # Convert Kelvin to Celsius
        temp_c = self.temperature_2m - 273.15

        # Nominal range: 15-25°C (no stress)
        # Stress increases outside this range
        if 15 <= temp_c <= 25:
            return 0.0
        elif temp_c < 15:
            # Cold stress (linear from 0°C)
            return max(0.0, min(1.0, (15 - temp_c) / 15))
        else:
            # Heat stress (linear from 25°C to 45°C)
            return max(0.0, min(1.0, (temp_c - 25) / 20))

    def get_solar_power_factor(self) -> float:
        """
        Calculate available solar power factor.

        Returns:
            Float in [0, 1] where 0=night, 1=peak solar
        """
        if self.global_horizontal_irradiance is None:
            return 0.0

        # Typical peak GHI ~1000 W/m²
        return min(1.0, self.global_horizontal_irradiance / 1000.0)


@dataclass
class CommsProfile:
    """
    Communications profile from Starlink metrics.

    Used for:
    - Network delay modeling in control loops
    - Communication window scheduling
    - Worst-case blackout bounds
    """

    # Network performance
    baseline_latency_ms: float
    jitter_ms: float
    packet_loss_percent: float

    # Bandwidth
    download_mbps: Optional[float] = None
    upload_mbps: Optional[float] = None

    # Reliability
    uptime_percent: Optional[float] = None
    outage_duration_seconds: Optional[float] = None

    # Coverage
    region_id: Optional[str] = None
    satellite_count: Optional[int] = None

    # Metadata
    source: str = "starlink"
    timestamp: Optional[datetime] = None

    @classmethod
    def from_starlink(cls, metrics: Dict[str, Any], region_id: str = None) -> 'CommsProfile':
        """
        Transform Starlink metrics API response to CommsProfile.

        Args:
            metrics: Raw Starlink metrics data
            region_id: Region identifier

        Returns:
            CommsProfile instance

        Example:
            >>> from api_integrations import APIManager
            >>> api = APIManager()
            >>> metrics = api.starlink.get_residential_metrics(region_id='US-STL')
            >>> comms = CommsProfile.from_starlink(metrics, 'US-STL')
        """
        # Extract metrics (structure depends on actual Starlink API)
        # This is a template - adjust based on real API response
        performance = metrics.get('performance', {})

        return cls(
            baseline_latency_ms=performance.get('latency_ms', 40.0),
            jitter_ms=performance.get('jitter_ms', 5.0),
            packet_loss_percent=performance.get('packet_loss', 0.1),
            download_mbps=performance.get('download_mbps'),
            upload_mbps=performance.get('upload_mbps'),
            uptime_percent=performance.get('uptime_percent'),
            region_id=region_id,
            source='starlink',
            timestamp=datetime.now()
        )

    @classmethod
    def create_nominal(cls) -> 'CommsProfile':
        """Create nominal (ideal) communications profile for testing."""
        return cls(
            baseline_latency_ms=20.0,
            jitter_ms=2.0,
            packet_loss_percent=0.0,
            download_mbps=200.0,
            upload_mbps=50.0,
            uptime_percent=99.9,
            source='nominal'
        )

    @classmethod
    def create_degraded(cls, severity: float = 0.5) -> 'CommsProfile':
        """
        Create degraded communications profile.

        Args:
            severity: Degradation severity in [0, 1] where 0=nominal, 1=worst case
        """
        return cls(
            baseline_latency_ms=20.0 + (severity * 100.0),  # Up to 120ms
            jitter_ms=2.0 + (severity * 20.0),              # Up to 22ms
            packet_loss_percent=severity * 5.0,             # Up to 5%
            download_mbps=200.0 * (1.0 - severity * 0.8),   # Down to 40 Mbps
            upload_mbps=50.0 * (1.0 - severity * 0.8),      # Down to 10 Mbps
            uptime_percent=99.9 - (severity * 10.0),        # Down to 89.9%
            source='degraded'
        )

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary for JSON serialization."""
        return {
            'latency': {
                'baseline_ms': self.baseline_latency_ms,
                'jitter_ms': self.jitter_ms
            },
            'reliability': {
                'packet_loss_percent': self.packet_loss_percent,
                'uptime_percent': self.uptime_percent
            },
            'bandwidth': {
                'download_mbps': self.download_mbps,
                'upload_mbps': self.upload_mbps
            },
            'region_id': self.region_id,
            'satellite_count': self.satellite_count,
            'source': self.source,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

    def get_network_delay_distribution(self) -> tuple[float, float]:
        """
        Get mean and std dev for network delay distribution.

        Returns:
            (mean_ms, std_ms) tuple for use in stochastic simulations
        """
        mean = self.baseline_latency_ms
        # Jitter approximates std dev
        std = self.jitter_ms
        return (mean, std)

    def is_acceptable_for_realtime_control(self, max_latency_ms: float = 50.0) -> bool:
        """
        Check if comms profile is acceptable for real-time control.

        Args:
            max_latency_ms: Maximum acceptable latency

        Returns:
            True if acceptable, False otherwise
        """
        # Check latency + 3*jitter (99.7% of samples)
        worst_case_latency = self.baseline_latency_ms + (3 * self.jitter_ms)

        return (
            worst_case_latency <= max_latency_ms and
            self.packet_loss_percent <= 1.0 and
            (self.uptime_percent is None or self.uptime_percent >= 99.0)
        )


@dataclass
class ScenarioConfig:
    """
    Scenario configuration from NASA NeoWs and SSD data.

    Used for:
    - Stress testing control under rare conditions
    - Unified control framework demos (orbital → AV → drone → MotorHandPro)
    - Validation narratives
    """

    # Scenario metadata
    scenario_id: str
    seed: int
    description: str

    # Orbital parameters (from SSD)
    orbital_elements: Optional[Dict[str, float]] = None

    # NEO encounters (from NeoWs)
    neo_encounters: List[Dict[str, Any]] = field(default_factory=list)

    # Derived parameters
    max_gravitational_perturbation: Optional[float] = None
    encounter_probability: Optional[float] = None

    # Environmental stress factors
    thermal_stress: float = 0.0
    radiation_stress: float = 0.0

    # Metadata
    source: str = "nasa"
    generated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_nasa(cls, neos_data: Dict[str, Any], ssd_data: Dict[str, Any],
                  seed: int) -> 'ScenarioConfig':
        """
        Generate scenario from NASA NeoWs and SSD data.

        Args:
            neos_data: NEO feed data from NeoWs API
            ssd_data: Small body orbit data from SSD API
            seed: Random seed for reproducibility

        Returns:
            ScenarioConfig instance

        Example:
            >>> from api_integrations import APIManager
            >>> api = APIManager()
            >>> neos = api.nasa_neows.get_feed(start_date='2025-11-15', end_date='2025-11-22')
            >>> ssd = api.nasa_ssd.get_orbit(spk_id='2000433')  # Eros
            >>> scenario = ScenarioConfig.from_nasa(neos, ssd, seed=42)
        """
        # Extract NEO encounters
        encounters = []
        neo_count = 0

        for date, neos_list in neos_data.get('near_earth_objects', {}).items():
            for neo in neos_list[:5]:  # Limit to 5 per day
                encounters.append({
                    'name': neo.get('name'),
                    'date': date,
                    'miss_distance_km': float(neo['close_approach_data'][0]
                                             ['miss_distance']['kilometers']),
                    'velocity_kps': float(neo['close_approach_data'][0]
                                         ['relative_velocity']['kilometers_per_second']),
                    'diameter_km': neo.get('estimated_diameter', {})
                                      .get('kilometers', {}).get('estimated_diameter_max', 0.0)
                })
                neo_count += 1

        # Extract orbital elements from SSD
        orbital_elements = None
        if ssd_data:
            orbital_elements = {
                'semi_major_axis': ssd_data.get('a'),
                'eccentricity': ssd_data.get('e'),
                'inclination': ssd_data.get('i'),
                'perihelion_distance': ssd_data.get('q')
            }

        return cls(
            scenario_id=f"space_{seed}_{neo_count}neos",
            seed=seed,
            description=f"Space scenario with {neo_count} NEO encounters",
            orbital_elements=orbital_elements,
            neo_encounters=encounters,
            source='nasa',
            generated_at=datetime.now()
        )

    @classmethod
    def create_nominal(cls, seed: int = 0) -> 'ScenarioConfig':
        """Create nominal (no perturbations) scenario."""
        return cls(
            scenario_id=f"nominal_{seed}",
            seed=seed,
            description="Nominal scenario with no external perturbations",
            source='synthetic'
        )

    @classmethod
    def create_stress_test(cls, seed: int = 0, severity: float = 0.5) -> 'ScenarioConfig':
        """
        Create stress test scenario with synthetic perturbations.

        Args:
            seed: Random seed
            severity: Stress severity in [0, 1]
        """
        np.random.seed(seed)

        # Generate synthetic NEO encounters
        n_encounters = int(severity * 10) + 1
        encounters = []

        for i in range(n_encounters):
            encounters.append({
                'name': f'SYN-{seed}-{i}',
                'date': '2025-11-15',
                'miss_distance_km': np.random.exponential(1e6),
                'velocity_kps': np.random.normal(20, 5),
                'diameter_km': np.random.exponential(1.0)
            })

        return cls(
            scenario_id=f"stress_{seed}_sev{severity}",
            seed=seed,
            description=f"Stress test scenario (severity={severity})",
            neo_encounters=encounters,
            thermal_stress=severity,
            radiation_stress=severity * 0.8,
            source='synthetic'
        )

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary for JSON serialization."""
        return {
            'scenario_id': self.scenario_id,
            'seed': self.seed,
            'description': self.description,
            'orbital_elements': self.orbital_elements,
            'neo_encounters': self.neo_encounters,
            'stress_factors': {
                'thermal': self.thermal_stress,
                'radiation': self.radiation_stress,
                'gravitational': self.max_gravitational_perturbation
            },
            'source': self.source,
            'generated_at': self.generated_at.isoformat()
        }

    def get_encounter_count(self) -> int:
        """Get number of NEO encounters in this scenario."""
        return len(self.neo_encounters)

    def get_closest_approach_km(self) -> Optional[float]:
        """Get closest NEO approach distance in this scenario."""
        if not self.neo_encounters:
            return None
        return min(enc['miss_distance_km'] for enc in self.neo_encounters)
