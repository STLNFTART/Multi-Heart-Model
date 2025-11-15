"""
Space API Integration Routes

FastAPI endpoints for accessing space data (environment, communications, scenarios)
via the clean interface layer.

These endpoints provide minimal surface for Node-RED flows, web panels, and MCP tools.

Author: Multi-Heart-Model Team
Date: 2025-11-15
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.space_integration import (
        build_environment_context,
        get_comms_profile,
        generate_space_scenario,
        EnvContext,
        CommsProfile,
        ScenarioConfig
    )
    SPACE_INTEGRATION_AVAILABLE = True
except ImportError:
    SPACE_INTEGRATION_AVAILABLE = False

router = APIRouter(prefix="/api/space", tags=["space"])


# =============================================================================
# Pydantic Models for API
# =============================================================================

class EnvironmentRequest(BaseModel):
    """Request for environment context."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    timestamp: Optional[str] = Field(None, description="ISO timestamp (default: now)")


class EnvironmentResponse(BaseModel):
    """Response with environment context."""
    location: list[float]
    timestamp: str
    solar: Dict[str, Optional[float]]
    temperature: Dict[str, Optional[float]]
    wind: Dict[str, Optional[float]]
    pressure: Optional[float]
    humidity: Optional[float]
    source: str
    quality: str
    derived: Dict[str, float] = Field(default_factory=dict)


class CommsRequest(BaseModel):
    """Request for communications profile."""
    region_id: Optional[str] = Field(None, description="Region ID (e.g., 'US-STL')")
    severity: Optional[float] = Field(None, ge=0, le=1, description="Degradation severity (0=nominal, 1=worst)")


class CommsResponse(BaseModel):
    """Response with communications profile."""
    latency: Dict[str, float]
    reliability: Dict[str, Optional[float]]
    bandwidth: Dict[str, Optional[float]]
    region_id: Optional[str]
    satellite_count: Optional[int]
    source: str
    timestamp: Optional[str]
    derived: Dict[str, Any] = Field(default_factory=dict)


class ScenarioRequest(BaseModel):
    """Request for scenario generation."""
    seed: int = Field(42, description="Random seed for reproducibility")
    use_real_data: bool = Field(False, description="Use real NASA data vs synthetic")


class ScenarioResponse(BaseModel):
    """Response with scenario configuration."""
    scenario_id: str
    seed: int
    description: str
    orbital_elements: Optional[Dict[str, float]]
    neo_encounters: list[Dict[str, Any]]
    stress_factors: Dict[str, Optional[float]]
    source: str
    generated_at: str
    derived: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Environment Context Endpoints
# =============================================================================

