"""
Multi-Heart-Model Web Control Panel Backend

FastAPI application with WebSocket support for real-time control and visualization.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters
from src.microprocessor import PrimalLogicProcessor
from bci_integration.data_acquisition.bci_adapter_base import CircularBuffer


# =============================================================================
# Pydantic Models
# =============================================================================

class SimulationConfig(BaseModel):
    """Configuration for HBCM simulation."""
    initial_state: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 0.0)
    t_start: float = 0.0
    t_end: float = 10.0
    dt: float = 0.001
    neural_params: Dict[str, float] = Field(default_factory=lambda: {
        'a': 0.7, 'b': 0.8, 'c': 3.0, 'stimulus_amplitude': 0.5
    })
    cardiac_params: Dict[str, float] = Field(default_factory=lambda: {
        'mu': 1.5, 'omega': 1.0, 'damping': 0.1
    })
    coupling_params: Dict[str, float] = Field(default_factory=lambda: {
        'neural_to_cardiac_gain': 0.5,
        'cardiac_to_neural_gain': 0.3,
        'neural_to_cardiac_delay': 0.12,
        'cardiac_to_neural_delay': 0.15
    })


class BCIConfig(BaseModel):
    """Configuration for BCI integration."""
    adapter_type: str = "openbci"  # openbci, lsl, synthetic
    port: Optional[str] = None
    board_type: Optional[str] = "cyton"
    n_channels: int = 8
    sampling_rate: float = 250.0
    enable_lsl: bool = True
    stream_name: Optional[str] = "MultiHeartModel_BCI"


class SystemStatus(BaseModel):
    """System status information."""
    is_running: bool = False
    simulation_time: float = 0.0
    bci_connected: bool = False
    bci_streaming: bool = False
    n_active_websockets: int = 0
    uptime_seconds: float = 0.0
    last_update: str = ""


class ControlCommand(BaseModel):
    """Control command for system manipulation."""
    command: str  # start, stop, pause, resume, reset, update_params
    parameters: Optional[Dict[str, Any]] = None


# =============================================================================
# WebSocket Connection Manager
# =============================================================================

class ConnectionManager:
    """Manages WebSocket connections for real-time data streaming."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_ids: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_ids[websocket] = client_id
        print(f"WebSocket connected: {client_id} (Total: {len(self.active_connections)})")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            client_id = self.connection_ids.get(websocket, "unknown")
            self.active_connections.remove(websocket)
            if websocket in self.connection_ids:
                del self.connection_ids[websocket]
            print(f"WebSocket disconnected: {client_id} (Total: {len(self.active_connections)})")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending to websocket: {e}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Broadcast error: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    @property
    def n_connections(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# =============================================================================
# System State Manager
# =============================================================================

class SystemState:
    """Manages the state of the Multi-Heart-Model system."""

    def __init__(self):
        # HBCM components
        self.hbcm: Optional[HeartBrainCouplingModel] = None
        self.config: Optional[SimulationConfig] = None

        # BCI components
        self.bci_adapter = None
        self.bci_buffer: Optional[CircularBuffer] = None
        self.lsl_bridge = None

        # Simulation state
        self.is_running = False
        self.is_paused = False
        self.current_time = 0.0
        self.current_state = (0.0, 0.0, 1.0, 0.0)
        self.trajectory = []

        # Data buffers for visualization
        self.time_buffer = []
        self.neural_buffer = []
        self.cardiac_buffer = []
        self.max_buffer_size = 10000

        # System metrics
        self.start_time = time.time()
        self.last_update_time = time.time()

    def initialize_hbcm(self, config: SimulationConfig):
        """Initialize HBCM with given configuration."""
        self.config = config

        # Create neural model
        neural_model = FitzHughNagumo(**config.neural_params)

        # Create cardiac model
        cardiac_model = VanDerPolOscillator(**config.cardiac_params)

        # Create coupling
        coupling = CouplingParameters(**config.coupling_params)

        # Create HBCM
        self.hbcm = HeartBrainCouplingModel(
            neural_model=neural_model,
            cardiac_model=cardiac_model,
            coupling=coupling
        )

        # Reset state
        self.current_state = config.initial_state
        self.current_time = config.t_start
        self.trajectory = []
        self.clear_buffers()

        print("HBCM initialized")

    def initialize_bci(self, config: BCIConfig):
        """Initialize BCI adapter."""
        try:
            if config.adapter_type == "openbci":
                from bci_integration.data_acquisition.openbci_adapter import OpenBCIAdapter
                self.bci_adapter = OpenBCIAdapter(
                    port=config.port,
                    board_type=config.board_type
                )
            elif config.adapter_type == "synthetic":
                # Use synthetic data generator
                from bci_integration.data_acquisition.synthetic_adapter import SyntheticAdapter
                self.bci_adapter = SyntheticAdapter(
                    n_channels=config.n_channels,
                    sampling_rate=config.sampling_rate
                )
            else:
                raise ValueError(f"Unknown adapter type: {config.adapter_type}")

            # Connect to BCI
            if self.bci_adapter.connect():
                # Initialize buffer
                self.bci_buffer = CircularBuffer(
                    n_channels=config.n_channels,
                    buffer_duration=5.0,
                    sampling_rate=config.sampling_rate
                )

                # Set up LSL bridge if enabled
                if config.enable_lsl:
                    from bci_integration.streaming.lsl_streamer import LSLBridge
                    self.lsl_bridge = LSLBridge(
                        self.bci_adapter,
                        stream_name=config.stream_name or "MultiHeartModel_BCI"
                    )
                    self.lsl_bridge.start()

                print(f"BCI initialized: {config.adapter_type}")
                return True
            else:
                print("Failed to connect to BCI")
                return False

        except Exception as e:
            print(f"BCI initialization error: {e}")
            return False

    def step_simulation(self):
        """Advance simulation by one timestep."""
        if self.hbcm is None or self.config is None:
            return

        # Get next state
        new_state = self.hbcm.step(
            self.current_time,
            self.current_state,
            self.config.dt
        )

        # Update state
        self.current_state = new_state
        self.current_time += self.config.dt

        # Add to trajectory
        self.trajectory.append((self.current_time, new_state))

        # Update buffers
        self.time_buffer.append(self.current_time)
        self.neural_buffer.append((new_state[0], new_state[1]))
        self.cardiac_buffer.append((new_state[2], new_state[3]))

        # Limit buffer sizes
        if len(self.time_buffer) > self.max_buffer_size:
            self.time_buffer.pop(0)
            self.neural_buffer.pop(0)
            self.cardiac_buffer.pop(0)

        self.last_update_time = time.time()

    def clear_buffers(self):
        """Clear visualization buffers."""
        self.time_buffer.clear()
        self.neural_buffer.clear()
        self.cardiac_buffer.clear()

    def get_status(self) -> SystemStatus:
        """Get current system status."""
        return SystemStatus(
            is_running=self.is_running,
            simulation_time=self.current_time,
            bci_connected=self.bci_adapter is not None and hasattr(self.bci_adapter, 'board') and self.bci_adapter.board is not None,
            bci_streaming=self.bci_adapter is not None and self.bci_adapter.is_streaming,
            n_active_websockets=0,  # Updated by connection manager
            uptime_seconds=time.time() - self.start_time,
            last_update=datetime.now().isoformat()
        )

    def get_latest_data(self, n_points: int = 1000) -> Dict[str, Any]:
        """Get latest simulation data for visualization."""
        # Limit to last n_points
        start_idx = max(0, len(self.time_buffer) - n_points)

        return {
            'time': self.time_buffer[start_idx:],
            'neural': {
                'v': [v for v, w in self.neural_buffer[start_idx:]],
                'w': [w for v, w in self.neural_buffer[start_idx:]]
            },
            'cardiac': {
                'x': [x for x, y in self.cardiac_buffer[start_idx:]],
                'y': [y for x, y in self.cardiac_buffer[start_idx:]]
            },
            'current_state': {
                'neural_v': self.current_state[0],
                'neural_w': self.current_state[1],
                'cardiac_x': self.current_state[2],
                'cardiac_y': self.current_state[3]
            },
            'timestamp': time.time()
        }


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Multi-Heart-Model Control Panel",
    description="Real-time control and visualization for BCI-integrated heart-brain coupling model",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
system_state = SystemState()
connection_manager = ConnectionManager()


# =============================================================================
# REST API Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Multi-Heart-Model Control Panel API",
        "version": "1.0.0",
        "endpoints": {
            "status": "/api/status",
            "config": "/api/config",
            "control": "/api/control",
            "data": "/api/data",
            "websocket": "/ws/{client_id}"
        }
    }


