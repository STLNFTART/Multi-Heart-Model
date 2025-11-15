"""
OpenBCI Adapter

Integrates OpenBCI hardware (Ganglion, Cyton, Daisy) with the Multi-Heart-Model framework.

Repository: https://github.com/OpenBCI/OpenBCI_Python
"""

from typing import Dict, List, Optional, Any
import numpy as np
import time
from .bci_adapter_base import BCIAdapterBase, BCIDataPacket, SignalType


class OpenBCIAdapter(BCIAdapterBase):
    """
    Adapter for OpenBCI hardware devices.

    Supports:
    - Cyton (8 channels)
    - Cyton + Daisy (16 channels)
    - Ganglion (4 channels)
    """

    def __init__(self, port: str = None, board_type: str = "cyton", config: Optional[Dict] = None):
        """
        Initialize OpenBCI adapter.

        Args:
            port: Serial port (e.g., '/dev/ttyUSB0' or 'COM3')
            board_type: 'cyton', 'ganglion', or 'daisy'
            config: Additional configuration
        """
        super().__init__(f"OpenBCI_{board_type}", config)
        self.port = port
        self.board_type = board_type.lower()
        self.board = None

        # Board specifications
        self.board_specs = {
            'cyton': {'channels': 8, 'sampling_rate': 250},
            'daisy': {'channels': 16, 'sampling_rate': 250},
            'ganglion': {'channels': 4, 'sampling_rate': 200}
        }

        if self.board_type not in self.board_specs:
            raise ValueError(f"Unknown board type: {board_type}")

        self.n_channels = self.board_specs[self.board_type]['channels']
        self.sampling_rate = self.board_specs[self.board_type]['sampling_rate']
        self.channel_names = [f"CH{i+1}" for i in range(self.n_channels)]

    def connect(self) -> bool:
        """
        Connect to OpenBCI board.

        Returns:
            True if successful
        """
        try:
            # Try to import OpenBCI library
            try:
                from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
                self._using_brainflow = True
            except ImportError:
                try:
                    import pyOpenBCI
                    self._using_brainflow = False
                except ImportError:
                    print("Error: Neither BrainFlow nor pyOpenBCI found.")
                    print("Install with: pip install brainflow")
                    return False

            if self._using_brainflow:
                # Use BrainFlow (recommended)
                params = BrainFlowInputParams()
                if self.port:
                    params.serial_port = self.port

                # Map board types to BrainFlow IDs
                board_id_map = {
                    'cyton': BoardIds.CYTON_BOARD.value,
                    'daisy': BoardIds.CYTON_DAISY_BOARD.value,
                    'ganglion': BoardIds.GANGLION_BOARD.value
                }

                self.board = BoardShim(board_id_map[self.board_type], params)
                self.board.prepare_session()

                # Get actual channel info from BrainFlow
                self.eeg_channels = BoardShim.get_eeg_channels(board_id_map[self.board_type])
                self.n_channels = len(self.eeg_channels)
                self.sampling_rate = BoardShim.get_sampling_rate(board_id_map[self.board_type])

                print(f"Connected to OpenBCI {self.board_type} via BrainFlow")
            else:
                # Use legacy pyOpenBCI
                if self.board_type == 'cyton' or self.board_type == 'daisy':
                    self.board = pyOpenBCI.OpenBCICyton(
                        port=self.port,
                        daisy=self.board_type == 'daisy'
                    )
                elif self.board_type == 'ganglion':
                    self.board = pyOpenBCI.OpenBCIGanglion(port=self.port)

                print(f"Connected to OpenBCI {self.board_type} via pyOpenBCI")

            return True

        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from OpenBCI board."""
        try:
            if self.board is not None:
                if self._is_streaming:
                    self.stop_stream()

                if self._using_brainflow:
                    self.board.release_session()
                else:
                    self.board.disconnect()

                self.board = None
                print("Disconnected from OpenBCI")
            return True
        except Exception as e:
            print(f"Disconnection error: {e}")
            return False

    def start_stream(self) -> bool:
        """Start streaming data from OpenBCI."""
        if self.board is None:
            print("Error: Not connected to board")
            return False

        try:
            if self._using_brainflow:
                self.board.start_stream()
            else:
                self.board.start_stream(self._openbci_callback)

            self._is_streaming = True

            # Start streaming thread for BrainFlow
            if self._using_brainflow:
                import threading
                self._stream_thread = threading.Thread(target=self._streaming_loop, daemon=True)
                self._stream_thread.start()

            print("Started OpenBCI streaming")
            return True

        except Exception as e:
            print(f"Streaming start error: {e}")
            return False

    def stop_stream(self) -> bool:
        """Stop streaming from OpenBCI."""
        try:
            self._is_streaming = False

            if self._stream_thread is not None:
                self._stream_thread.join(timeout=2.0)
                self._stream_thread = None

            if self.board is not None:
                if self._using_brainflow:
                    self.board.stop_stream()
                else:
                    self.board.stop_stream()

            print("Stopped OpenBCI streaming")
            return True

        except Exception as e:
            print(f"Streaming stop error: {e}")
            return False

    def _acquire_data(self) -> Optional[BCIDataPacket]:
        """Acquire data packet from OpenBCI (BrainFlow mode)."""
        if not self._using_brainflow or self.board is None:
            return None

        try:
            # Get available data
            data = self.board.get_board_data()

            if data.shape[1] == 0:
                time.sleep(0.01)  # Small delay if no data
                return None

            # Extract EEG channels
            eeg_data = data[self.eeg_channels, :]

            # Get timestamp (use first sample timestamp)
            timestamp = time.time()

            # Create packet
            packet = BCIDataPacket(
                timestamp=timestamp,
                signal_type=SignalType.EEG,
                channels=self.channel_names[:self.n_channels],
                data=eeg_data.astype(np.float32),
                sampling_rate=self.sampling_rate,
                metadata={
                    'board_type': self.board_type,
                    'n_samples': data.shape[1],
                    'adapter': 'OpenBCI_BrainFlow'
                }
            )

            return packet

        except Exception as e:
            print(f"Data acquisition error: {e}")
            return None

    def _openbci_callback(self, sample):
        """Callback for legacy pyOpenBCI streaming."""
        try:
            # Extract channel data
            channel_data = np.array(sample.channels_data, dtype=np.float32).reshape(-1, 1)

            packet = BCIDataPacket(
                timestamp=time.time(),
                signal_type=SignalType.EEG,
                channels=self.channel_names,
                data=channel_data,
                sampling_rate=self.sampling_rate,
                metadata={
                    'board_type': self.board_type,
                    'sample_id': sample.id,
                    'adapter': 'OpenBCI_pyOpenBCI'
                }
            )

            # Add to queue
            try:
                self._data_queue.put_nowait(packet)
            except:
                pass  # Queue full

            # Call callbacks
            for callback in self._callbacks:
                try:
                    callback(packet)
                except:
                    pass

        except Exception as e:
            print(f"Callback error: {e}")

    def get_channel_info(self) -> Dict[str, Any]:
        """Get channel information."""
        return {
            'board_type': self.board_type,
            'n_channels': self.n_channels,
            'channel_names': self.channel_names,
            'sampling_rate': self.sampling_rate,
            'signal_type': 'EEG',
            'units': 'microvolts'
        }

    def set_channel_settings(self, channel: int, power_down: bool = False,
                            gain: int = 24, input_type: str = 'normal'):
        """
        Configure individual channel settings.

        Args:
            channel: Channel number (1-indexed)
            power_down: Power down the channel
            gain: Gain setting (1, 2, 4, 6, 8, 12, 24)
            input_type: 'normal', 'shorted', 'bias_meas', 'mvdd', 'temp', etc.
        """
        if not self._using_brainflow and self.board is not None:
            # Legacy pyOpenBCI command string
            # Format: xCHANNELPOWERGAININPUTTYPEBIASSRBLATCH
            pass  # Implement based on OpenBCI command protocol

    def enable_synthetic_square_wave(self, enable: bool = True):
        """Enable/disable synthetic square wave for testing."""
        if self.board is not None and not self._using_brainflow:
            if enable:
                self.board.write_command('[')  # Start square wave
            else:
                self.board.write_command('0')  # Stop square wave
