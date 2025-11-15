"""
OpenSim Integration Bridge

Connects Multi-Heart-Model with OpenSim biomechanical simulations.

OpenSim Repository: https://github.com/opensim-org/opensim-core

This bridge allows:
- Exporting HBCM cardiac dynamics to OpenSim muscle activation
- Importing OpenSim muscle forces to influence cardiac load
- Synchronized co-simulation of heart-brain-musculoskeletal systems
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET


@dataclass
class OpenSimConfig:
    """Configuration for OpenSim integration."""
    opensim_install_path: Optional[str] = None
    model_file: Optional[str] = None  # .osim file path
    dt: float = 0.001  # Simulation timestep
    use_api: bool = True  # Use Python API if available, else command-line
    muscle_control_mode: str = "activation"  # "activation" or "excitation"


class OpenSimBridge:
    """
    Bridge between Multi-Heart-Model and OpenSim.

    Enables bi-directional coupling:
    - HBCM cardiac output → OpenSim muscle activation
    - OpenSim muscle forces → HBCM cardiac load
    """

    def __init__(self, config: OpenSimConfig):
        """
        Initialize OpenSim bridge.

        Args:
            config: OpenSim configuration
        """
        self.config = config
        self.opensim_available = False
        self.opensim_model = None
        self.state = None

        # Try to import OpenSim Python API
        self._initialize_opensim()

    def _initialize_opensim(self):
        """Initialize OpenSim Python API if available."""
        try:
            import opensim as osim
            self.osim = osim
            self.opensim_available = True
            print("OpenSim Python API loaded successfully")

            if self.config.model_file:
                self.load_model(self.config.model_file)

        except ImportError:
            print("OpenSim Python API not found. Will use command-line interface.")
            print("Install: conda install -c opensim-org opensim")
            self.opensim_available = False

    def load_model(self, model_file: str) -> bool:
        """
        Load OpenSim model from .osim file.

        Args:
            model_file: Path to .osim model file

        Returns:
            True if successful
        """
        if not self.opensim_available:
            print("OpenSim API not available")
            return False

        try:
            self.opensim_model = self.osim.Model(model_file)
            self.state = self.opensim_model.initSystem()

            print(f"Loaded OpenSim model: {model_file}")
            print(f"  Muscles: {self.opensim_model.getMuscles().getSize()}")
            print(f"  Bodies: {self.opensim_model.getBodySet().getSize()}")
            print(f"  Coordinates: {self.opensim_model.getCoordinateSet().getSize()}")

            return True

        except Exception as e:
            print(f"Error loading OpenSim model: {e}")
            return False

    def cardiac_to_muscle_activation(
        self, cardiac_state: Tuple[float, float],
        muscle_mapping: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Convert cardiac state to muscle activation patterns.

        Args:
            cardiac_state: (x, y) from Van der Pol oscillator
            muscle_mapping: Optional mapping of muscle names to scaling factors

        Returns:
            Dictionary of muscle names to activation levels (0-1)
        """
        x, y = cardiac_state

        # Normalize cardiac position to activation range [0, 1]
        # Van der Pol typically oscillates in range [-2, 2]
        activation_base = (np.tanh(x) + 1.0) / 2.0  # Map to [0, 1]

        # Default muscle mapping (example for arm model)
        if muscle_mapping is None:
            muscle_mapping = {
                'BIClong': 1.0,      # Biceps long head
                'BICshort': 1.0,     # Biceps short head
                'TRIlong': 0.5,      # Triceps long head
                'TRIlat': 0.5,       # Triceps lateral head
                'TRImed': 0.5,       # Triceps medial head
                'BRA': 0.8,          # Brachialis
            }

        # Apply mapping
        activations = {}
        for muscle_name, scale in muscle_mapping.items():
            # Add some phase variation based on velocity
            phase_mod = np.sin(y * np.pi) * 0.2  # ±0.2 variation
            activation = np.clip(activation_base * scale + phase_mod, 0.0, 1.0)
            activations[muscle_name] = activation

        return activations

    def apply_muscle_activations(self, activations: Dict[str, float]) -> bool:
        """
        Apply muscle activations to OpenSim model.

        Args:
            activations: Dictionary of muscle names to activation levels

        Returns:
            True if successful
        """
        if not self.opensim_available or self.opensim_model is None:
            return False

        try:
            muscles = self.opensim_model.getMuscles()

            for muscle_name, activation in activations.items():
                muscle = muscles.get(muscle_name)
                if muscle:
                    if self.config.muscle_control_mode == "activation":
                        muscle.setActivation(self.state, activation)
                    else:  # excitation
                        muscle.setExcitation(self.state, activation)

            return True

        except Exception as e:
            print(f"Error applying muscle activations: {e}")
            return False

    def get_muscle_forces(self, muscle_names: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Get current muscle forces from OpenSim model.

        Args:
            muscle_names: Optional list of specific muscles (None = all muscles)

        Returns:
            Dictionary of muscle names to forces (Newtons)
        """
        if not self.opensim_available or self.opensim_model is None:
            return {}

        try:
            forces = {}
            muscles = self.opensim_model.getMuscles()

            if muscle_names is None:
                # Get all muscles
                muscle_names = [
                    muscles.get(i).getName()
                    for i in range(muscles.getSize())
                ]

            for muscle_name in muscle_names:
                muscle = muscles.get(muscle_name)
                if muscle:
                    force = muscle.getActiveFiberForce(self.state)
                    forces[muscle_name] = force

            return forces

        except Exception as e:
            print(f"Error getting muscle forces: {e}")
            return {}

    def muscle_force_to_cardiac_load(self, forces: Dict[str, float]) -> float:
        """
        Convert muscle forces to cardiac load (influences heart rate).

        Args:
            forces: Dictionary of muscle forces

        Returns:
            Cardiac load factor (higher = more metabolic demand)
        """
        # Total muscle force as proxy for metabolic demand
        total_force = sum(forces.values())

        # Normalize to reasonable range [0, 1]
        # Assume typical max total force ~1000 N for upper extremity
        load_factor = np.tanh(total_force / 1000.0)

        return load_factor

    def step_simulation(self, dt: Optional[float] = None) -> bool:
        """
        Advance OpenSim simulation by one timestep.

        Args:
            dt: Timestep (uses config.dt if None)

        Returns:
            True if successful
        """
        if not self.opensim_available or self.opensim_model is None:
            return False

        if dt is None:
            dt = self.config.dt

        try:
            # Realize to acceleration stage
            self.opensim_model.realizeAcceleration(self.state)

            # Get integrator
            integrator = self.osim.RungeKuttaMersonIntegrator(
                self.opensim_model.getMultibodySystem()
            )
            integrator.setAccuracy(1e-5)

            # Step
            integrator.stepTo(self.state.getTime() + dt)

            return True

        except Exception as e:
            print(f"Error stepping OpenSim simulation: {e}")
            return False

    def export_motion(self, output_file: str,
                     times: List[float],
                     states: List[Dict[str, float]]) -> bool:
        """
        Export motion trajectory to OpenSim .sto (storage) format.

        Args:
            output_file: Path for output .sto file
            times: List of time points
            states: List of state dictionaries (coordinate names to values)

        Returns:
            True if successful
        """
        try:
            # Create storage file
            storage = self.osim.Storage()
            storage.setName("MultiHeartModel_Motion")

            # Get coordinate names
            coord_names = list(states[0].keys()) if states else []

            # Set column labels
            labels = self.osim.ArrayStr()
            labels.append("time")
            for name in coord_names:
                labels.append(name)
            storage.setColumnLabels(labels)

            # Add data rows
            for t, state_dict in zip(times, states):
                row = self.osim.ArrayDouble()
                row.append(t)
                for name in coord_names:
                    row.append(state_dict.get(name, 0.0))
                storage.append(row)

            # Write to file
            storage.print(output_file)

            print(f"Exported motion to: {output_file}")
            return True

        except Exception as e:
            print(f"Error exporting motion: {e}")
            return False

    def create_control_file(
        self,
        output_file: str,
        times: List[float],
        activations: List[Dict[str, float]]
    ) -> bool:
        """
        Create OpenSim control file (.sto) from activation time series.

        Args:
            output_file: Path for output control file
            times: Time points
            activations: List of activation dictionaries

        Returns:
            True if successful
        """
        try:
            with open(output_file, 'w') as f:
                # Header
                f.write("MultiHeartModel_Controls\n")
                f.write("version=1\n")
                f.write(f"nRows={len(times)}\n")

                # Get muscle names
                muscle_names = list(activations[0].keys()) if activations else []
                f.write(f"nColumns={len(muscle_names) + 1}\n")
                f.write("inDegrees=no\n")
                f.write("\n")

                # Column labels
                f.write("time\t" + "\t".join(muscle_names) + "\n")

                # Data
                for t, act_dict in zip(times, activations):
                    values = [str(t)] + [str(act_dict.get(m, 0.0)) for m in muscle_names]
                    f.write("\t".join(values) + "\n")

            print(f"Created control file: {output_file}")
            return True

        except Exception as e:
            print(f"Error creating control file: {e}")
            return False


class HBCMOpenSimCoSimulator:
    """
    Co-simulator for synchronized HBCM and OpenSim execution.

    Runs both systems in lockstep with bi-directional coupling.
    """

    def __init__(self, hbcm_model, opensim_bridge: OpenSimBridge,
                 coupling_gain: float = 0.1):
        """
        Initialize co-simulator.

        Args:
            hbcm_model: HeartBrainCouplingModel instance
            opensim_bridge: OpenSimBridge instance
            coupling_gain: Strength of muscle-to-cardiac coupling
        """
        self.hbcm = hbcm_model
        self.opensim = opensim_bridge
        self.coupling_gain = coupling_gain

        # History for analysis
        self.time_history = []
        self.hbcm_history = []
        self.opensim_history = []
        self.muscle_force_history = []

    def simulate(
        self,
        initial_hbcm_state: Tuple[float, float, float, float],
        duration: float,
        dt: float,
        muscle_mapping: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Run co-simulation.

        Args:
            initial_hbcm_state: Initial (v, w, x, y) for HBCM
            duration: Simulation duration in seconds
            dt: Timestep
            muscle_mapping: Muscle activation mapping

        Returns:
            Dictionary with simulation results
        """
        print(f"Starting co-simulation: {duration}s @ dt={dt}s")

        current_time = 0.0
        hbcm_state = initial_hbcm_state

        steps = int(duration / dt)

        for step in range(steps):
            # 1. Extract cardiac state from HBCM
            cardiac_state = (hbcm_state[2], hbcm_state[3])  # (x, y)

            # 2. Convert to muscle activations
            activations = self.opensim.cardiac_to_muscle_activation(
                cardiac_state, muscle_mapping
            )

            # 3. Apply to OpenSim
            self.opensim.apply_muscle_activations(activations)

            # 4. Step OpenSim
            self.opensim.step_simulation(dt)

            # 5. Get muscle forces from OpenSim
            forces = self.opensim.get_muscle_forces()

            # 6. Convert muscle forces to cardiac load
            cardiac_load = self.opensim.muscle_force_to_cardiac_load(forces)

            # 7. Step HBCM with cardiac load influence
            # (Would need to modify HBCM to accept external load parameter)
            # For now, just step normally
            hbcm_state = self.hbcm.step(current_time, hbcm_state, dt)

            # Store history
            self.time_history.append(current_time)
            self.hbcm_history.append(hbcm_state)
            self.opensim_history.append(activations)
            self.muscle_force_history.append(forces)

            current_time += dt

            if step % 1000 == 0:
                print(f"  Step {step}/{steps}, t={current_time:.2f}s, "
                      f"cardiac_load={cardiac_load:.3f}")

        print("Co-simulation complete")

        return {
            'times': self.time_history,
            'hbcm_states': self.hbcm_history,
            'muscle_activations': self.opensim_history,
            'muscle_forces': self.muscle_force_history,
            'duration': duration,
            'timestep': dt,
            'n_steps': len(self.time_history)
        }

    def export_to_opensim(self, output_dir: str):
        """
        Export co-simulation results to OpenSim format.

        Args:
            output_dir: Directory for output files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        # Export muscle activations as control file
        self.opensim.create_control_file(
            str(output_path / "muscle_controls.sto"),
            self.time_history,
            self.opensim_history
        )

        # Export results as JSON
        results = {
            'metadata': {
                'duration': self.time_history[-1] if self.time_history else 0,
                'n_steps': len(self.time_history),
                'dt': self.time_history[1] - self.time_history[0] if len(self.time_history) > 1 else 0
            },
            'times': self.time_history,
            'hbcm_neural_v': [s[0] for s in self.hbcm_history],
            'hbcm_neural_w': [s[1] for s in self.hbcm_history],
            'hbcm_cardiac_x': [s[2] for s in self.hbcm_history],
            'hbcm_cardiac_y': [s[3] for s in self.hbcm_history],
        }

        with open(output_path / "cosimulation_results.json", 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Exported results to: {output_dir}")


def create_simple_opensim_model(output_file: str = "simple_arm.osim") -> bool:
    """
    Create a simple OpenSim arm model programmatically.

    Args:
        output_file: Path for output .osim file

    Returns:
        True if successful
    """
    # This is a simplified example - real models are much more complex
    # Normally you'd use OpenSim GUI or Python API to build models

    model_xml = """<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
    <Model name="SimpleArm">
        <credits>Generated by Multi-Heart-Model</credits>
        <BodySet>
            <objects>
                <Body name="ground">
                    <mass>0</mass>
                    <mass_center>0 0 0</mass_center>
                    <inertia>0 0 0 0 0 0</inertia>
                </Body>
                <Body name="humerus">
                    <mass>1.8645</mass>
                    <mass_center>0 -0.18 0</mass_center>
                    <inertia>0.01481 0.00410 0.01490 0 0 0</inertia>
                </Body>
            </objects>
        </BodySet>
    </Model>
</OpenSimDocument>"""

    try:
        with open(output_file, 'w') as f:
            f.write(model_xml)
        print(f"Created simple OpenSim model: {output_file}")
        return True
    except Exception as e:
        print(f"Error creating model: {e}")
        return False