@app.get("/api/status")
async def get_status():
    """Get current system status."""
    status = system_state.get_status()
    status.n_active_websockets = connection_manager.n_connections
    return status


@app.post("/api/config/simulation")
async def configure_simulation(config: SimulationConfig):
    """Configure HBCM simulation parameters."""
    try:
        system_state.initialize_hbcm(config)
        return {"status": "success", "message": "Simulation configured"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/bci")
async def configure_bci(config: BCIConfig):
    """Configure BCI adapter."""
    try:
        success = system_state.initialize_bci(config)
        if success:
            return {"status": "success", "message": "BCI configured and connected"}
        else:
            raise HTTPException(status_code=500, detail="BCI connection failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/control")
async def control_system(command: ControlCommand):
    """Send control command to system."""
    try:
        if command.command == "start":
            if system_state.hbcm is None:
                raise HTTPException(status_code=400, detail="Simulation not configured")
            system_state.is_running = True
            system_state.is_paused = False
            return {"status": "success", "message": "Simulation started"}

        elif command.command == "stop":
            system_state.is_running = False
            return {"status": "success", "message": "Simulation stopped"}

        elif command.command == "pause":
            system_state.is_paused = True
            return {"status": "success", "message": "Simulation paused"}

        elif command.command == "resume":
            system_state.is_paused = False
            return {"status": "success", "message": "Simulation resumed"}

        elif command.command == "reset":
            if system_state.config:
                system_state.initialize_hbcm(system_state.config)
            return {"status": "success", "message": "Simulation reset"}

        elif command.command == "update_params":
            # Update parameters dynamically
            if command.parameters:
                # Implementation for dynamic parameter updates
                pass
            return {"status": "success", "message": "Parameters updated"}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown command: {command.command}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/latest")
async def get_latest_data(n_points: int = 1000):
    """Get latest simulation data."""
    try:
        data = system_state.get_latest_data(n_points)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/export")
async def export_data(format: str = "json"):
    """Export simulation data."""
    try:
        data = system_state.get_latest_data(n_points=len(system_state.time_buffer))

        if format == "json":
            return JSONResponse(content=data)
        elif format == "csv":
            # Generate CSV
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(['time', 'neural_v', 'neural_w', 'cardiac_x', 'cardiac_y'])

            # Data
            for i in range(len(data['time'])):
                writer.writerow([
                    data['time'][i],
                    data['neural']['v'][i],
                    data['neural']['w'][i],
                    data['cardiac']['x'][i],
                    data['cardiac']['y'][i]
                ])

            return FileResponse(
                output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=hbcm_data.csv"}
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown format: {format}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WebSocket Endpoint
# =============================================================================

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time data streaming.

    Client receives updates at regular intervals with simulation state.
    """
    await connection_manager.connect(websocket, client_id)

    try:
        while True:
            # Receive messages from client (for control commands)
            try:
                message = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)

                # Handle client commands
                if message.get('type') == 'control':
                    command = message.get('command')
                    # Process command...

            except asyncio.TimeoutError:
                pass  # No message received, continue

            # Send periodic updates if simulation is running
            if system_state.is_running and not system_state.is_paused:
                # Step simulation
                system_state.step_simulation()

                # Send data every N steps (to avoid overwhelming client)
                if len(system_state.time_buffer) % 10 == 0:
                    data = system_state.get_latest_data(n_points=100)
                    await connection_manager.send_personal_message({
                        'type': 'data_update',
                        'data': data
                    }, websocket)

            await asyncio.sleep(0.001)  # Small delay

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


# =============================================================================
# Background Tasks
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    print("Multi-Heart-Model Control Panel starting up...")
    print(f"System started at: {datetime.now()}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    print("Multi-Heart-Model Control Panel shutting down...")

    # Stop BCI streaming
    if system_state.bci_adapter:
        system_state.bci_adapter.stop_stream()
        system_state.bci_adapter.disconnect()

    # Close LSL bridge
    if system_state.lsl_bridge:
        system_state.lsl_bridge.stop()


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
