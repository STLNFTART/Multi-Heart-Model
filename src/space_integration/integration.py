"""
Space API Integration Functions

High-level functions that call api_integrations and return
domain-specific dataclasses.

IMPORTANT: These functions should ONLY be called from high-level code,
NEVER from control kernels or tight loops.

Author: Multi-Heart-Model Team
Date: 2025-11-15
"""

from datetime import datetime
from typing import Optional
import logging

from .context import EnvContext, CommsProfile, ScenarioConfig

# Lazy import to avoid dependency if api_integrations not available
_api_manager = None

logger = logging.getLogger(__name__)


def _get_api_manager():
    """Lazy initialization of APIManager."""
    global _api_manager
    if _api_manager is None:
        try:
            from api_integrations import APIManager
            _api_manager = APIManager()
            logger.info("APIManager initialized successfully")
        except ImportError:
            logger.warning("api_integrations not available - using fallback")
            _api_manager = None
    return _api_manager


def build_environment_context(
    lat: float,
    lon: float,
    timestamp: Optional[datetime] = None
) -> EnvContext:
    """
    Build environmental context from NASA POWER data.

    This function is the ONLY place where NASA POWER API should be called
    for environment modeling.

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        timestamp: Time for which to get data (default: now)

    Returns:
        EnvContext with environmental parameters

    Example:
        >>> env = build_environment_context(38.63, -90.20)
        >>> thermal_stress = env.get_thermal_stress_factor()
        >>> solar_factor = env.get_solar_power_factor()

    Usage in Control Systems:
        # HIGH-LEVEL, before control loop
        env_context = build_environment_context(lat, lon, time)

        # Pass to control initialization
        controller = DroneController(env_context=env_context)

        # Controller uses env_context.get_thermal_stress_factor()
        # but NEVER calls api_integrations directly
    """
    if timestamp is None:
        timestamp = datetime.now()

    api = _get_api_manager()

    if api is None:
        # Fallback: return synthetic data
        logger.warning("Using synthetic environment context (API not available)")
        return EnvContext(
            latitude=lat,
            longitude=lon,
            timestamp=timestamp,
            temperature_2m=293.15,  # 20°C
            source='synthetic'
        )

    try:
        # Call NASA POWER API
        # Note: Adjust parameters based on actual API
        power_data = api.nasa_power.get_hourly(
            lat=lat,
            lon=lon,
            parameters=['ALLSKY_SFC_SW_DWN', 'T2M', 'PS', 'WS10M', 'WD10M', 'RH2M'],
            start=timestamp.strftime('%Y%m%d'),
            end=timestamp.strftime('%Y%m%d')
        )

        return EnvContext.from_power(power_data, lat, lon, timestamp)

    except Exception as e:
        logger.error(f"Failed to get NASA POWER data: {e}")
        # Return synthetic fallback
        return EnvContext(
            latitude=lat,
            longitude=lon,
            timestamp=timestamp,
            temperature_2m=293.15,
            source='fallback'
        )


def get_comms_profile(
    region_id: Optional[str] = None,
    severity: Optional[float] = None
) -> CommsProfile:
    """
    Get communications profile from Starlink metrics.

    This function is the ONLY place where Starlink API should be called
    for network modeling.

    Args:
        region_id: Region identifier (e.g., 'US-STL')
        severity: If set, return degraded profile instead of real data

    Returns:
        CommsProfile with network parameters

    Example:
        >>> comms = get_comms_profile(region_id='US-STL')
        >>> mean, std = comms.get_network_delay_distribution()
        >>> acceptable = comms.is_acceptable_for_realtime_control(max_latency_ms=50)

    Usage in Control Systems:
        # HIGH-LEVEL, before control loop
        comms_profile = get_comms_profile(region_id='US-STL')

        # Pass to network simulator
        network = NetworkSimulator(comms_profile=comms_profile)

        # Network uses comms_profile.get_network_delay_distribution()
        # but NEVER calls api_integrations directly
    """
    # If severity specified, return synthetic degraded profile
    if severity is not None:
        return CommsProfile.create_degraded(severity=severity)

    api = _get_api_manager()

    if api is None or region_id is None:
        # Fallback: return nominal profile
        logger.warning("Using nominal communications profile")
        return CommsProfile.create_nominal()

    try:
        # Call Starlink API
        metrics = api.starlink.get_residential_metrics(region_id=region_id)
        return CommsProfile.from_starlink(metrics, region_id=region_id)

    except Exception as e:
        logger.error(f"Failed to get Starlink metrics: {e}")
        # Return nominal fallback
        return CommsProfile.create_nominal()


