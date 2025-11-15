"""
Lab Streaming Layer (LSL) Integration

Provides real-time data streaming capabilities using LSL protocol.

Repository: https://github.com/sccn/liblsl
"""

from typing import Dict, List, Optional, Any
import numpy as np
import time
import threading
from ..data_acquisition.bci_adapter_base import BCIDataPacket, SignalType


class LSLStreamer:
    """
    LSL outlet for streaming BCI data to the network.

    Allows other applications to subscribe to the data stream.
    """

    def __init__(self, stream_name: str, stream_type: str = "EEG",
                 n_channels: int = 8, sampling_rate: float = 250.0,
                 channel_names: Optional[List[str]] = None):
        """
        Initialize LSL outlet.

        Args:
            stream_name: Name of the LSL stream
            stream_type: Type of stream (EEG, ECG, etc.)
            n_channels: Number of channels
            sampling_rate: Sampling rate in Hz
            channel_names: List of channel names
        """
        self.stream_name = stream_name
        self.stream_type = stream_type
        self.n_channels = n_channels
        self.sampling_rate = sampling_rate
        self.channel_names = channel_names or [f"CH{i+1}" for i in range(n_channels)]

        self.outlet = None
        self._is_initialized = False

    def initialize(self) -> bool:
        """
        Create LSL outlet.

        Returns:
            True if successful
        """
        try:
            from pylsl import StreamInfo, StreamOutlet, cf_float32

            # Create stream info
            info = StreamInfo(
                name=self.stream_name,
                type=self.stream_type,
                channel_count=self.n_channels,
                nominal_srate=self.sampling_rate,
                channel_format=cf_float32,
                source_id=f"MultiHeartModel_{self.stream_name}"
            )

            # Add channel metadata
            channels = info.desc().append_child("channels")
            for name in self.channel_names:
                ch = channels.append_child("channel")
                ch.append_child_value("label", name)
                ch.append_child_value("unit", "microvolts")
                ch.append_child_value("type", self.stream_type)

            # Create outlet
            self.outlet = StreamOutlet(info)
            self._is_initialized = True

            print(f"LSL outlet created: {self.stream_name} ({self.stream_type}, {self.n_channels} channels, {self.sampling_rate} Hz)")
            return True

        except ImportError:
            print("Error: pylsl not found. Install with: pip install pylsl")
            return False
        except Exception as e:
            print(f"LSL initialization error: {e}")
            return False

    def push_packet(self, packet: BCIDataPacket):
        """
        Push a BCI data packet to the LSL stream.

        Args:
            packet: BCIDataPacket to stream
        """
        if not self._is_initialized or self.outlet is None:
            return

        try:
            # Push each sample with timestamp
            n_samples = packet.n_samples

            for i in range(n_samples):
                sample = packet.data[:, i].tolist()
                timestamp = packet.timestamp + i / packet.sampling_rate
                self.outlet.push_sample(sample, timestamp)

        except Exception as e:
            print(f"LSL push error: {e}")

    def push_chunk(self, data: np.ndarray, timestamps: Optional[np.ndarray] = None):
        """
        Push a chunk of data to LSL.

        Args:
            data: NumPy array of shape (n_channels, n_samples)
            timestamps: Optional timestamps for each sample
        """
        if not self._is_initialized or self.outlet is None:
            return

        try:
            # Transpose to (n_samples, n_channels) for LSL
            chunk = data.T.tolist()

            if timestamps is not None:
                self.outlet.push_chunk(chunk, timestamps.tolist())
            else:
                self.outlet.push_chunk(chunk)

        except Exception as e:
            print(f"LSL chunk push error: {e}")

    def close(self):
        """Close the LSL outlet."""
        if self.outlet is not None:
            del self.outlet
            self.outlet = None
            self._is_initialized = False
            print(f"LSL outlet closed: {self.stream_name}")


