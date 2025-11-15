"""
Real-time Visualization Components

Provides matplotlib, Plotly, and 3D visualization tools for the Multi-Heart-Model.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web serving

from typing import List, Tuple, Optional, Dict, Any
import io
import base64


class RealtimePlotter:
    """
    Real-time plotting with matplotlib for neural and cardiac signals.
    """

    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        """
        Initialize plotter.

        Args:
            figsize: Figure size (width, height) in inches
        """
        self.figsize = figsize
        self.fig, self.axes = plt.subplots(3, 2, figsize=figsize)
        self.fig.tight_layout(pad=3.0)

        # Set up subplots
        self._setup_plots()

        # Data storage
        self.time_data = []
        self.neural_v = []
        self.neural_w = []
        self.cardiac_x = []
        self.cardiac_y = []

        self.max_points = 2000

    def _setup_plots(self):
        """Configure subplot properties."""
        # Neural voltage
        self.axes[0, 0].set_title('Neural Voltage (v)')
        self.axes[0, 0].set_xlabel('Time (s)')
        self.axes[0, 0].set_ylabel('Voltage')
        self.axes[0, 0].grid(True, alpha=0.3)

        # Neural recovery
        self.axes[0, 1].set_title('Neural Recovery (w)')
        self.axes[0, 1].set_xlabel('Time (s)')
        self.axes[0, 1].set_ylabel('Recovery')
        self.axes[0, 1].grid(True, alpha=0.3)

        # Cardiac position
        self.axes[1, 0].set_title('Cardiac Position (x)')
        self.axes[1, 0].set_xlabel('Time (s)')
        self.axes[1, 0].set_ylabel('Position')
        self.axes[1, 0].grid(True, alpha=0.3)

        # Cardiac velocity
        self.axes[1, 1].set_title('Cardiac Velocity (y)')
        self.axes[1, 1].set_xlabel('Time (s)')
        self.axes[1, 1].set_ylabel('Velocity')
        self.axes[1, 1].grid(True, alpha=0.3)

        # Neural phase space
        self.axes[2, 0].set_title('Neural Phase Space')
        self.axes[2, 0].set_xlabel('v')
        self.axes[2, 0].set_ylabel('w')
        self.axes[2, 0].grid(True, alpha=0.3)

        # Cardiac phase space
        self.axes[2, 1].set_title('Cardiac Phase Space')
        self.axes[2, 1].set_xlabel('x')
        self.axes[2, 1].set_ylabel('y')
        self.axes[2, 1].grid(True, alpha=0.3)

    def update(self, time: List[float], neural: List[Tuple[float, float]],
               cardiac: List[Tuple[float, float]]):
        """
        Update plots with new data.

        Args:
            time: Time values
            neural: List of (v, w) tuples
            cardiac: List of (x, y) tuples
        """
        # Update data
        self.time_data = time[-self.max_points:]
        self.neural_v = [v for v, w in neural[-self.max_points:]]
        self.neural_w = [w for v, w in neural[-self.max_points:]]
        self.cardiac_x = [x for x, y in cardiac[-self.max_points:]]
        self.cardiac_y = [y for x, y in cardiac[-self.max_points:]]

        # Clear previous plots
        for ax_row in self.axes:
            for ax in ax_row:
                ax.clear()

        self._setup_plots()

        # Plot time series
        self.axes[0, 0].plot(self.time_data, self.neural_v, 'b-', linewidth=0.5)
        self.axes[0, 1].plot(self.time_data, self.neural_w, 'r-', linewidth=0.5)
        self.axes[1, 0].plot(self.time_data, self.cardiac_x, 'g-', linewidth=0.5)
        self.axes[1, 1].plot(self.time_data, self.cardiac_y, 'm-', linewidth=0.5)

        # Plot phase spaces
        self.axes[2, 0].plot(self.neural_v, self.neural_w, 'b-', linewidth=0.5, alpha=0.6)
        self.axes[2, 0].plot(self.neural_v[-1], self.neural_w[-1], 'ro', markersize=8)  # Current point

        self.axes[2, 1].plot(self.cardiac_x, self.cardiac_y, 'g-', linewidth=0.5, alpha=0.6)
        self.axes[2, 1].plot(self.cardiac_x[-1], self.cardiac_y[-1], 'ro', markersize=8)  # Current point

    def get_figure(self) -> Figure:
        """Get the matplotlib figure."""
        return self.fig

    def save_to_buffer(self, format: str = 'png', dpi: int = 100) -> io.BytesIO:
        """
        Save figure to buffer.

        Args:
            format: Image format ('png', 'jpg', 'svg')
            dpi: Resolution

        Returns:
            BytesIO buffer with image data
        """
        buf = io.BytesIO()
        self.fig.savefig(buf, format=format, dpi=dpi, bbox_inches='tight')
        buf.seek(0)
        return buf

    def get_base64_image(self, format: str = 'png', dpi: int = 100) -> str:
        """
        Get base64-encoded image for web display.

        Args:
            format: Image format
            dpi: Resolution

        Returns:
            Base64-encoded string
        """
        buf = self.save_to_buffer(format, dpi)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f"data:image/{format};base64,{img_base64}"


class PlotlyVisualizer:
    """
    Interactive Plotly-based visualization for web display.
    """

    @staticmethod
    def create_interactive_plot(time: List[float], neural: List[Tuple[float, float]],
                               cardiac: List[Tuple[float, float]]) -> Dict[str, Any]:
        """
        Create interactive Plotly figure.

        Args:
            time: Time values
            neural: Neural state (v, w) tuples
            cardiac: Cardiac state (x, y) tuples

        Returns:
            Plotly figure dictionary
        """
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            # Create subplots
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=('Neural Voltage (v)', 'Neural Recovery (w)',
                              'Cardiac Position (x)', 'Cardiac Velocity (y)',
                              'Neural Phase Space', 'Cardiac Phase Space'),
                vertical_spacing=0.1,
                horizontal_spacing=0.1
            )

            # Extract data
            neural_v = [v for v, w in neural]
            neural_w = [w for v, w in neural]
            cardiac_x = [x for x, y in cardiac]
            cardiac_y = [y for x, y in cardiac]

            # Time series plots
            fig.add_trace(go.Scatter(x=time, y=neural_v, mode='lines',
                                    name='Neural v', line=dict(color='blue', width=1)),
                         row=1, col=1)

            fig.add_trace(go.Scatter(x=time, y=neural_w, mode='lines',
                                    name='Neural w', line=dict(color='red', width=1)),
                         row=1, col=2)

            fig.add_trace(go.Scatter(x=time, y=cardiac_x, mode='lines',
                                    name='Cardiac x', line=dict(color='green', width=1)),
                         row=2, col=1)

            fig.add_trace(go.Scatter(x=time, y=cardiac_y, mode='lines',
                                    name='Cardiac y', line=dict(color='magenta', width=1)),
                         row=2, col=2)

            # Phase space plots
            fig.add_trace(go.Scatter(x=neural_v, y=neural_w, mode='lines',
                                    name='Neural Phase', line=dict(color='blue', width=1)),
                         row=3, col=1)
            fig.add_trace(go.Scatter(x=[neural_v[-1]], y=[neural_w[-1]],
                                    mode='markers', marker=dict(color='red', size=10),
                                    name='Current Neural', showlegend=False),
                         row=3, col=1)

            fig.add_trace(go.Scatter(x=cardiac_x, y=cardiac_y, mode='lines',
                                    name='Cardiac Phase', line=dict(color='green', width=1)),
                         row=3, col=2)
            fig.add_trace(go.Scatter(x=[cardiac_x[-1]], y=[cardiac_y[-1]],
                                    mode='markers', marker=dict(color='red', size=10),
                                    name='Current Cardiac', showlegend=False),
                         row=3, col=2)

            # Update layout
            fig.update_layout(
                height=900,
                showlegend=True,
                title_text="Multi-Heart-Model Real-time Visualization"
            )

            # Update axes labels
            fig.update_xaxes(title_text="Time (s)", row=1, col=1)
            fig.update_xaxes(title_text="Time (s)", row=1, col=2)
            fig.update_xaxes(title_text="Time (s)", row=2, col=1)
            fig.update_xaxes(title_text="Time (s)", row=2, col=2)
            fig.update_xaxes(title_text="v", row=3, col=1)
            fig.update_xaxes(title_text="x", row=3, col=2)

            fig.update_yaxes(title_text="Voltage", row=1, col=1)
            fig.update_yaxes(title_text="Recovery", row=1, col=2)
            fig.update_yaxes(title_text="Position", row=2, col=1)
            fig.update_yaxes(title_text="Velocity", row=2, col=2)
            fig.update_yaxes(title_text="w", row=3, col=1)
            fig.update_yaxes(title_text="y", row=3, col=2)

            return fig.to_dict()

        except ImportError:
            print("Plotly not installed. Install with: pip install plotly")
            return {}


class Visualizer3D:
    """
    3D visualization using VTK and Mayavi (when available).
    """

    @staticmethod
    def create_3d_trajectory_vtk(neural: List[Tuple[float, float]],
                                 cardiac: List[Tuple[float, float]],
                                 time: List[float]) -> Optional[str]:
        """
        Create 3D trajectory visualization using VTK.

        Args:
            neural: Neural state (v, w) tuples
            cardiac: Cardiac state (x, y) tuples
            time: Time values

        Returns:
            HTML string with VTK visualization
        """
        try:
            # Try using PyVista (modern VTK wrapper)
            import pyvista as pv

            # Create plotter
            plotter = pv.Plotter(off_screen=True)

            # Neural trajectory (v, w, t) in 3D
            neural_v = np.array([v for v, w in neural])
            neural_w = np.array([w for v, w in neural])
            time_arr = np.array(time)

            # Create point cloud
            points_neural = np.column_stack([neural_v, neural_w, time_arr])
            cloud_neural = pv.PolyData(points_neural)

            # Create line
            cloud_neural["scalars"] = np.arange(len(points_neural))
            tubes_neural = cloud_neural.tube(radius=0.01)

            plotter.add_mesh(tubes_neural, scalars="scalars", cmap="viridis",
                           label="Neural Trajectory")

            # Cardiac trajectory (x, y, t) in 3D
            cardiac_x = np.array([x for x, y in cardiac])
            cardiac_y = np.array([y for x, y in cardiac])

            points_cardiac = np.column_stack([cardiac_x, cardiac_y, time_arr])
            cloud_cardiac = pv.PolyData(points_cardiac)

            cloud_cardiac["scalars"] = np.arange(len(points_cardiac))
            tubes_cardiac = cloud_cardiac.tube(radius=0.01)

            plotter.add_mesh(tubes_cardiac, scalars="scalars", cmap="plasma",
                           label="Cardiac Trajectory")

            # Set labels
            plotter.add_axes_at_origin(labels_off=False)
            plotter.add_legend()

            # Export to HTML
            html_str = plotter.export_html("trajectory_3d.html", backend="html")

            return html_str

        except ImportError:
            print("PyVista not installed. Install with: pip install pyvista")
            return None

    @staticmethod
    def create_plotly_3d_surface(neural: List[Tuple[float, float]],
                                cardiac: List[Tuple[float, float]],
                                time: List[float]) -> Dict[str, Any]:
        """
        Create 3D surface plot using Plotly.

        Args:
            neural: Neural state (v, w)
            cardiac: Cardiac state (x, y)
            time: Time values

        Returns:
            Plotly figure dictionary
        """
        try:
            import plotly.graph_objects as go

            # Extract data
            neural_v = np.array([v for v, w in neural])
            neural_w = np.array([w for v, w in neural])
            cardiac_x = np.array([x for x, y in cardiac])
            cardiac_y = np.array([y for x, y in cardiac])
            time_arr = np.array(time)

            # Create 3D scatter plots
            fig = go.Figure()

            # Neural trajectory
            fig.add_trace(go.Scatter3d(
                x=neural_v,
                y=neural_w,
                z=time_arr,
                mode='lines',
                name='Neural Trajectory',
                line=dict(color='blue', width=3)
            ))

            # Cardiac trajectory
            fig.add_trace(go.Scatter3d(
                x=cardiac_x,
                y=cardiac_y,
                z=time_arr,
                mode='lines',
                name='Cardiac Trajectory',
                line=dict(color='green', width=3)
            ))

            # Add current position markers
            fig.add_trace(go.Scatter3d(
                x=[neural_v[-1]],
                y=[neural_w[-1]],
                z=[time_arr[-1]],
                mode='markers',
                name='Current Neural',
                marker=dict(color='red', size=8)
            ))

            fig.add_trace(go.Scatter3d(
                x=[cardiac_x[-1]],
                y=[cardiac_y[-1]],
                z=[time_arr[-1]],
                mode='markers',
                name='Current Cardiac',
                marker=dict(color='orange', size=8)
            ))

            # Update layout
            fig.update_layout(
                title="3D Heart-Brain Coupling Trajectories",
                scene=dict(
                    xaxis_title='Neural v / Cardiac x',
                    yaxis_title='Neural w / Cardiac y',
                    zaxis_title='Time (s)',
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.5)
                    )
                ),
                height=700
            )

            return fig.to_dict()

        except ImportError:
            print("Plotly not installed")
            return {}


class SpectrogramVisualizer:
    """Create spectrograms for neural and cardiac signals."""

    @staticmethod
    def create_spectrogram(signal: np.ndarray, sampling_rate: float,
                          title: str = "Spectrogram") -> Figure:
        """
        Create spectrogram plot.

        Args:
            signal: 1D signal array
            sampling_rate: Sampling rate in Hz
            title: Plot title

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Compute spectrogram
        from scipy import signal as sp_signal
        f, t, Sxx = sp_signal.spectrogram(signal, sampling_rate,
                                          nperseg=min(256, len(signal)//4))

        # Plot
        im = ax.pcolormesh(t, f, 10 * np.log10(Sxx + 1e-12), shading='gouraud',
                          cmap='viridis')
        ax.set_ylabel('Frequency (Hz)')
        ax.set_xlabel('Time (s)')
        ax.set_title(title)

        # Colorbar
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label('Power (dB)')

        return fig
