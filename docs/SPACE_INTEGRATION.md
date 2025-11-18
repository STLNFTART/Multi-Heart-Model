# Space API Integration Guide

**Last Updated:** 2025-11-15
**Module:** `src/space_integration`
**Related Branches:** `claude/nasa-starlink-api-01WrjyTUaZvA3TpZLi67QCSG`

This document describes the clean architecture for integrating NASA and Starlink APIs with the Multi-Heart-Model system. The integration layer provides environmental context, communications profiles, and scenario generation while maintaining strict separation between external data providers and internal control kernels.

---

## Table of Contents

1. [Overview](#overview)
2. [Architectural Principles](#architectural-principles)
3. [Interface Boundary](#interface-boundary)
4. [Integration Functions](#integration-functions)
5. [FastAPI Endpoints](#fastapi-endpoints)
6. [Usage Patterns](#usage-patterns)
7. [Real-World Integration](#real-world-integration)
8. [Examples](#examples)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### Purpose

The space integration layer provides a **clean boundary** between external NASA/Starlink APIs and internal control systems. It serves three primary functions:

1. **Environmental Context**: Transform NASA POWER and EPIC data into actionable environmental parameters
2. **Communications Profiles**: Model network characteristics from Starlink metrics for control loop testing
3. **Scenario Generation**: Create stress-test scenarios from NASA NeoWs and SSD orbital data

### Key Principle

**CRITICAL**: The `api_integrations` package is a **pure data provider** and should NEVER be called from control kernels. All API access must go through the interface boundary defined in `src/space_integration`.

```
┌─────────────────────────────────────────────────────────────┐
│                    Control Kernels                          │
│  (HBCM, MotorHandPro, PrimalLogicProcessor, etc.)          │
│                   NEVER ACCESS APIs                         │
└─────────────────────────────────────────────────────────────┘
                          ↑
                          │ Domain Objects Only
                          │
┌─────────────────────────────────────────────────────────────┐
│              Interface Boundary (THIS LAYER)                │
│  EnvContext, CommsProfile, ScenarioConfig                   │
│  build_environment_context(), get_comms_profile(), etc.     │
└─────────────────────────────────────────────────────────────┘
                          ↑
                          │ API Calls (high-level only)
                          │
┌─────────────────────────────────────────────────────────────┐
│                  api_integrations/                          │
│  NASA POWER, EPIC, NeoWs, SSD, Starlink                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Architectural Principles

### 1. Clean Separation

**Rule**: Control kernels see domain objects, not raw API data.

```python
# CORRECT: Control kernel sees EnvContext
class DroneController:
    def __init__(self, env_context: EnvContext):
        self.thermal_stress = env_context.get_thermal_stress_factor()

    def control_loop(self, state):
        # Use self.thermal_stress
        # NEVER call api_integrations

# WRONG: Control kernel sees raw NASA POWER JSON
class DroneController:
    def __init__(self, nasa_power_json: dict):  # WRONG!
        # Now coupled to external API format
```

### 2. Lazy Initialization

**Rule**: API managers are initialized only when needed, with graceful fallbacks.

```python
_api_manager: Optional[APIManager] = None

def _get_api_manager() -> Optional[APIManager]:
    """Lazy initialization with fallback."""
    global _api_manager
    if _api_manager is None:
        try:
            from api_integrations import APIManager
            _api_manager = APIManager()
        except ImportError:
            return None  # Graceful fallback
    return _api_manager
```

### 3. Domain Transformation

**Rule**: Transform at the boundary, never leak external formats.

```python
# CORRECT: Transformation at boundary
@classmethod
def from_power(cls, power_data: Dict[str, Any], lat: float, lon: float,
               timestamp: datetime) -> 'EnvContext':
    """Transform NASA POWER API response to EnvContext."""
    params = power_data.get('properties', {}).get('parameter', {})
    return cls(
        latitude=lat,
        longitude=lon,
        timestamp=timestamp,
        global_horizontal_irradiance=params.get('ALLSKY_SFC_SW_DWN'),
        temperature_2m=params.get('T2M'),
        # ... domain-specific fields
        source='nasa_power'
    )
```

### 4. Fallback Strategies

**Rule**: Always provide synthetic/nominal fallbacks when real APIs unavailable.

```python
def build_environment_context(lat: float, lon: float,
                              timestamp: Optional[datetime] = None) -> EnvContext:
    """Build environmental context with fallback."""
    api = _get_api_manager()

    if api is None:
        # Fallback: synthetic data
        return EnvContext(
            latitude=lat,
            longitude=lon,
            timestamp=timestamp or datetime.now(timezone.utc),
            temperature_2m=293.15,  # 20°C
            source='synthetic'
        )

    try:
        power_data = api.nasa_power.get_hourly(...)
        return EnvContext.from_power(power_data, lat, lon, timestamp)
    except Exception as e:
        # Fallback on error
        return EnvContext(latitude=lat, longitude=lon, timestamp=timestamp,
                         temperature_2m=293.15, source='fallback')
```

---

## Interface Boundary

### EnvContext

**Purpose**: Environmental context from NASA POWER and EPIC data.

```python
@dataclass
class EnvContext:
    """Environmental context for control systems."""

    # Location and time
    latitude: float
    longitude: float
    timestamp: datetime

    # Solar radiation
    global_horizontal_irradiance: Optional[float] = None  # W/m²
    direct_normal_irradiance: Optional[float] = None      # W/m²
    diffuse_horizontal_irradiance: Optional[float] = None # W/m²

    # Temperature
    temperature_2m: Optional[float] = None                # K

    # Wind
    wind_speed: Optional[float] = None                    # m/s
    wind_direction: Optional[float] = None                # degrees

    # Other
    relative_humidity: Optional[float] = None             # %
    surface_pressure: Optional[float] = None              # kPa
    cloud_coverage: Optional[float] = None                # %

    # Earth imagery (from EPIC)
    earth_image_url: Optional[str] = None

    # Metadata
    source: str = 'unknown'  # 'nasa_power', 'synthetic', 'fallback'
    quality: str = 'unknown'  # 'high', 'medium', 'low'
```

**Key Methods**:

```python
def get_thermal_stress_factor(self) -> float:
    """
    Calculate thermal stress factor for control systems.

    Returns:
        float: 0.0 (no stress) to 1.0 (extreme stress)
    """
    if self.temperature_2m is None:
        return 0.0

    # Thermal stress based on deviation from nominal (20°C = 293.15K)
    nominal_temp_k = 293.15
    temp_deviation = abs(self.temperature_2m - nominal_temp_k)

    # Stress increases with temperature deviation
    # 0K deviation = 0.0 stress
    # 20K deviation = 0.5 stress
    # 40K+ deviation = 1.0 stress
    stress = min(1.0, temp_deviation / 40.0)
    return stress

def get_solar_power_factor(self) -> float:
    """
    Calculate solar power availability factor.

    Returns:
        float: 0.0 (night) to 1.0 (peak solar)
    """
    if self.global_horizontal_irradiance is None:
        return 0.0

    # Peak solar irradiance ~1000 W/m²
    peak_irradiance = 1000.0
    factor = min(1.0, self.global_horizontal_irradiance / peak_irradiance)
    return factor
```

**Construction**:

```python
# From NASA POWER API
env = EnvContext.from_power(power_data, lat=38.63, lon=-90.20, timestamp=now)

# Synthetic (for testing)
env = EnvContext.create_synthetic(lat=38.63, lon=-90.20, temperature_c=25.0)

# Serialization
env_dict = env.to_dict()
env_restored = EnvContext.from_dict(env_dict)
```

### CommsProfile

**Purpose**: Communications profile from Starlink metrics.

```python
@dataclass
class CommsProfile:
    """Communications profile for network modeling."""

    # Basic metrics
    baseline_latency_ms: float
    jitter_ms: float
    packet_loss_percent: float

    # Throughput
    download_mbps: Optional[float] = None
    upload_mbps: Optional[float] = None

    # Regional
    region_id: Optional[str] = None
    satellite_count: Optional[int] = None

    # Quality indicators
    signal_strength_db: Optional[float] = None
    snr_db: Optional[float] = None

    # Metadata
    source: str = 'unknown'  # 'starlink', 'nominal', 'degraded'
    timestamp: Optional[datetime] = None
```

**Key Methods**:

```python
def is_acceptable_for_realtime_control(self, max_latency_ms: float = 50.0,
                                       max_jitter_ms: float = 10.0,
                                       max_packet_loss_pct: float = 1.0) -> bool:
    """
    Check if communications profile meets real-time control requirements.

    Args:
        max_latency_ms: Maximum acceptable latency (default: 50ms)
        max_jitter_ms: Maximum acceptable jitter (default: 10ms)
        max_packet_loss_pct: Maximum acceptable packet loss (default: 1%)

    Returns:
        bool: True if acceptable for real-time control
    """
    return (
        self.baseline_latency_ms <= max_latency_ms and
        self.jitter_ms <= max_jitter_ms and
        self.packet_loss_percent <= max_packet_loss_pct
    )

def get_network_delay_distribution(self) -> Tuple[float, float]:
    """
    Get network delay distribution parameters for stochastic simulations.

    Returns:
        Tuple[float, float]: (mean_ms, std_ms)
    """
    mean_ms = self.baseline_latency_ms
    std_ms = self.jitter_ms / 2.0  # Approximate jitter as 2*std
    return mean_ms, std_ms
```

**Construction**:

```python
# From Starlink API
comms = CommsProfile.from_starlink(metrics_data, region_id='US-STL')

# Nominal (ideal conditions)
comms = CommsProfile.create_nominal()

# Degraded (stress testing)
comms = CommsProfile.create_degraded(severity=0.5)
```

### ScenarioConfig

**Purpose**: Scenario configuration from NASA NeoWs and SSD orbital data.

```python
@dataclass
class ScenarioConfig:
    """Scenario configuration for stress testing."""

    # Identification
    scenario_id: str
    description: str
    seed: int

    # Orbital elements
    orbital_elements: Optional[Dict[str, float]] = None

    # Near-Earth Object encounters
    neo_encounters: List[Dict[str, Any]] = field(default_factory=list)

    # Environmental stressors
    thermal_stress: float = 0.0  # 0.0-1.0
    radiation_stress: float = 0.0  # 0.0-1.0

    # Communications stressors
    comms_degradation: float = 0.0  # 0.0-1.0

    # Metadata
    source: str = 'unknown'  # 'nasa_neows', 'synthetic'
    timestamp: Optional[datetime] = None
```

**Key Methods**:

```python
def get_encounter_count(self) -> int:
    """Get number of NEO encounters in scenario."""
    return len(self.neo_encounters)

def get_max_threat_level(self) -> float:
    """
    Calculate maximum threat level from NEO encounters.

    Returns:
        float: 0.0 (no threat) to 1.0 (maximum threat)
    """
    if not self.neo_encounters:
        return 0.0

    # Threat based on miss distance (closer = higher threat)
    min_miss_distance = min(neo['miss_distance_km'] for neo in self.neo_encounters)

    # Normalize: 1M km = low threat, <100k km = high threat
    threat = max(0.0, min(1.0, 1.0 - (min_miss_distance - 100000) / 900000))
    return threat
```

**Construction**:

```python
# From NASA APIs
scenario = ScenarioConfig.from_nasa(neos_data, ssd_data, seed=42)

# Synthetic
scenario = ScenarioConfig.create_synthetic(seed=42, encounter_count=3)
```

---

## Integration Functions

### build_environment_context()

**Purpose**: Build environmental context from NASA POWER data.

**Signature**:
```python
def build_environment_context(
    lat: float,
    lon: float,
    timestamp: Optional[datetime] = None
) -> EnvContext
```

**Usage**:
```python
from src.space_integration import build_environment_context

# Get current environmental conditions for St. Louis, MO
env = build_environment_context(lat=38.63, lon=-90.20)

print(f"Temperature: {env.temperature_2m - 273.15:.1f}°C")
print(f"Solar GHI: {env.global_horizontal_irradiance} W/m²")
print(f"Thermal Stress: {env.get_thermal_stress_factor():.3f}")
```

**When to Call**:
- **Before control loop initialization** (high-level setup)
- **For HBCM metadata enrichment** (simulation context)
- **For configuration generation** (test scenarios)

**NEVER Call**:
- Inside control loops
- At high frequency (>1 Hz)
- From hardware control kernels

### get_comms_profile()

**Purpose**: Get communications profile from Starlink metrics or synthetic models.

**Signature**:
```python
def get_comms_profile(
    region_id: Optional[str] = None,
    severity: Optional[float] = None
) -> CommsProfile
```

**Usage**:
```python
from src.space_integration import get_comms_profile

# Get real Starlink metrics for a region
comms = get_comms_profile(region_id='US-STL')

# Get degraded profile for stress testing
comms = get_comms_profile(severity=0.5)  # 50% degradation

# Check if acceptable for real-time control
if comms.is_acceptable_for_realtime_control(max_latency_ms=50):
    print("Comms acceptable for real-time control")

# Get delay distribution for simulation
mean_ms, std_ms = comms.get_network_delay_distribution()
```

**When to Call**:
- **Before control loop initialization** (network modeling setup)
- **For stress test configuration** (degraded scenarios)
- **For simulation parameter generation** (delay modeling)

**NEVER Call**:
- Inside control loops
- For actual network I/O (use domain objects, not API)

### generate_space_scenario()

**Purpose**: Generate space scenario from NASA NeoWs and SSD data.

**Signature**:
```python
def generate_space_scenario(
    seed: int,
    use_real_data: bool = False
) -> ScenarioConfig
```

**Usage**:
```python
from src.space_integration import generate_space_scenario

# Generate synthetic scenario
scenario = generate_space_scenario(seed=42, use_real_data=False)

print(f"Scenario: {scenario.description}")
print(f"NEO Encounters: {scenario.get_encounter_count()}")
print(f"Max Threat: {scenario.get_max_threat_level():.3f}")

# Use in HBCM simulation
hbcm_metadata = {
    'run_id': 'hbcm_123',
    'scenario': scenario.to_dict()
}
```

**When to Call**:
- **Before simulation batch runs** (scenario setup)
- **For Monte Carlo testing** (varied conditions)
- **For safety envelope validation** (stress scenarios)

**NEVER Call**:
- Inside control loops
- During real-time operation

---

## FastAPI Endpoints

The space integration layer exposes three REST endpoints via FastAPI.

### POST /api/space/env-context

**Purpose**: Get environmental context from NASA POWER data.

**Request**:
```json
{
  "latitude": 38.63,
  "longitude": -90.20,
  "timestamp": "2025-11-15T12:00:00Z"  // optional
}
```

**Response**:
```json
{
  "latitude": 38.63,
  "longitude": -90.20,
  "timestamp": "2025-11-15T12:00:00Z",
  "global_horizontal_irradiance": 850.5,
  "temperature_2m": 293.15,
  "wind_speed": 5.2,
  "source": "nasa_power",
  "quality": "high",
  "derived": {
    "thermal_stress_factor": 0.0,
    "solar_power_factor": 0.85
  }
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/space/env-context \
  -H 'Content-Type: application/json' \
  -d '{"latitude": 38.63, "longitude": -90.20}'
```

### POST /api/space/comms-profile

**Purpose**: Get communications profile from Starlink metrics.

**Request**:
```json
{
  "region_id": "US-STL",     // optional
  "severity": 0.5            // optional, 0.0-1.0
}
```

**Response**:
```json
{
  "baseline_latency_ms": 35.0,
  "jitter_ms": 8.0,
  "packet_loss_percent": 0.5,
  "download_mbps": 150.0,
  "upload_mbps": 20.0,
  "region_id": "US-STL",
  "source": "starlink",
  "acceptable_for_realtime": true,
  "network_delay_distribution": {
    "mean_ms": 35.0,
    "std_ms": 4.0
  }
}
```

**cURL Example**:
```bash
# Get nominal profile
curl -X POST http://localhost:8000/api/space/comms-profile \
  -H 'Content-Type: application/json' \
  -d '{}'

# Get degraded profile
curl -X POST http://localhost:8000/api/space/comms-profile \
  -H 'Content-Type: application/json' \
  -d '{"severity": 0.3}'
```

### POST /api/space/scenario

**Purpose**: Generate space scenario from NASA NeoWs and SSD data.

**Request**:
```json
{
  "seed": 42,
  "use_real_data": false
}
```

**Response**:
```json
{
  "scenario_id": "scenario_42",
  "description": "Synthetic space scenario with 3 NEO encounters",
  "seed": 42,
  "neo_encounters": [
    {
      "name": "2023 AB1",
      "miss_distance_km": 150000.0,
      "velocity_kps": 15.2,
      "diameter_m": 250.0
    }
  ],
  "thermal_stress": 0.3,
  "radiation_stress": 0.2,
  "comms_degradation": 0.1,
  "source": "synthetic",
  "encounter_count": 3,
  "max_threat_level": 0.85
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/space/scenario \
  -H 'Content-Type: application/json' \
  -d '{"seed": 123, "use_real_data": false}'
```

### GET /api/space/health

**Purpose**: Health check for space integration endpoints.

**Response**:
```json
{
  "status": "healthy",
  "api_integration_available": true,
  "endpoints": [
    "/api/space/env-context",
    "/api/space/comms-profile",
    "/api/space/scenario"
  ]
}
```

---

## Usage Patterns

### CORRECT Pattern: High-Level Initialization

```python
"""
CORRECT: Call space integration at high level, before control loop.
"""
from src.space_integration import build_environment_context, get_comms_profile
from src.microprocessor import PrimalLogicProcessor
from src.integration import MotorHandBridge

# HIGH-LEVEL SETUP (before control loop)
env = build_environment_context(lat=38.63, lon=-90.20)
comms = get_comms_profile(region_id='US-STL')

# Extract parameters for control system
thermal_stress = env.get_thermal_stress_factor()
network_delay_mean_s = comms.baseline_latency_ms / 1000.0
network_delay_std_s = comms.jitter_ms / 2000.0

# Initialize control system with domain parameters
class DroneController:
    def __init__(self, env_context: EnvContext, comms_profile: CommsProfile):
        self.thermal_stress = env_context.get_thermal_stress_factor()
        self.network_delay_mean = comms_profile.baseline_latency_ms / 1000.0
        self.plp = PrimalLogicProcessor()

    def control_loop(self, state: dict) -> float:
        """
        Control loop uses pre-computed parameters.
        NEVER calls api_integrations.
        """
        # Adjust control gain based on thermal stress
        control_gain = 1.0 - 0.5 * self.thermal_stress

        # Compute control signal
        error = state['target'] - state['current']
        control = self.plp.compute_control(error, dt=0.001)
        control *= control_gain

        return control

# Create controller
controller = DroneController(env_context=env, comms_profile=comms)

# Run control loop (CLEAN - no API calls)
for t in range(1000):
    state = get_state()
    control = controller.control_loop(state)
    apply_control(control)
```

### INCORRECT Pattern: API Calls in Control Loop

```python
"""
WRONG: DO NOT DO THIS!
Calling api_integrations inside control loop destroys performance.
"""
from api_integrations import APIManager  # WRONG!

class DroneController:
    def __init__(self):
        self.api = APIManager()  # WRONG!

    def control_loop(self, state: dict) -> float:
        """WRONG: API call in control loop."""
        # WRONG: Slow API call at 1000 Hz!
        power_data = self.api.nasa_power.get_hourly(...)  # WRONG!
        temp = power_data['properties']['parameter']['T2M']  # WRONG!

        # WRONG: Now coupled to external API format
        # WRONG: Latency will destroy control loop performance
        # WRONG: No fallback if API fails

        control_gain = 1.0 - (temp - 273.15) / 100.0
        return control_gain * state['error']

# This will fail catastrophically in production!
```

### CORRECT Pattern: HBCM Metadata Enrichment

```python
"""
CORRECT: Use space integration for HBCM simulation metadata.
"""
from src.coupling import HeartBrainCouplingModel
from src.space_integration import (
    build_environment_context,
    get_comms_profile,
    generate_space_scenario
)

# Build context (high-level, before simulation)
env = build_environment_context(lat=38.63, lon=-90.20)
comms = get_comms_profile(region_id='US-STL')
scenario = generate_space_scenario(seed=42)

# Create HBCM simulation
hbcm = HeartBrainCouplingModel()

# Enrich metadata
simulation_metadata = {
    'run_id': 'hbcm_20251115_001',
    'timestamp': env.timestamp.isoformat(),
    'location': {'lat': env.latitude, 'lon': env.longitude},
    'environment': {
        'temperature_c': env.temperature_2m - 273.15 if env.temperature_2m else None,
        'solar_ghi': env.global_horizontal_irradiance,
        'thermal_stress': env.get_thermal_stress_factor(),
        'source': env.source
    },
    'communications': {
        'latency_ms': comms.baseline_latency_ms,
        'jitter_ms': comms.jitter_ms,
        'packet_loss_pct': comms.packet_loss_percent,
        'acceptable_for_realtime': comms.is_acceptable_for_realtime_control(),
        'source': comms.source
    },
    'scenario': {
        'id': scenario.scenario_id,
        'description': scenario.description,
        'neo_encounters': scenario.get_encounter_count(),
        'max_threat': scenario.get_max_threat_level()
    }
}

# Run simulation (CLEAN - uses pre-computed context)
trajectory = hbcm.simulate(
    initial_state=(0.0, 0.0, 1.0, 0.0),
    t_span=(0.0, 10.0),
    dt=0.001
)

# Save with metadata
results = {
    'metadata': simulation_metadata,
    'trajectory': trajectory
}
```

### CORRECT Pattern: MotorHandPro Network Delay Modeling

```python
"""
CORRECT: Use CommsProfile to model network delay in control testing.
"""
from src.integration import MotorHandBridge
from src.space_integration import get_comms_profile
import numpy as np

# Get communications profile (high-level, before test)
comms = get_comms_profile(severity=0.3)  # 30% degradation

# Extract network delay distribution
mean_delay_s, std_delay_s = comms.get_network_delay_distribution()
mean_delay_s /= 1000.0  # ms to s
std_delay_s /= 1000.0   # ms to s

# Configure test harness
class MotorHandTestHarness:
    def __init__(self, comms_profile: CommsProfile):
        self.bridge = MotorHandBridge(port='/dev/ttyUSB0')
        self.mean_delay = comms_profile.baseline_latency_ms / 1000.0
        self.std_delay = comms_profile.jitter_ms / 2000.0
        self.packet_loss = comms_profile.packet_loss_percent / 100.0

    def send_command_with_network_simulation(self, command: dict):
        """Simulate network effects on command transmission."""
        # Simulate packet loss
        if np.random.random() < self.packet_loss:
            # Packet lost, retry or timeout
            return None

        # Simulate network delay
        delay = np.random.normal(self.mean_delay, self.std_delay)
        delay = max(0.0, delay)  # Delay can't be negative

        # Sleep to simulate delay
        time.sleep(delay)

        # Send actual command
        return self.bridge.send_command(command)

# Run test
harness = MotorHandTestHarness(comms_profile=comms)
harness.send_command_with_network_simulation({'throttle': 128})
```

---

## Real-World Integration

### Integration with MotorHandPro

**Use Case**: Model Starlink network delay in MotorHandPro control loop testing.

```python
from src.integration import MotorHandBridge
from src.microprocessor import PrimalLogicProcessor
from src.space_integration import get_comms_profile

# Get communications profile for test region
comms = get_comms_profile(region_id='US-STL')

# Check if acceptable for real-time control
if not comms.is_acceptable_for_realtime_control(max_latency_ms=50):
    print("WARNING: Network latency too high for real-time control!")

# Extract delay parameters
mean_delay_ms, std_delay_ms = comms.get_network_delay_distribution()

# Use in simulation
# (See MotorHandPro integration documentation for full example)
```

### Integration with HBCM

**Use Case**: Add environmental context to HBCM simulation metadata.

```python
from src.coupling import HeartBrainCouplingModel
from src.space_integration import build_environment_context

# Get environmental context for simulation location
env = build_environment_context(lat=38.63, lon=-90.20)

# Create HBCM with environmental parameters
hbcm = HeartBrainCouplingModel()

# Store context in simulation metadata
metadata = {
    'environment': env.to_dict(),
    'thermal_stress': env.get_thermal_stress_factor(),
    'solar_power': env.get_solar_power_factor()
}

# Run simulation
# (See HBCM documentation for full example)
```

### Integration with Organ-On-Chip

**Use Case**: Vary environmental stress in drug toxicity screening.

```python
from src.organchip import OrganChipSuite
from src.space_integration import build_environment_context

# Get environmental context
env = build_environment_context(lat=38.63, lon=-90.20)

# Extract thermal stress factor
thermal_stress = env.get_thermal_stress_factor()

# Modify drug test parameters based on environmental stress
suite = OrganChipSuite()

# Adjust dose based on environmental stress
# (Higher stress = lower tolerance)
adjusted_dose = base_dose * (1.0 - 0.3 * thermal_stress)

results = suite.run_drug_test(
    drug_name="Doxorubicin",
    dose_mg_kg=adjusted_dose,
    duration_hours=48.0,
    dt_minutes=1.0
)
```

---

## Examples

### Example 1: Basic Environmental Context

```python
from src.space_integration import build_environment_context

# Get current environmental conditions
env = build_environment_context(lat=38.63, lon=-90.20)

# Display key parameters
print(f"Location: {env.latitude}, {env.longitude}")
print(f"Temperature: {env.temperature_2m - 273.15:.1f}°C")
print(f"Solar GHI: {env.global_horizontal_irradiance} W/m²")
print(f"Wind Speed: {env.wind_speed} m/s")

# Get derived parameters
thermal_stress = env.get_thermal_stress_factor()
solar_factor = env.get_solar_power_factor()

print(f"Thermal Stress: {thermal_stress:.3f} [0=no stress, 1=extreme]")
print(f"Solar Power: {solar_factor:.3f} [0=night, 1=peak]")
```

### Example 2: Communications Profile for Network Testing

```python
from src.space_integration import get_comms_profile

# Get nominal profile
comms_nominal = get_comms_profile()

print("Nominal Communications Profile:")
print(f"  Latency: {comms_nominal.baseline_latency_ms} ms")
print(f"  Jitter: {comms_nominal.jitter_ms} ms")
print(f"  Packet Loss: {comms_nominal.packet_loss_percent}%")

# Get degraded profile for stress testing
comms_degraded = get_comms_profile(severity=0.5)

print("\nDegraded Communications Profile (50% severity):")
print(f"  Latency: {comms_degraded.baseline_latency_ms} ms")
print(f"  Jitter: {comms_degraded.jitter_ms} ms")
print(f"  Packet Loss: {comms_degraded.packet_loss_percent}%")

# Check acceptability
acceptable = comms_degraded.is_acceptable_for_realtime_control(max_latency_ms=50)
print(f"\nAcceptable for Real-Time Control: {'YES' if acceptable else 'NO'}")

# Get delay distribution for simulation
mean_ms, std_ms = comms_degraded.get_network_delay_distribution()
print(f"Network Delay Distribution: μ={mean_ms:.1f}ms, σ={std_ms:.1f}ms")
```

### Example 3: Scenario Generation for Monte Carlo Testing

```python
from src.space_integration import generate_space_scenario
import numpy as np

# Generate 10 different scenarios for Monte Carlo testing
scenarios = []
for seed in range(10):
    scenario = generate_space_scenario(seed=seed, use_real_data=False)
    scenarios.append(scenario)

    print(f"\nScenario {seed}:")
    print(f"  Description: {scenario.description}")
    print(f"  NEO Encounters: {scenario.get_encounter_count()}")
    print(f"  Max Threat: {scenario.get_max_threat_level():.3f}")
    print(f"  Thermal Stress: {scenario.thermal_stress:.3f}")

# Run simulations with varied scenarios
for i, scenario in enumerate(scenarios):
    print(f"\nRunning simulation {i} with scenario: {scenario.scenario_id}")
    # ... run simulation with scenario parameters
```

### Example 4: Complete Demo

See `examples/space_integration_demo.py` for a comprehensive demonstration including:
- Environmental context usage
- Communications profile modeling
- Scenario generation
- Correct vs incorrect patterns
- FastAPI endpoint examples

Run it with:
```bash
python examples/space_integration_demo.py
```

---

## Testing

### Unit Tests

Test the interface boundary dataclasses and transformation methods:

```python
# tests/test_space_integration.py
import pytest
from datetime import datetime, timezone
from src.space_integration import EnvContext, CommsProfile, ScenarioConfig

def test_env_context_thermal_stress():
    """Test thermal stress calculation."""
    # Nominal temperature (20°C = 293.15K)
    env = EnvContext(
        latitude=38.63,
        longitude=-90.20,
        timestamp=datetime.now(timezone.utc),
        temperature_2m=293.15
    )

    assert env.get_thermal_stress_factor() == pytest.approx(0.0)

    # Extreme cold (-20°C = 253.15K)
    env.temperature_2m = 253.15
    assert env.get_thermal_stress_factor() == pytest.approx(1.0)

def test_comms_profile_acceptability():
    """Test real-time control acceptability check."""
    # Nominal profile
    comms = CommsProfile.create_nominal()
    assert comms.is_acceptable_for_realtime_control(max_latency_ms=50)

    # High latency profile
    comms.baseline_latency_ms = 100.0
    assert not comms.is_acceptable_for_realtime_control(max_latency_ms=50)

def test_scenario_threat_level():
    """Test threat level calculation."""
    scenario = ScenarioConfig.create_synthetic(seed=42, encounter_count=1)
    threat = scenario.get_max_threat_level()
    assert 0.0 <= threat <= 1.0
```

### Integration Tests

Test the integration functions with fallback behavior:

```python
# tests/integration/test_space_integration.py
from src.space_integration import (
    build_environment_context,
    get_comms_profile,
    generate_space_scenario
)

def test_build_environment_context_fallback():
    """Test that environment context builds with fallback."""
    env = build_environment_context(lat=38.63, lon=-90.20)

    assert env.latitude == 38.63
    assert env.longitude == -90.20
    assert env.source in ['nasa_power', 'synthetic', 'fallback']

def test_get_comms_profile_nominal():
    """Test nominal communications profile."""
    comms = get_comms_profile()

    assert comms.baseline_latency_ms > 0
    assert comms.source in ['starlink', 'nominal', 'degraded']

def test_generate_space_scenario_synthetic():
    """Test synthetic scenario generation."""
    scenario = generate_space_scenario(seed=42, use_real_data=False)

    assert scenario.seed == 42
    assert scenario.source == 'synthetic'
```

### API Endpoint Tests

Test FastAPI endpoints:

```python
# tests/test_space_routes.py
from fastapi.testclient import TestClient
from web_control_panel.backend.main import app

client = TestClient(app)

def test_env_context_endpoint():
    """Test environment context endpoint."""
    response = client.post(
        "/api/space/env-context",
        json={"latitude": 38.63, "longitude": -90.20}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['latitude'] == 38.63
    assert data['longitude'] == -90.20
    assert 'thermal_stress_factor' in data.get('derived', {})

def test_comms_profile_endpoint():
    """Test communications profile endpoint."""
    response = client.post(
        "/api/space/comms-profile",
        json={"severity": 0.5}
    )

    assert response.status_code == 200
    data = response.json()
    assert 'baseline_latency_ms' in data
    assert 'acceptable_for_realtime' in data

def test_scenario_endpoint():
    """Test scenario generation endpoint."""
    response = client.post(
        "/api/space/scenario",
        json={"seed": 42, "use_real_data": False}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['seed'] == 42
    assert 'encounter_count' in data
```

---

## Troubleshooting

### Issue: ImportError for api_integrations

**Symptom**:
```
ImportError: No module named 'api_integrations'
```

**Cause**: The `api_integrations` package is not installed or not in Python path.

**Solution**: The integration layer gracefully falls back to synthetic data. No action needed unless you specifically want real API data.

**To enable real APIs**:
1. Ensure `api_integrations/` is in your Python path
2. Or install as package: `pip install -e /path/to/api_integrations`

### Issue: NASA POWER API Rate Limiting

**Symptom**:
```
ERROR: NASA POWER API returned 429 Too Many Requests
```

**Cause**: Exceeded NASA POWER API rate limits.

**Solution**: The integration layer automatically falls back to synthetic data. To reduce API calls:
- Cache `EnvContext` results (they don't change rapidly)
- Use synthetic data for testing
- Call `build_environment_context()` at low frequency (<1/minute)

### Issue: Network Timeout

**Symptom**:
```
ERROR: Network timeout calling NASA POWER API
```

**Cause**: Network connectivity issues or slow API response.

**Solution**: The integration layer automatically falls back to synthetic data. The system continues operating normally.

### Issue: Incorrect Thermal Stress

**Symptom**: Thermal stress factor doesn't match expected environmental conditions.

**Cause**: Temperature units mismatch (K vs °C).

**Solution**: All temperatures in `EnvContext` are in Kelvin (K). Convert to Celsius:
```python
temp_c = env.temperature_2m - 273.15
```

### Issue: Communications Profile Too Degraded

**Symptom**: `is_acceptable_for_realtime_control()` always returns False.

**Cause**: Severity parameter too high, or max_latency_ms too strict.

**Solution**: Adjust severity or thresholds:
```python
# Less degradation
comms = get_comms_profile(severity=0.2)  # 20% instead of 50%

# More lenient thresholds
acceptable = comms.is_acceptable_for_realtime_control(
    max_latency_ms=100,  # Allow 100ms instead of 50ms
    max_packet_loss_pct=2.0  # Allow 2% instead of 1%
)
```

---

## Summary

### Key Takeaways

1. **Clean Separation**: `api_integrations` is NEVER called from control kernels
2. **Interface Boundary**: EnvContext, CommsProfile, ScenarioConfig sit between external APIs and internal systems
3. **Lazy Initialization**: APIs loaded only when needed, with graceful fallbacks
4. **Domain Transformation**: Raw API data → domain objects at boundary
5. **High-Level Only**: Integration functions called before control loops, not inside them
6. **FastAPI Exposure**: Minimal REST endpoints for external access
7. **Metadata Enrichment**: Use for HBCM simulation context, not real-time control

### Architecture Benefits

- **Performance**: No API calls in control loops
- **Testability**: Easy to test with synthetic data
- **Robustness**: Graceful fallbacks when APIs unavailable
- **Maintainability**: Clean separation of concerns
- **Extensibility**: Easy to add new data sources

### Related Documentation

- `examples/space_integration_demo.py` - Comprehensive demonstration
- `src/space_integration/` - Source code
- `web_control_panel/backend/space_routes.py` - FastAPI endpoints
- `docs/ARCHITECTURE_OVERVIEW.md` - Overall system architecture
- `docs/QUICK_REFERENCE.md` - Parameter quick reference

---

**Document Maintained By:** Multi-Heart-Model Team
**For Questions:** See examples or source code documentation
**Last Updated:** 2025-11-15