class LSLReceiver:
    """
    LSL inlet for receiving data from LSL streams.

    Allows receiving data from other BCI applications.
    """

    def __init__(self, stream_name: Optional[str] = None,
                 stream_type: Optional[str] = None,
                 timeout: float = 5.0):
        """
        Initialize LSL receiver.

        Args:
            stream_name: Name of stream to connect to (None = first available)
            stream_type: Type of stream (None = any type)
            timeout: Timeout for finding stream in seconds
        """
        self.stream_name = stream_name
        self.stream_type = stream_type
        self.timeout = timeout
        self.inlet = None
        self._is_connected = False

    def connect(self) -> bool:
        """
        Connect to LSL stream.

        Returns:
            True if successful
        """
        try:
            from pylsl import StreamInlet, resolve_byprop, resolve_stream

            # Resolve streams
            print(f"Searching for LSL stream (timeout={self.timeout}s)...")

            if self.stream_name:
                streams = resolve_byprop('name', self.stream_name, timeout=self.timeout)
            elif self.stream_type:
                streams = resolve_byprop('type', self.stream_type, timeout=self.timeout)
            else:
                streams = resolve_stream(timeout=self.timeout)

            if not streams:
                print("No LSL streams found")
                return False

            # Connect to first matching stream
            stream_info = streams[0]
            self.inlet = StreamInlet(stream_info, max_buflen=360)

            # Get stream info
            info = self.inlet.info()
            self.n_channels = info.channel_count()
            self.sampling_rate = info.nominal_srate()
            self.actual_stream_name = info.name()
            self.actual_stream_type = info.type()

            # Get channel names
            self.channel_names = []
            channels = info.desc().child("channels")
            if not channels.empty():
                ch = channels.child("channel")
                for _ in range(self.n_channels):
                    self.channel_names.append(ch.child_value("label"))
                    ch = ch.next_sibling()
            else:
                self.channel_names = [f"CH{i+1}" for i in range(self.n_channels)]

            self._is_connected = True
            print(f"Connected to LSL stream: {self.actual_stream_name} "
                  f"({self.actual_stream_type}, {self.n_channels} channels, "
                  f"{self.sampling_rate} Hz)")

            return True

        except ImportError:
            print("Error: pylsl not found. Install with: pip install pylsl")
            return False
        except Exception as e:
            print(f"LSL connection error: {e}")
            return False

    def pull_packet(self, timeout: float = 1.0) -> Optional[BCIDataPacket]:
        """
        Pull one data packet from LSL stream.

        Args:
            timeout: Timeout in seconds

        Returns:
            BCIDataPacket if available, None otherwise
        """
        if not self._is_connected or self.inlet is None:
            return None

        try:
            sample, timestamp = self.inlet.pull_sample(timeout=timeout)

            if sample is None:
                return None

            # Convert to BCIDataPacket
            data = np.array(sample, dtype=np.float32).reshape(-1, 1)

            # Determine signal type
            signal_type = SignalType.EEG
            if self.actual_stream_type.upper() in SignalType.__members__:
                signal_type = SignalType[self.actual_stream_type.upper()]

            packet = BCIDataPacket(
                timestamp=timestamp,
                signal_type=signal_type,
                channels=self.channel_names,
                data=data,
                sampling_rate=self.sampling_rate,
                metadata={
                    'stream_name': self.actual_stream_name,
                    'stream_type': self.actual_stream_type,
                    'source': 'LSL'
                }
            )

            return packet

        except Exception as e:
            print(f"LSL pull error: {e}")
            return None

    def pull_chunk(self, timeout: float = 0.0, max_samples: int = 1024) -> Optional[BCIDataPacket]:
        """
        Pull a chunk of data from LSL stream.

        Args:
            timeout: Timeout in seconds (0.0 = immediate)
            max_samples: Maximum number of samples to pull

        Returns:
            BCIDataPacket with chunk data, None if no data
        """
        if not self._is_connected or self.inlet is None:
            return None

        try:
            chunk, timestamps = self.inlet.pull_chunk(timeout=timeout, max_samples=max_samples)

            if not chunk:
                return None

            # Convert to numpy arrays
            data = np.array(chunk, dtype=np.float32).T  # Transpose to (n_channels, n_samples)
            timestamps_arr = np.array(timestamps)

            # Determine signal type
            signal_type = SignalType.EEG
            if self.actual_stream_type.upper() in SignalType.__members__:
                signal_type = SignalType[self.actual_stream_type.upper()]

            packet = BCIDataPacket(
                timestamp=timestamps_arr[0] if len(timestamps_arr) > 0 else time.time(),
                signal_type=signal_type,
                channels=self.channel_names,
                data=data,
                sampling_rate=self.sampling_rate,
                metadata={
                    'stream_name': self.actual_stream_name,
                    'stream_type': self.actual_stream_type,
                    'n_samples': len(chunk),
                    'timestamps': timestamps_arr,
                    'source': 'LSL'
                }
            )

            return packet

        except Exception as e:
            print(f"LSL chunk pull error: {e}")
            return None

    def disconnect(self):
        """Disconnect from LSL stream."""
        if self.inlet is not None:
            del self.inlet
            self.inlet = None
            self._is_connected = False
            print(f"Disconnected from LSL stream: {self.actual_stream_name}")

    @property
    def is_connected(self) -> bool:
        """Check if connected to stream."""
        return self._is_connected


class LSLBridge:
    """
    Bridge between BCI adapters and LSL streams.

    Automatically forwards data from any BCIAdapterBase to LSL.
    """

    def __init__(self, adapter, stream_name: Optional[str] = None):
        """
        Initialize LSL bridge.

        Args:
            adapter: BCIAdapterBase instance
            stream_name: Name for LSL stream (default: adapter name)
        """
        self.adapter = adapter
        self.stream_name = stream_name or adapter.adapter_name

        # Create LSL outlet based on adapter info
        channel_info = adapter.get_channel_info()

        self.streamer = LSLStreamer(
            stream_name=self.stream_name,
            stream_type=channel_info.get('signal_type', 'EEG'),
            n_channels=channel_info.get('n_channels', 8),
            sampling_rate=channel_info.get('sampling_rate', 250.0),
            channel_names=channel_info.get('channel_names')
        )

        self._bridge_active = False

    def start(self) -> bool:
        """
        Start bridging adapter data to LSL.

        Returns:
            True if successful
        """
        if not self.streamer.initialize():
            return False

        # Register callback to forward data
        self.adapter.register_callback(self._forward_to_lsl)
        self._bridge_active = True

        print(f"LSL bridge active: {self.adapter.adapter_name} -> {self.stream_name}")
        return True

    def stop(self):
        """Stop bridging."""
        if self._bridge_active:
            self.adapter.unregister_callback(self._forward_to_lsl)
            self.streamer.close()
            self._bridge_active = False
            print(f"LSL bridge stopped: {self.stream_name}")

    def _forward_to_lsl(self, packet: BCIDataPacket):
        """Forward BCI packet to LSL stream."""
        if self._bridge_active:
            self.streamer.push_packet(packet)

    @property
    def is_active(self) -> bool:
        """Check if bridge is active."""
        return self._bridge_active