@router.post("/env-context", response_model=EnvironmentResponse)
async def get_environment_context(request: EnvironmentRequest):
    """
    Get environmental context from NASA POWER data.

    This endpoint provides solar irradiance, temperature, wind, and other
    environmental parameters for a given location and time.

    **Use Cases:**
    - Drone/UAV environment modeling
    - AV road condition priors
    - Energy/thermal models
    - HBCM run metadata enrichment

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/space/env-context \\
      -H 'Content-Type: application/json' \\
      -d '{
        "latitude": 38.63,
        "longitude": -90.20
      }'
    ```
    """
    if not SPACE_INTEGRATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Space integration not available (api_integrations package required)"
        )

    try:
        # Parse timestamp if provided
        timestamp = None
        if request.timestamp:
            timestamp = datetime.fromisoformat(request.timestamp)

        # Get environment context
        env = build_environment_context(
            lat=request.latitude,
            lon=request.longitude,
            timestamp=timestamp
        )

        # Build response
        response = EnvironmentResponse(
            **env.to_dict(),
            derived={
                'thermal_stress_factor': env.get_thermal_stress_factor(),
                'solar_power_factor': env.get_solar_power_factor()
            }
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get environment context: {str(e)}")


@router.get("/env-context")
async def get_environment_context_simple(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude")
):
    """
    Get environmental context (simple query parameter version).

    **Example:**
    ```bash
    curl http://localhost:8000/api/space/env-context?lat=38.63&lon=-90.20
    ```
    """
    request = EnvironmentRequest(latitude=lat, longitude=lon)
    return await get_environment_context(request)


# =============================================================================
# Communications Profile Endpoints
# =============================================================================

@router.post("/comms-profile", response_model=CommsResponse)
async def get_communications_profile(request: CommsRequest):
    """
    Get communications profile from Starlink metrics.

    This endpoint provides network latency, jitter, packet loss, and bandwidth
    information for a given region or degradation level.

    **Use Cases:**
    - Network delay modeling in control loops
    - Communication window scheduling
    - Worst-case blackout bounds
    - Real-time control validation

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/space/comms-profile \\
      -H 'Content-Type: application/json' \\
      -d '{
        "region_id": "US-STL"
      }'
    ```

    **Degraded Profile Example:**
    ```bash
    curl -X POST http://localhost:8000/api/space/comms-profile \\
      -H 'Content-Type: application/json' \\
      -d '{
        "severity": 0.7
      }'
    ```
    """
    if not SPACE_INTEGRATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Space integration not available (api_integrations package required)"
        )

    try:
        # Get communications profile
        comms = get_comms_profile(
            region_id=request.region_id,
            severity=request.severity
        )

        # Build response
        mean_ms, std_ms = comms.get_network_delay_distribution()

        response = CommsResponse(
            **comms.to_dict(),
            derived={
                'network_delay_mean_ms': mean_ms,
                'network_delay_std_ms': std_ms,
                'acceptable_for_realtime_control': comms.is_acceptable_for_realtime_control(),
                'acceptable_for_50ms_control': comms.is_acceptable_for_realtime_control(max_latency_ms=50)
            }
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comms profile: {str(e)}")


@router.get("/comms-profile")
async def get_communications_profile_simple(
    region_id: Optional[str] = Query(None, description="Region ID"),
    severity: Optional[float] = Query(None, ge=0, le=1, description="Degradation severity")
):
    """
    Get communications profile (simple query parameter version).

    **Examples:**
    ```bash
    # Get nominal profile
    curl http://localhost:8000/api/space/comms-profile

    # Get regional profile
    curl http://localhost:8000/api/space/comms-profile?region_id=US-STL

    # Get degraded profile
    curl http://localhost:8000/api/space/comms-profile?severity=0.5
    ```
    """
    request = CommsRequest(region_id=region_id, severity=severity)
    return await get_communications_profile(request)


# =============================================================================
# Scenario Generation Endpoints
# =============================================================================

@router.post("/scenario", response_model=ScenarioResponse)
async def generate_scenario(request: ScenarioRequest):
    """
    Generate space scenario from NASA NeoWs and SSD data.

    This endpoint creates scenario configurations for stress testing control
    systems under rare, high-variance conditions.

    **Use Cases:**
    - Stress test control under extreme conditions
    - Unified control framework demos (orbital → AV → drone → MotorHandPro)
    - Validation narratives
    - Scenario generation for Primal Logic sims

    **Example (Synthetic):**
    ```bash
    curl -X POST http://localhost:8000/api/space/scenario \\
      -H 'Content-Type: application/json' \\
      -d '{
        "seed": 42,
        "use_real_data": false
      }'
    ```

    **Example (Real NASA Data):**
    ```bash
    curl -X POST http://localhost:8000/api/space/scenario \\
      -H 'Content-Type: application/json' \\
      -d '{
        "seed": 123,
        "use_real_data": true
      }'
    ```
    """
    if not SPACE_INTEGRATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Space integration not available (api_integrations package required)"
        )

    try:
        # Generate scenario
        scenario = generate_space_scenario(
            seed=request.seed,
            use_real_data=request.use_real_data
        )

        # Build response
        response = ScenarioResponse(
            **scenario.to_dict(),
            derived={
                'encounter_count': scenario.get_encounter_count(),
                'closest_approach_km': scenario.get_closest_approach_km()
            }
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate scenario: {str(e)}")


@router.get("/scenario")
async def generate_scenario_simple(
    seed: int = Query(42, description="Random seed"),
    use_real_data: bool = Query(False, description="Use real NASA data")
):
    """
    Generate space scenario (simple query parameter version).

    **Example:**
    ```bash
    curl http://localhost:8000/api/space/scenario?seed=42&use_real_data=false
    ```
    """
    request = ScenarioRequest(seed=seed, use_real_data=use_real_data)
    return await generate_scenario(request)


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def space_health():
    """
    Check space integration health.

    Returns:
    - available: Whether api_integrations package is available
    - timestamp: Current server time
    """
    return {
        "available": SPACE_INTEGRATION_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/space/env-context",
            "/api/space/comms-profile",
            "/api/space/scenario"
        ]
    }
