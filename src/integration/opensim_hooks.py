"""
OpenSim integration hooks for Multi-Heart-Model.

This module provides bidirectional integration between the Heart-Brain Coupling Model (HBCM)
and OpenSim biomechanical simulations.

Key Features:
1. Convert cardiac dynamics to muscle activation patterns
2. Export OpenSim-compatible motion files (.mot format)
3. Orchestrate OpenSim CLI simulations
4. Parse biomechanical results for closed-loop feedback
5. Map biomechanical loads back to cardiac afterload

Author: Multi-Heart-Model Team
License: MIT
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Callable
import numpy as np
import subprocess
import os
from pathlib import Path


@dataclass
class OpenSimConfig:
    """Configuration for OpenSim integration."""

    # OpenSim model and setup files
    model_file: str = "models/gait2392.osim"
    setup_file: str = "setup/forward_dynamics_setup.xml"

    # Output paths
    motion_output_dir: str = "results/opensim/motions"
    results_output_dir: str = "results/opensim/biomechanics"

    # Simulation parameters
    time_step: float = 0.01
    integrator: str = "RungeKutta45"  # or "SemiExplicitEuler2"

    # Muscle mapping
    n_muscles: int = 8
    muscle_names: Optional[List[str]] = None

    # Cardiac-to-muscle mapping function
    mapping_function: str = "phase_distributed"  # or "direct", "fatigue_model"

    # OpenSim executable
    opensim_bin: str = "opensim-cmd"

    def __post_init__(self):
        """Initialize default muscle names if not provided."""
        if self.muscle_names is None:
            self.muscle_names = [
                "glut_max_r",
                "hamstrings_r",
                "rect_fem_r",
                "vasti_r",
                "bifemsh_r",
                "gastroc_r",
                "soleus_r",
                "tib_ant_r"
            ][:self.n_muscles]

        # Ensure output directories exist
        Path(self.motion_output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.results_output_dir).mkdir(parents=True, exist_ok=True)


@dataclass
class BiomechanicalResults:
    """Container for OpenSim simulation results."""

    success: bool
    output_file: str
    kinematics: Dict[str, np.ndarray] = field(default_factory=dict)
    forces: Dict[str, Dict[str, float]] = field(default_factory=dict)
    summary: Dict[str, float] = field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""


class CardiacForceExtractor:
    """
    Extract muscle activation patterns from HBCM cardiac dynamics.

    This class implements various mapping strategies to convert cardiac oscillator
    state (Van der Pol model) into physiologically-plausible muscle activation patterns
    for biomechanical simulation.
    """

    def __init__(self, config: OpenSimConfig = None):
        """
        Initialize the cardiac force extractor.

        Args:
            config: OpenSim configuration (uses defaults if None)
        """
        self.config = config or OpenSimConfig()

    def cardiac_state_to_muscle_activation(
        self,
        cardiac_trajectory: List[Tuple[float, Tuple[float, float]]],
        mapping_strategy: Optional[str] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert cardiac oscillator state to muscle activation patterns.

        Args:
            cardiac_trajectory: List of (time, (x, y)) tuples from HBCM cardiac model
            mapping_strategy: Override config mapping ("phase_distributed", "direct", "fatigue_model")

        Returns:
            Tuple of (times, activations) where:
            - times: 1D array of timesteps (seconds)
            - activations: 2D array of shape (n_timesteps, n_muscles) with values [0, 1]

        Mathematical Mapping:
            Phase-distributed strategy distributes cardiac phase across muscles:
                activation_i(t) = normalize(x(t)) * cos(ω*t + φ_i)
            where φ_i = 2π*i/n_muscles creates phase offsets for gait-like patterns
        """
        strategy = mapping_strategy or self.config.mapping_function

        # Extract time and state arrays
        times = np.array([t for t, _ in cardiac_trajectory])
        x_values = np.array([x for _, (x, y) in cardiac_trajectory])
        y_values = np.array([y for _, (x, y) in cardiac_trajectory])

        # Apply selected mapping strategy
        if strategy == "phase_distributed":
            activations = self._phase_distributed_mapping(times, x_values, y_values)
        elif strategy == "direct":
            activations = self._direct_mapping(x_values, y_values)
        elif strategy == "fatigue_model":
            activations = self._fatigue_model_mapping(times, x_values, y_values)
        else:
            raise ValueError(f"Unknown mapping strategy: {strategy}")

        return times, activations

    def _phase_distributed_mapping(
        self,
        times: np.ndarray,
        x_values: np.ndarray,
        y_values: np.ndarray
    ) -> np.ndarray:
        """
        Distribute cardiac phase across muscles to simulate gait-like patterns.

        This creates a wave of activation across muscle groups, where each muscle
        activates in sequence based on cardiac rhythm. Useful for generating
        coordinated movement patterns from cardiac oscillations.
        """
        # Normalize cardiac position to [0, 1] range (amplitude modulation)
        x_norm = (x_values - x_values.min()) / (x_values.max() - x_values.min() + 1e-10)

        # Estimate cardiac frequency from trajectory
        cardiac_period = self._estimate_period(times, x_values)
        cardiac_freq = 1.0 / cardiac_period if cardiac_period > 0 else 1.0

        # Create phase-shifted activations for each muscle
        n_timesteps = len(times)
        activations = np.zeros((n_timesteps, self.config.n_muscles))

        for i in range(self.config.n_muscles):
            # Phase offset for this muscle
            phase_shift = 2 * np.pi * i / self.config.n_muscles

            # Generate activation with cardiac rhythm and phase offset
            for t_idx, t in enumerate(times):
                phase = 2 * np.pi * cardiac_freq * t + phase_shift
                activations[t_idx, i] = x_norm[t_idx] * (0.5 + 0.5 * np.cos(phase))

        # Ensure all activations in [0, 1] range
        activations = np.clip(activations, 0.0, 1.0)

        return activations

    def _direct_mapping(
        self,
        x_values: np.ndarray,
        y_values: np.ndarray
    ) -> np.ndarray:
        """
        Direct mapping where all muscles receive the same activation from cardiac state.

        Simplest mapping - useful for testing or when cardiac output directly
        drives a single muscle group (e.g., cardiac-driven breathing simulation).
        """
        # Normalize to [0, 1]
        x_norm = (x_values - x_values.min()) / (x_values.max() - x_values.min() + 1e-10)

        # Repeat for all muscles
        n_timesteps = len(x_values)
        activations = np.tile(x_norm.reshape(-1, 1), (1, self.config.n_muscles))

        return activations

    def _fatigue_model_mapping(
        self,
        times: np.ndarray,
        x_values: np.ndarray,
        y_values: np.ndarray
    ) -> np.ndarray:
        """
        Incorporate muscle fatigue dynamics into activation patterns.

        Models gradual fatigue accumulation where prolonged cardiac stress
        leads to decreased muscle activation capacity. Useful for simulating
        exhaustion during prolonged exercise or cardiac events.

        Fatigue dynamics:
            fatigue_rate = k * activation^2
            recovery_rate = r * (1 - fatigue)
        """
        x_norm = (x_values - x_values.min()) / (x_values.max() - x_values.min() + 1e-10)

        # Fatigue parameters (can be made configurable)
        k_fatigue = 0.01  # Fatigue accumulation rate
        r_recovery = 0.05  # Recovery rate

        n_timesteps = len(times)
        activations = np.zeros((n_timesteps, self.config.n_muscles))
        fatigue = np.zeros(self.config.n_muscles)  # Current fatigue level [0, 1]

        # Compute time steps
        dt = np.diff(times)
        dt = np.append(dt, dt[-1] if len(dt) > 0 else 0.01)

        for t_idx in range(n_timesteps):
            # Base activation from cardiac state
            base_activation = x_norm[t_idx]

            for muscle_idx in range(self.config.n_muscles):
                # Reduce activation by fatigue
                activations[t_idx, muscle_idx] = base_activation * (1.0 - fatigue[muscle_idx])

                # Update fatigue
                fatigue_increase = k_fatigue * (activations[t_idx, muscle_idx] ** 2) * dt[t_idx]
                fatigue_decrease = r_recovery * fatigue[muscle_idx] * dt[t_idx]
                fatigue[muscle_idx] = np.clip(
                    fatigue[muscle_idx] + fatigue_increase - fatigue_decrease,
                    0.0, 1.0
                )

        return activations

    def _estimate_period(self, times: np.ndarray, signal: np.ndarray) -> float:
        """
        Estimate the dominant period of a signal using zero-crossing analysis.

        Args:
            times: Time array
            signal: Signal values

        Returns:
            Estimated period in seconds (0.0 if unable to estimate)
        """
        if len(signal) < 3:
            return 1.0  # Default period

        # Find zero crossings
        mean_signal = signal - signal.mean()
        crossings = np.where(np.diff(np.sign(mean_signal)))[0]

        if len(crossings) < 2:
            return 1.0

        # Estimate period from average crossing interval
        crossing_times = times[crossings]
        periods = np.diff(crossing_times)

        # Period is 2x the average half-period
        return 2.0 * np.median(periods) if len(periods) > 0 else 1.0

    def export_opensim_motion(
        self,
        times: np.ndarray,
        activations: np.ndarray,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Export muscle activations to OpenSim .mot (motion) format.

        The .mot format is a tab-delimited text file with a header containing
        metadata and a data section with time and muscle activation columns.

        Args:
            times: 1D array of time values (seconds)
            activations: 2D array of shape (n_timesteps, n_muscles)
            output_filename: Custom filename (auto-generated if None)

        Returns:
            Path to the generated .mot file

        File Format:
            Cardiac-Derived Muscle Activations
            nRows=<number of timesteps>
            nColumns=<number of muscles + 1>
            inDegrees=no
            endheader
            time    muscle_1    muscle_2    ...
            0.000   0.500       0.300       ...
            0.010   0.520       0.310       ...
            ...
        """
        if output_filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"cardiac_activations_{timestamp}.mot"

        output_path = os.path.join(self.config.motion_output_dir, output_filename)

        # Validate dimensions
        if len(times) != activations.shape[0]:
            raise ValueError(f"Time array length {len(times)} doesn't match "
                           f"activations rows {activations.shape[0]}")

        if activations.shape[1] != len(self.config.muscle_names):
            raise ValueError(f"Activations has {activations.shape[1]} muscles but "
                           f"config specifies {len(self.config.muscle_names)} names")

        # Write .mot file
        with open(output_path, 'w') as f:
            # Header
            f.write("Cardiac-Derived Muscle Activations\n")
            f.write(f"nRows={len(times)}\n")
            f.write(f"nColumns={len(self.config.muscle_names) + 1}\n")
            f.write("inDegrees=no\n")
            f.write("endheader\n")

            # Column names
            f.write("time\t" + "\t".join(self.config.muscle_names) + "\n")

            # Data rows
            for i, t in enumerate(times):
                row_values = [f"{t:.6f}"] + [f"{a:.6f}" for a in activations[i, :]]
                f.write("\t".join(row_values) + "\n")

        return output_path


class OpenSimBridge:
    """
    Bridge between HBCM and OpenSim biomechanical simulation.

    This class orchestrates the full workflow:
    1. Convert HBCM cardiac trajectory to muscle activations
    2. Export OpenSim motion file
    3. Run OpenSim simulation via CLI
    4. Parse biomechanical results
    5. Extract feedback signals for HBCM
    """

    def __init__(self, config: OpenSimConfig = None):
        """
        Initialize the OpenSim bridge.

        Args:
            config: OpenSim configuration (uses defaults if None)
        """
        self.config = config or OpenSimConfig()
        self.extractor = CardiacForceExtractor(self.config)

    def run_full_pipeline(
        self,
        cardiac_trajectory: List[Tuple[float, Tuple[float, float]]],
        model_file: Optional[str] = None,
        setup_file: Optional[str] = None
    ) -> BiomechanicalResults:
        """
        Run complete HBCM → OpenSim pipeline.

        Args:
            cardiac_trajectory: List of (time, (x, y)) from HBCM
            model_file: Override default OpenSim model
            setup_file: Override default setup XML

        Returns:
            BiomechanicalResults with kinematics, forces, and summary

        Workflow:
            1. Extract muscle activations from cardiac trajectory
            2. Export to .mot file
            3. Run OpenSim forward dynamics
            4. Parse results
            5. Calculate feedback parameters
        """
        # Step 1: Generate muscle activations
        times, activations = self.extractor.cardiac_state_to_muscle_activation(
            cardiac_trajectory
        )

        # Step 2: Export to .mot file
        motion_file = self.extractor.export_opensim_motion(times, activations)

        # Step 3: Run OpenSim simulation
        results = self.run_forward_dynamics(
            motion_file=motion_file,
            model_file=model_file,
            setup_file=setup_file
        )

        # Step 4: Calculate feedback parameters
        if results.success and results.kinematics:
            results.summary = self.create_closed_loop_feedback(results.kinematics)

        return results

    def run_forward_dynamics(
        self,
        motion_file: str,
        model_file: Optional[str] = None,
        setup_file: Optional[str] = None
    ) -> BiomechanicalResults:
        """
        Run OpenSim forward dynamics simulation via CLI.

        Args:
            motion_file: Path to .mot file with muscle activations
            model_file: Path to .osim model file (uses config default if None)
            setup_file: Path to setup XML (uses config default if None)

        Returns:
            BiomechanicalResults object

        Requires:
            OpenSim installed with CLI tools (opensim-cmd or opensim-cmd.exe)
        """
        model = model_file or self.config.model_file
        setup = setup_file or self.config.setup_file

        # Generate output filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(
            self.config.results_output_dir,
            f"biomechanics_{timestamp}.sto"
        )

        # Build OpenSim command
        # Note: Command syntax depends on OpenSim version and installation
        # This is a generic template - may need adjustment
        cmd = [
            self.config.opensim_bin,
            "run-tool",
            setup,
            "-model", model,
            "-motion", motion_file,
            "-results", output_file
        ]

        try:
            # Run OpenSim simulation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                return BiomechanicalResults(
                    success=False,
                    output_file="",
                    stdout=result.stdout,
                    stderr=result.stderr
                )

            # Parse results if successful
            kinematics = self._parse_sto_file(output_file)
            forces = self._extract_forces(kinematics)

            return BiomechanicalResults(
                success=True,
                output_file=output_file,
                kinematics=kinematics,
                forces=forces,
                stdout=result.stdout,
                stderr=result.stderr
            )

        except subprocess.TimeoutExpired:
            return BiomechanicalResults(
                success=False,
                output_file="",
                stderr="OpenSim simulation timed out after 5 minutes"
            )
        except FileNotFoundError:
            return BiomechanicalResults(
                success=False,
                output_file="",
                stderr=f"OpenSim executable not found: {self.config.opensim_bin}\n"
                       f"Ensure OpenSim is installed and accessible in PATH"
            )

    def _parse_sto_file(self, sto_path: str) -> Dict[str, np.ndarray]:
        """
        Parse OpenSim .sto (storage) file.

        .sto files are tab-delimited text files with a header section followed
        by data columns. Each column represents a state variable (joint angle,
        muscle force, etc.).

        Args:
            sto_path: Path to .sto file

        Returns:
            Dictionary mapping column names to numpy arrays
        """
        if not os.path.exists(sto_path):
            return {}

        data = {}
        header_complete = False
        columns = []

        with open(sto_path, 'r') as f:
            for line in f:
                # Skip until end of header
                if line.startswith('endheader'):
                    header_complete = True
                    continue

                if not header_complete:
                    continue

                # First line after header contains column names
                if not columns:
                    columns = line.strip().split('\t')
                    data = {col: [] for col in columns}
                    continue

                # Data lines
                values = line.strip().split('\t')
                if len(values) != len(columns):
                    continue  # Skip malformed lines

                for col, val in zip(columns, values):
                    try:
                        data[col].append(float(val))
                    except ValueError:
                        data[col].append(0.0)  # Handle non-numeric values

        # Convert to numpy arrays
        return {col: np.array(vals) for col, vals in data.items()}

    def _extract_forces(
        self,
        kinematics: Dict[str, np.ndarray]
    ) -> Dict[str, Dict[str, float]]:
        """
        Extract force/moment summary statistics from kinematics data.

        Args:
            kinematics: Dictionary of kinematic variables

        Returns:
            Dictionary mapping force/moment names to statistics (mean, max, min, std)
        """
        forces = {}

        for key, values in kinematics.items():
            # Identify force/moment columns
            key_lower = key.lower()
            if any(term in key_lower for term in ['force', 'moment', 'torque', 'grf']):
                forces[key] = {
                    'mean': float(np.mean(values)),
                    'max': float(np.max(values)),
                    'min': float(np.min(values)),
                    'std': float(np.std(values)),
                    'rms': float(np.sqrt(np.mean(values ** 2)))
                }

        return forces

    def create_closed_loop_feedback(
        self,
        biomechanical_results: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """
        Extract biomechanical loads to feed back into HBCM cardiac model.

        This creates a closed-loop system where biomechanical simulation results
        influence cardiac parameters, allowing for physiologically-realistic
        coupling (e.g., exercise load increases cardiac afterload).

        Args:
            biomechanical_results: Parsed OpenSim results

        Returns:
            Dictionary of feedback parameters for HBCM:
            - cardiac_afterload_factor: Multiplier for cardiac resistance
            - total_mechanical_power: Summed mechanical work
            - peak_ground_reaction_force: Max GRF (if available)
            - metabolic_cost: Estimated energy expenditure
        """
        feedback = {
            'cardiac_afterload_factor': 1.0,
            'total_mechanical_power': 0.0,
            'peak_ground_reaction_force': 0.0,
            'metabolic_cost': 0.0
        }

        # Calculate total mechanical power from joint powers
        total_power = 0.0
        power_columns = [k for k in biomechanical_results.keys()
                        if 'power' in k.lower()]

        for col in power_columns:
            total_power += np.abs(biomechanical_results[col]).mean()

        feedback['total_mechanical_power'] = total_power

        # Find peak ground reaction force
        grf_columns = [k for k in biomechanical_results.keys()
                      if 'grf' in k.lower() or 'ground_force' in k.lower()]

        if grf_columns:
            peak_grf = max(np.max(np.abs(biomechanical_results[col]))
                          for col in grf_columns)
            feedback['peak_ground_reaction_force'] = peak_grf

        # Estimate cardiac afterload adjustment
        # Higher mechanical work → higher cardiac load
        # This is a simplified model; real physiology is more complex
        if total_power > 0:
            # Normalize power to [0, 1] range (assumes max power ~100 W)
            normalized_power = min(total_power / 100.0, 1.0)
            # Afterload increases up to 50% with maximum effort
            feedback['cardiac_afterload_factor'] = 1.0 + 0.5 * normalized_power

        # Estimate metabolic cost (simplified)
        # Metabolic cost ≈ 4-5 times mechanical work for human movement
        feedback['metabolic_cost'] = total_power * 4.5

        return feedback


# Convenience function for quick integration
def run_hbcm_opensim_integration(
    cardiac_trajectory: List[Tuple[float, Tuple[float, float]]],
    config: Optional[OpenSimConfig] = None
) -> BiomechanicalResults:
    """
    One-line function to run complete HBCM → OpenSim integration.

    Args:
        cardiac_trajectory: List of (time, (x, y)) from HBCM cardiac model
        config: Optional OpenSim configuration

    Returns:
        BiomechanicalResults with kinematics, forces, and feedback parameters

    Example:
        >>> from src.cardiac import VanDerPolOscillator
        >>> from src.coupling import HeartBrainCouplingModel
        >>> from src.integration.opensim_hooks import run_hbcm_opensim_integration
        >>>
        >>> # Run HBCM simulation
        >>> hbcm = HeartBrainCouplingModel()
        >>> trajectory = hbcm.simulate((0, 0, 1, 0), (0, 10), 0.01)
        >>>
        >>> # Extract cardiac trajectory
        >>> _, _, cardiac = hbcm.extract_series(trajectory)
        >>> cardiac_traj = [(t, state) for t, state in zip(times, cardiac)]
        >>>
        >>> # Run OpenSim integration
        >>> results = run_hbcm_opensim_integration(cardiac_traj)
        >>>
        >>> # Check results
        >>> if results.success:
        >>>     print(f"Cardiac afterload factor: {results.summary['cardiac_afterload_factor']}")
        >>>     print(f"Mechanical power: {results.summary['total_mechanical_power']} W")
    """
    bridge = OpenSimBridge(config)
    return bridge.run_full_pipeline(cardiac_trajectory)
