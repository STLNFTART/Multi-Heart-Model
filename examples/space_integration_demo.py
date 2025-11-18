#!/usr/bin/env python3
"""
Space Integration Demo

Demonstrates proper usage of the space integration layer:
1. EnvContext for environmental parameters
2. CommsProfile for network modeling
3. ScenarioConfig for stress testing

Key Principle: api_integrations is NEVER called from control kernels.
This example shows the clean boundary between external data and internal systems.

Author: Multi-Heart-Model Team
Date: 2025-11-15
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 70)
print("Space Integration Demo")
print("=" * 70)
print()

# =============================================================================
# Part 1: Environment Context
# =============================================================================

print("Part 1: Environment Context")
print("-" * 70)

from src.space_integration import build_environment_context

# Get environmental data for St. Louis, MO
lat, lon = 38.63, -90.20

print(f"Location: {lat}, {lon} (St. Louis, MO)")
print()

# HIGH-LEVEL CALL (not in control loop)
env_context = build_environment_context(lat, lon)

print(f"Source: {env_context.source}")
print(f"Temperature: {env_context.temperature_2m} K")
if env_context.temperature_2m:
    temp_c = env_context.temperature_2m - 273.15
    print(f"             {temp_c:.1f} °C")

print(f"Solar GHI: {env_context.global_horizontal_irradiance} W/m²")
print(f"Wind Speed: {env_context.wind_speed} m/s")
print()

# Derived parameters for control systems
thermal_stress = env_context.get_thermal_stress_factor()
solar_factor = env_context.get_solar_power_factor()

print("Derived Parameters (for control systems):")
print(f"  Thermal Stress Factor: {thermal_stress:.3f} [0=no stress, 1=extreme]")
print(f"  Solar Power Factor:    {solar_factor:.3f} [0=night, 1=peak solar]")
print()

# Export for HBCM metadata
env_metadata = env_context.to_dict()
print("HBCM Metadata Example:")
print(f"  {{'run_id': 'hbcm_123', 'environment_context': {env_metadata}}}")
print()

# =============================================================================
# Part 2: Communications Profile
# =============================================================================

print("\nPart 2: Communications Profile")
print("-" * 70)

from src.space_integration import get_comms_profile

# Get nominal communications profile
print("Nominal Profile (ideal conditions):")
comms_nominal = get_comms_profile(region_id=None, severity=None)

print(f"  Baseline Latency: {comms_nominal.baseline_latency_ms} ms")
print(f"  Jitter:           {comms_nominal.jitter_ms} ms")
print(f"  Packet Loss:      {comms_nominal.packet_loss_percent}%")
print(f"  Source:           {comms_nominal.source}")
print()

# Get degraded profile for stress testing
print("Degraded Profile (50% severity):")
comms_degraded = get_comms_profile(severity=0.5)

print(f"  Baseline Latency: {comms_degraded.baseline_latency_ms} ms")
print(f"  Jitter:           {comms_degraded.jitter_ms} ms")
print(f"  Packet Loss:      {comms_degraded.packet_loss_percent}%")
print()

# Check acceptability for real-time control
acceptable_nominal = comms_nominal.is_acceptable_for_realtime_control(max_latency_ms=50)
acceptable_degraded = comms_degraded.is_acceptable_for_realtime_control(max_latency_ms=50)

print("Acceptable for Real-Time Control (<50ms latency)?")
print(f"  Nominal:  {'YES' if acceptable_nominal else 'NO'}")
print(f"  Degraded: {'YES' if acceptable_degraded else 'NO'}")
print()

# Get network delay distribution for stochastic simulations
mean_ms, std_ms = comms_degraded.get_network_delay_distribution()
print("Network Delay Distribution (for simulation):")
print(f"  Mean: {mean_ms:.1f} ms")
print(f"  Std:  {std_ms:.1f} ms")
print()

# =============================================================================
# Part 3: Scenario Generation
# =============================================================================

print("\nPart 3: Scenario Generation")
print("-" * 70)

from src.space_integration import generate_space_scenario

# Generate synthetic scenario
print("Synthetic Scenario (seed=42):")
scenario_synthetic = generate_space_scenario(seed=42, use_real_data=False)

print(f"  Scenario ID:   {scenario_synthetic.scenario_id}")
print(f"  Description:   {scenario_synthetic.description}")
print(f"  NEO Encounters: {scenario_synthetic.get_encounter_count()}")
print(f"  Thermal Stress: {scenario_synthetic.thermal_stress:.2f}")
print(f"  Source:         {scenario_synthetic.source}")
print()

if scenario_synthetic.neo_encounters:
    print("  Sample NEO Encounter:")
    neo = scenario_synthetic.neo_encounters[0]
    print(f"    Name:           {neo['name']}")
    print(f"    Miss Distance:  {neo['miss_distance_km']:.0f} km")
    print(f"    Velocity:       {neo['velocity_kps']:.2f} km/s")
    print()

# =============================================================================
# Part 4: Usage in Control Systems (Proper Pattern)
# =============================================================================

print("\nPart 4: Proper Usage in Control Systems")
print("-" * 70)
print()

print("CORRECT Pattern:")
print("""
# HIGH-LEVEL, before control loop
from src.space_integration import build_environment_context, get_comms_profile