def generate_space_scenario(seed: int, use_real_data: bool = False) -> ScenarioConfig:
    """
    Generate space scenario from NASA NeoWs and SSD data.

    This function is the ONLY place where NeoWs/SSD APIs should be called
    for scenario generation.

    Args:
        seed: Random seed for reproducibility
        use_real_data: If True, fetch real NASA data; if False, use synthetic

    Returns:
        ScenarioConfig with orbital parameters and NEO encounters

    Example:
        >>> scenario = generate_space_scenario(seed=42, use_real_data=True)
        >>> n_encounters = scenario.get_encounter_count()
        >>> closest_km = scenario.get_closest_approach_km()

    Usage in Control Systems:
        # HIGH-LEVEL, scenario setup
        scenario = generate_space_scenario(seed=42)

        # Pass to Primal Logic simulator
        simulator = PrimalLogicSim(scenario=scenario)

        # Simulator uses scenario.thermal_stress, scenario.neo_encounters
        # but NEVER calls api_integrations directly
    """
    if not use_real_data:
        # Synthetic scenario for testing
        return ScenarioConfig.create_stress_test(seed=seed, severity=0.5)

    api = _get_api_manager()

    if api is None:
        logger.warning("Using synthetic space scenario (API not available)")
        return ScenarioConfig.create_stress_test(seed=seed, severity=0.3)

    try:
        # Get NEO feed for next 7 days
        from datetime import timedelta
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)

        neos_data = api.nasa_neows.get_feed(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )

        # Get a sample asteroid orbit (Eros as example)
        ssd_data = api.nasa_ssd.get_orbit(spk_id='2000433')

        return ScenarioConfig.from_nasa(neos_data, ssd_data, seed=seed)

    except Exception as e:
        logger.error(f"Failed to get NASA scenario data: {e}")
        # Return synthetic fallback
        return ScenarioConfig.create_stress_test(seed=seed, severity=0.3)


# Convenience functions for HBCM metadata enrichment

def get_environment_metadata(lat: float, lon: float) -> dict:
    """
    Get environment metadata for HBCM run enrichment.

    Returns a dictionary suitable for adding to HBCM metadata.

    Example:
        >>> metadata = get_environment_metadata(38.63, -90.20)
        >>> hbcm_run = {
        ...     "run_id": "hbcm_123",
        ...     "environment_context": metadata
        ... }
    """
    env = build_environment_context(lat, lon)
    return {
        "source": env.source,
        "location": [env.latitude, env.longitude],
        "time": env.timestamp.isoformat(),
        "summary": {
            "ghi": env.global_horizontal_irradiance,
            "temp": env.temperature_2m,
            "thermal_stress": env.get_thermal_stress_factor(),
            "solar_factor": env.get_solar_power_factor()
        }
    }


def get_comms_metadata(region_id: Optional[str] = None) -> dict:
    """
    Get communications metadata for HBCM run enrichment.

    Example:
        >>> metadata = get_comms_metadata(region_id='US-STL')
        >>> hbcm_run = {
        ...     "run_id": "hbcm_123",
        ...     "comms_context": metadata
        ... }
    """
    comms = get_comms_profile(region_id=region_id)
    return {
        "source": comms.source,
        "region_id": comms.region_id,
        "summary": {
            "latency_ms": comms.baseline_latency_ms,
            "jitter_ms": comms.jitter_ms,
            "packet_loss": comms.packet_loss_percent,
            "acceptable_for_realtime": comms.is_acceptable_for_realtime_control()
        }
    }
