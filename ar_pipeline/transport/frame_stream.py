"""
FrameStream - WebSocket-based video frame streaming

Provides efficient streaming of camera frames from glasses to phone
and AR output from phone to glasses.
"""

import asyncio
import json
import base64
import cv2
import numpy as np
from typing import Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum


class FrameType(Enum):
    """Types of frames that can be streamed."""
    CAMERA_RAW = "camera_raw"
    CAMERA_COMPRESSED = "camera_compressed"
    AR_OUTPUT = "ar_output"
    POSE_DATA = "pose_data"


@dataclass
class StreamConfig:
    """Configuration for frame streaming."""
    jpeg_quality: int = 70
    target_resolution: Tuple[int, int] = (640, 480)
    max_fps: int = 30
    websocket_port: int = 8765


def encode_frame(
    image: np.ndarray,
    quality: int = 70,
    format: str = 'jpeg'
) -> bytes:
    """
    Compress a frame for transmission.
    
    Args:
        image: Input image (BGR format)
        quality: JPEG quality (1-100)
        format: Output format ('jpeg' or 'png')
        
    Returns:
        Compressed image bytes
    """
    # Resize if needed
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    
    if format == 'png':
        encode_params = [cv2.IMWRITE_PNG_COMPRESSION, min(quality // 10, 9)]
    
    success, encoded = cv2.imencode(f'.{format}', image, encode_params)
    
    if not success:
        raise ValueError("Failed to encode frame")
    
    return encoded.tobytes()


def decode_frame(data: bytes, format: str = 'jpeg') -> np.ndarray:
    """
    Decompress a received frame.
    
    Args:
        data: Compressed image bytes
        format: Input format ('jpeg' or 'png')
        
    Returns:
        Decoded image (BGR format)
    """
    nparr = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Failed to decode frame")
    
    return image


def frame_to_base64(image: np.ndarray, quality: int = 70) -> str:
    """
    Convert frame to base64-encoded string for JSON transmission.
    
    Args:
        image: Input image
        quality: JPEG quality
        
    Returns:
        Base64-encoded string (without data:image prefix)
    """
    encoded = encode_frame(image, quality)
    return base64.b64encode(encoded).decode('ascii')


def base64_to_frame(data: str) -> np.ndarray:
    """
    Convert base64 string to image.
    
    Args:
        data: Base64-encoded string (without prefix)
        
    Returns:
        Decoded image
    """
    encoded = base64.b64decode(data)
    return decode_frame(encoded)


class FrameStreamer:
    """
    WebSocket server for streaming frames to clients.
    
    Usage:
        streamer = FrameStreamer(host="0.0.0.0", port=8765)
        await streamer.start()
        # In loop: streamer.broadcast_frame(frame)
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        config: Optional[StreamConfig] = None
    ):
        self.host = host
        self.port = port
        self.config = config or StreamConfig()
        self.clients = set()
        self.server = None
        self.running = False
    
    async def start(self) -> None:
        """Start the WebSocket server."""
        import websockets
        
        self.server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port
        )
        self.running = True
        print(f"FrameStreamer started on ws://{self.host}:{self.port}")
        
        await self.server.wait_closed()
    
    async def _handle_client(self, websocket) -> None:
        """Handle a connected client."""
        self.clients.add(websocket)
        print(f"Client connected. Total: {len(self.clients)}")
        
        try:
            async for message in websocket:
                # Handle incoming messages (pose data, commands)
                await self._process_message(websocket, message)
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            self.clients.remove(websocket)
            print(f"Client disconnected. Total: {len(self.clients)}")
    
    async def _process_message(self, websocket, message: str) -> None:
        """Process incoming message from client."""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'pose':
                # Receive pose data from client
                await self._on_pose_data(data)
            elif msg_type == 'command':
                # Handle commands
                await self._on_command(data)
        except json.JSONDecodeError:
            print(f"Invalid message: {message[:100]}")
    
    async def _on_pose_data(self, data: dict) -> None:
        """Handle received pose data."""
        # Override in subclass
        pass
    
    async def _on_command(self, data: dict) -> None:
        """Handle commands."""
        # Override in subclass
        pass
    
    async def broadcast_frame(
        self,
        frame: np.ndarray,
        frame_type: FrameType = FrameType.AR_OUTPUT
    ) -> None:
        """
        Broadcast a frame to all connected clients.
        
        Args:
            frame: Image to broadcast
            frame_type: Type of frame for client handling
        """
        if not self.clients:
            return
        
        # Compress frame
        compressed = encode_frame(frame, self.config.jpeg_quality)
        
        # Create message
        message = {
            'type': frame_type.value,
            'data': base64.b64encode(compressed).decode('ascii'),
            'timestamp': asyncio.get_event_loop().time()
        }
        
        # Broadcast to all clients
        message_str = json.dumps(message)
        
        # Send to all clients concurrently
        await asyncio.gather(
            *[client.send(message_str) for client in self.clients],
            return_exceptions=True
        )
    
    async def broadcast_pose(
        self,
        rvec: np.ndarray,
        tvec: np.ndarray,
        marker_id: int
    ) -> None:
        """
        Broadcast pose data to clients.
        
        Args:
            rvec: Rotation vector
            tvec: Translation vector
            marker_id: Detected marker ID
        """
        message = {
            'type': FrameType.POSE_DATA.value,
            'marker_id': int(marker_id),
            'rvec': rvec.tolist(),
            'tvec': tvec.tolist(),
            'timestamp': asyncio.get_event_loop().time()
        }
        
        message_str = json.dumps(message)
        
        await asyncio.gather(
            *[client.send(message_str) for client in self.clients],
            return_exceptions=True
        )
    
    async def stop(self) -> None:
        """Stop the server."""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()


class FrameReceiver:
    """
    WebSocket client for receiving frames.
    
    Usage:
        receiver = FrameReceiver("ws://server:8765")
        async with receiver:
            async for frame in receiver.frames():
                process(frame)
    """
    
    def __init__(
        self,
        uri: str,
        config: Optional[StreamConfig] = None
    ):
        self.uri = uri
        self.config = config or StreamConfig()
        self.websocket = None
        self.running = False
    
    async def __aenter__(self) -> 'FrameReceiver':
        """Enter async context."""
        import websockets
        self.websocket = await websockets.connect(self.uri)
        self.running = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
    
    async def receive_frame(self) -> Tuple[np.ndarray, FrameType]:
        """
        Receive a single frame.
        
        Returns:
            (frame, frame_type)
        """
        if not self.websocket:
            raise RuntimeError("Not connected")
        
        message = await self.websocket.recv()
        data = json.loads(message)
        
        frame = base64_to_frame(data['data'])
        frame_type = FrameType(data['type'])
        
        return frame, frame_type
    
    async def send_pose(
        self,
        rvec: np.ndarray,
        tvec: np.ndarray,
        marker_id: int
    ) -> None:
        """
        Send pose data to server.
        
        Args:
            rvec: Rotation vector
            tvec: Translation vector
            marker_id: Marker ID
        """
        if not self.websocket:
            raise RuntimeError("Not connected")
        
        message = {
            'type': FrameType.POSE_DATA.value,
            'marker_id': int(marker_id),
            'rvec': rvec.tolist(),
            'tvec': tvec.tolist()
        }
        
        await self.websocket.send(json.dumps(message))
    
    async def send_command(self, command: str, **kwargs) -> None:
        """
        Send a command to server.
        
        Args:
            command: Command name
            **kwargs: Command arguments
        """
        if not self.websocket:
            raise RuntimeError("Not connected")
        
        message = {
            'type': 'command',
            'command': command,
            **kwargs
        }
        
        await self.websocket.send(json.dumps(message))


async def run_streamer_demo():
    """Demo: Stream camera frames to browser."""
    import websockets
    import asyncio
    
    # Simple demo showing frame streaming
    cap = cv2.VideoCapture(0)
    
    async def stream_frames(websocket):
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize
            frame = cv2.resize(frame, (640, 480))
            
            # Encode and send
            compressed = encode_frame(frame, 70)
            await websocket.send(compressed)
            
            await asyncio.sleep(1/30)  # 30 FPS
    
    print("Demo: Run with 'python -m ar_pipeline.transport.frame_stream'")
    cap.release()


if __name__ == "__main__":
    asyncio.run(run_streamer_demo())