env = build_environment_context(lat=38.63, lon=-90.20)
comms = get_comms_profile(region_id='US-STL')

# Pass to control initialization
class DroneController:
    def __init__(self, env_context, comms_profile):
        self.thermal_stress = env_context.get_thermal_stress_factor()
        self.network_delay_mean = comms_profile.baseline_latency_ms / 1000.0  # s

    def control_loop(self, state):
        # Use thermal_stress in control logic
        # Use network_delay_mean for timing
        # NEVER call api_integrations here
        pass

controller = DroneController(env_context=env, comms_profile=comms)
""")

print("\nINCORRECT Pattern (DO NOT DO THIS):")
print("""
# WRONG: Calling api_integrations inside control loop
class DroneController:
    def control_loop(self, state):
        from api_integrations import APIManager  # WRONG!
        api = APIManager()
        power = api.nasa_power.get_hourly(...)  # WRONG! Slow API call in loop
        # This will destroy control loop performance
""")

# =============================================================================
# Part 5: Integration with FastAPI Endpoints
# =============================================================================

print("\nPart 5: FastAPI Endpoint Usage")
print("-" * 70)
print()

print("The space integration layer is exposed via FastAPI endpoints:")
print()
print("1. Environment Context:")
print("   POST http://localhost:8000/api/space/env-context")
print("   Body: {\"latitude\": 38.63, \"longitude\": -90.20}")
print()
print("2. Communications Profile:")
print("   GET http://localhost:8000/api/space/comms-profile?region_id=US-STL")
print("   GET http://localhost:8000/api/space/comms-profile?severity=0.5")
print()
print("3. Scenario Generation:")
print("   POST http://localhost:8000/api/space/scenario")
print("   Body: {\"seed\": 42, \"use_real_data\": false}")
print()

print("Example curl commands:")
print()
print("# Get environment context")
print("curl -X POST http://localhost:8000/api/space/env-context \\")
print("  -H 'Content-Type: application/json' \\")
print("  -d '{\"latitude\": 38.63, \"longitude\": -90.20}'")
print()
print("# Get comms profile")
print("curl http://localhost:8000/api/space/comms-profile?severity=0.3")
print()
print("# Generate scenario")
print("curl -X POST http://localhost:8000/api/space/scenario \\")
print("  -H 'Content-Type: application/json' \\")
print("  -d '{\"seed\": 123, \"use_real_data\": false}'")
print()

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
print()

print("Key Takeaways:")
print()
print("1. api_integrations = Pure data provider")
print("   - NEVER called from control loops")
print("   - Only called from high-level integration functions")
print()
print("2. Interface Layer = Clean boundary")
print("   - EnvContext, CommsProfile, ScenarioConfig")
print("   - Domain-specific dataclasses")
print("   - Transformation functions")
print()
print("3. Control Systems = Domain objects only")
print("   - See EnvContext, not raw NASA POWER JSON")
print("   - See CommsProfile, not raw Starlink JSON")
print("   - See ScenarioConfig, not raw NeoWs/SSD JSON")
print()
print("4. FastAPI Endpoints = Minimal surface")
print("   - /api/space/env-context")
print("   - /api/space/comms-profile")
print("   - /api/space/scenario")
print()
print("This architecture keeps external data separate from control kernels,")
print("ensuring performance, testability, and clean separation of concerns.")
print()
