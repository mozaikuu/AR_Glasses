"""
Smart Glasses Server API v2
Mobile-optimized API for ESP32 + Phone Gateway architecture.

Features:
- Minimal payload sizes (compressed data)
- Fast response times
- BLE-friendly packet sizes
- Voice Activity Detection (VAD)
- Context-aware responses
- Hand gesture recognition endpoint

Author: Open Source Smart Glasses Project
License: MIT
"""

import asyncio
import base64
import json
import sys
import time
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import API_HOST, API_PORT, API_URL
from tools.speech.tts import text_to_speech, text_to_speech_sync


# ==================== DATA MODELS ====================

class AudioInput(BaseModel):
    """Compressed audio input from glasses."""
    audio: str = Field(..., description="Base64-encoded audio (mono, 16kHz, 16-bit)")
    sample_rate: int = Field(default=16000, description="Audio sample rate")
    duration_ms: Optional[int] = Field(default=None, description="Audio duration in milliseconds")


class ImageInput(BaseModel):
    """Compressed image input from glasses camera."""
    image: str = Field(..., description="Base64-encoded JPEG image")
    width: int = Field(..., description="Image width")
    height: int = Field(..., description="Image height")
    format: str = Field(default="jpeg", description="Image format (jpeg, png)")


class SensorData(BaseModel):
    """IMU sensor data from glasses."""
    accelerometer: list = Field(default=[0, 0, 0], description="[x, y, z] in m/s^2")
    gyroscope: list = Field(default=[0, 0, 0], description="[x, y, z] in rad/s")
    magnetometer: Optional[list] = Field(default=None, description="[x, y, z] in uT")
    timestamp: Optional[int] = Field(default=None, description="Microseconds since boot")


class GestureInput(BaseModel):
    """Hand gesture detection result from on-device model."""
    gesture: str = Field(..., description="Detected gesture (swipe_left, swipe_right, tap, etc.)")
    confidence: float = Field(default=1.0, description="Confidence score 0-1")
    timestamp: Optional[int] = Field(default=None, description="Microseconds since boot")


class MultimodalInput(BaseModel):
    """Combined input from glasses sensors."""
    audio: Optional[AudioInput] = None
    image: Optional[ImageInput] = None
    sensors: Optional[SensorData] = None
    gesture: Optional[GestureInput] = None
    context: Optional[dict] = Field(default=None, description="Additional context")


class VoiceCommandRequest(BaseModel):
    """Voice command from wake word activation."""
    command: str = Field(..., description="Transcribed voice command")
    audio_base64: Optional[str] = Field(default=None, description="Original audio for reprocessing")
    wake_word: str = Field(default="Nova", description="Detected wake word")


class NavigationRequest(BaseModel):
    """Navigation request."""
    current_location: str = Field(..., description="Current location name or ID")
    destination: str = Field(..., description="Destination location name or ID")
    accessibility: bool = Field(default=False, description="Accessible route needed")


class QRVisibleRequest(BaseModel):
    """QR marker detected and currently visible in camera."""
    qr_data: str = Field(..., description="Raw QR payload (JSON string)")
    tracking_id: Optional[str] = Field(default=None, description="Stable tracker ID from Unity")
    source: str = Field(default="hololens2", description="Client source identifier")
    timestamp: Optional[float] = Field(default=None, description="Client timestamp (epoch seconds)")


class QRHiddenRequest(BaseModel):
    """QR marker is no longer visible."""
    tracking_id: str = Field(..., description="Stable tracker ID from Unity")
    qr_id: Optional[str] = Field(default=None, description="Optional QR location ID")
    source: str = Field(default="hololens2", description="Client source identifier")
    timestamp: Optional[float] = Field(default=None, description="Client timestamp (epoch seconds)")


class QRTelemetryRequest(BaseModel):
    """Client telemetry while QR modal is shown."""
    tracking_id: str = Field(..., description="Stable tracker ID from Unity")
    qr_id: Optional[str] = Field(default=None, description="QR location ID")
    event: str = Field(default="displayed", description="Telemetry event name")
    payload: dict = Field(default_factory=dict, description="Additional event payload")
    source: str = Field(default="hololens2", description="Client source identifier")
    timestamp: Optional[float] = Field(default=None, description="Client timestamp (epoch seconds)")


class ResponseOutput(BaseModel):
    """Response to send back to glasses."""
    text: str = Field(..., description="Text response for TTS")
    audio_url: Optional[str] = Field(default=None, description="URL to pre-generated audio")
    navigation_instruction: Optional[str] = Field(default=None, description="Navigation step")
    action: Optional[str] = Field(default=None, description="Action to take (vibrate, flash, etc.)")
    urgency: str = Field(default="normal", description="Priority level (low, normal, high, critical)")
    confidence: float = Field(default=1.0, description="Response confidence")


# ==================== GLOBAL STATE ====================

# Store recent context for context-aware responses
_context_history: list = []
_MAX_CONTEXT_HISTORY = 10

# Conversation memory
_conversation_memory: list = []

# Active navigation sessions
_navigation_sessions: dict = {}

# Active QR markers currently visible by tracking_id
_active_qr_markers: dict = {}

# Recent QR telemetry events from clients
_qr_telemetry_log: list = []
_MAX_QR_TELEMETRY = 200


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager with background tasks."""
    print("[API v2] Starting Smart Glasses Server v2...")
    print("[API v2] Features: VAD, Context-Aware, Gesture Recognition")

    # Start background context cleanup task
    cleanup_task = asyncio.create_task(_context_cleanup())

    yield

    # Cleanup
    cleanup_task.cancel()
    print("[API v2] Shutting down...")


async def _context_cleanup():
    """Periodic cleanup of old context data."""
    while True:
        await asyncio.sleep(60)  # Every minute
        global _context_history
        if len(_context_history) > _MAX_CONTEXT_HISTORY:
            _context_history = _context_history[-_MAX_CONTEXT_HISTORY:]


# ==================== APP SETUP ====================

app = FastAPI(
    title="Smart Glasses API v2",
    description="Mobile-optimized API for ESP32 Smart Glasses",
    version="2.0.0",
    lifespan=lifespan
)

# CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== HELPER FUNCTIONS ====================

def _update_context(context_data: dict):
    """Update conversation context."""
    global _context_history
    context_data["timestamp"] = time.time()
    _context_history.append(context_data)
    if len(_context_history) > _MAX_CONTEXT_HISTORY:
        _context_history.pop(0)


def _get_recent_context() -> dict:
    """Get recent context for context-aware responses."""
    if not _context_history:
        return {}
    return _context_history[-1]


def _add_to_memory(role: str, content: str):
    """Add to conversation memory."""
    global _conversation_memory
    _conversation_memory.append({"role": role, "content": content, "timestamp": time.time()})
    # Keep last 20 turns
    if len(_conversation_memory) > 20:
        _conversation_memory.pop(0)


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """API status check."""
    return {
        "status": "online",
        "version": "2.0.0",
        "features": ["vad", "context_aware", "gesture_recognition", "navigation"],
        "architecture": "ESP32 + Phone Gateway + Server"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "uptime_seconds": time.time(),
        "memory_usage": "N/A",  # Could add psutil
        "context_items": len(_context_history),
        "conversation_turns": len(_conversation_memory)
    }


# -------------------- VOICE ENDPOINTS --------------------

@app.post("/v2/voice/transcribe", response_model=dict)
async def transcribe_audio(request: VoiceCommandRequest):
    """
    Transcribe voice command with wake word removal.

    This endpoint is called when wake word is detected on device.
    Returns transcribed text with wake word removed.
    """
    command = request.command

    # Remove wake word if present
    wake_words = ["nova", "hey nova", "hey", "ok nova"]
    command_lower = command.lower()
    for wake in wake_words:
        if command_lower.startswith(wake):
            command = command[len(wake):].strip()
            break

    _add_to_memory("user", command)

    return {
        "transcribed": command,
        "original": request.command,
        "wake_word": request.wake_word,
        "confidence": 0.9  # Would come from STT engine
    }


@app.post("/v2/voice/process", response_model=ResponseOutput)
async def process_voice_command(request: VoiceCommandRequest):
    """
    Process voice command and return context-aware response.

    This is the main voice interaction endpoint.
    Includes VAD, speech processing, and context awareness.
    """
    command = request.command

    # Remove wake word
    wake_words = ["nova", "hey nova", "hey", "ok nova"]
    command_lower = command.lower()
    for wake in wake_words:
        if command_lower.startswith(wake):
            command = command[len(wake):].strip()
            break

    # Get context for context-aware response
    context = _get_recent_context()

    # Build conversation history for LLM
    messages = []
    for mem in _conversation_memory[-5:]:  # Last 5 turns
        messages.append({"role": mem["role"], "content": mem["content"]})

    # Process with LLM (simplified - would call actual LLM)
    response_text = await _process_with_llm(command, messages, context)

    _add_to_memory("assistant", response_text)

    return ResponseOutput(
        text=response_text,
        action="speak" if len(response_text) < 200 else "display",
        urgency="normal"
    )


async def _process_with_llm(command: str, history: list, context: dict) -> str:
    """Process command with LLM - simplified version."""
    # This would call the actual LLM
    # For now, return a simple response
    if "navigate" in command.lower() or "direction" in command.lower():
        return "Where would you like to go?"
    elif "what" in command.lower() and "see" in command.lower():
        return "I see a busy environment. What would you like to know?"
    elif "help" in command.lower():
        return "I'm here to help. What do you need assistance with?"
    else:
        return f"I heard: {command}. How can I assist you further?"


# -------------------- VISION ENDPOINTS --------------------

@app.post("/v2/vision/detect")
async def detect_objects(request: ImageInput):
    """
    Detect and describe objects in image from glasses camera.

    Uses Moondream for enhanced vision-language understanding.
    Returns detailed descriptions, objects, and scene analysis.
    """
    try:
        import cv2
        import base64
        from PIL import Image  # Added PIL import
        
        # Decode image
        img_data = base64.b64decode(request.image)
        nparr = np.frombuffer(img_data, dtype=np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        # Check if Moondream should be used
        from config.settings import USE_MOONDREAM
        
        if USE_MOONDREAM:
            try:
                from tools.vision.moondream import load_model
                
                # Load model once
                model, tokenizer = load_model()
                if model is not None:
                    print("Using Moondream for vision detection", file=sys.stderr)
                    
                    # Convert frame to PIL Image for Moondream
                    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                    enc_image = model.encode_image(pil_image)
                    
                    # Get detailed description
                    description = model.query(enc_image, "Describe what you see in detail")["answer"]
                    
                    # Get list of objects
                    objects = model.query(enc_image, "List all objects you see")["answer"]
                    
                    # Get any text visible
                    text = model.query(enc_image, "Extract any text visible")["answer"]
                    
                    return {
                        "description": description,
                        "objects": objects,
                        "text": text if text else "No text detected",
                        "model": "moondream"
                    }
            except Exception as moondream_error:
                print(f"Moondream error: {moondream_error}, falling back to YOLO", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
        
        # Fallback to YOLO
        from ultralytics import YOLO
        model_path = PROJECT_ROOT / "models" / "yolo11n.pt"
        if not model_path.exists():
            model = YOLO("yolo11n.pt")
        else:
            model = YOLO(str(model_path))
        
        results = model(image, conf=0.5)

        detections = []
        for r in results:
            for box in r.boxes:
                detections.append({
                    "class": model.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "bbox": box.xyxy[0].tolist()
                })

        _update_context({"last_vision": {"objects": [d["class"] for d in detections], "count": len(detections)}})

        return {
            "detections": detections,
            "object_count": len(detections),
            "model": "yolo"
        }

    except Exception as e:
        print(f"Vision detection error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v2/vision/scene")
async def analyze_scene(request: ImageInput):
    """
    High-level scene analysis for context-aware understanding.

    Uses Moondream for detailed scene description, activities, and context.
    Returns scene description, activities, and context.
    """
    try:
        import cv2
        import base64
        from PIL import Image
        
        # Decode image
        img_data = base64.b64decode(request.image)
        nparr = np.frombuffer(img_data, dtype=np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        # Check if Moondream should be used
        from config.settings import USE_MOONDREAM
        
        if USE_MOONDREAM:
            try:
                from tools.vision.moondream import load_model
                
                # Load model once
                model, tokenizer = load_model()
                if model is not None:
                    print("Using Moondream for scene analysis", file=sys.stderr)
                    
                    # Convert to PIL Image
                    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                    enc_image = model.encode_image(pil_image)
                    
                    # Get comprehensive scene analysis
                    scene_type = model.query(enc_image, "What type of environment is this?")["answer"]
                    
                    activity = model.query(enc_image, "What activities are happening?")["answer"]
                    
                    lighting = model.query(enc_image, "Describe the lighting conditions")["answer"]
                    
                    safety = model.query(enc_image, "Are there any safety concerns?")["answer"]
                    
                    description = model.query(enc_image, "Give a comprehensive description")["answer"]
                    
                    return {
                        "scene_type": scene_type if scene_type else "unknown",
                        "activity": activity if activity else "unknown",
                        "objects_of_interest": [],
                        "safety_concerns": [s.strip() for s in safety.split('\n') if s.strip() and 'none' not in s.lower()],
                        "lighting": lighting if lighting else "adequate",
                        "description": description,
                        "model": "moondream"
                    }
            except Exception as moondream_error:
                print(f"Moondream scene analysis error: {moondream_error}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
        
        # Fallback
        return {
            "scene_type": "unknown",
            "activity": "unknown",
            "objects_of_interest": [],
            "safety_concerns": [],
            "lighting": "unknown",
            "description": "Moondream not available, YOLO fallback would be needed for scene analysis",
            "model": "none"
        }
    except Exception as e:
        print(f"Scene analysis error: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- GESTURE ENDPOINTS --------------------

@app.post("/v2/gesture/recognize", response_model=dict)
async def recognize_gesture(request: GestureInput):
    """
    Process and validate hand gesture detection.

    Gestures: swipe_left, swipe_right, tap, double_tap, pinch, rotate
    """
    gesture = request.gesture.lower()
    confidence = request.confidence

    valid_gestures = [
        "swipe_left", "swipe_right", "swipe_up", "swipe_down",
        "tap", "double_tap", "pinch", "spread", "rotate_cw", "rotate_ccw",
        "wave", "point", "fist", "peace"
    ]

    if gesture not in valid_gestures:
        return {
            "recognized": False,
            "gesture": request.gesture,
            "suggestion": f"Try: {', '.join(valid_gestures[:5])}"
        }

    # Map gesture to actions
    gesture_actions = {
        "swipe_left": {"action": "previous", "description": "Previous item"},
        "swipe_right": {"action": "next", "description": "Next item"},
        "swipe_up": {"action": "scroll_up", "description": "Scroll up"},
        "swipe_down": {"action": "scroll_down", "description": "Scroll down"},
        "tap": {"action": "select", "description": "Select current item"},
        "double_tap": {"action": "confirm", "description": "Confirm action"},
        "pinch": {"action": "zoom_out", "description": "Zoom out"},
        "spread": {"action": "zoom_in", "description": "Zoom in"},
    }

    action_info = gesture_actions.get(gesture, {"action": "custom", "description": "Custom gesture"})

    _update_context({"last_gesture": gesture, "action": action_info["action"]})

    return {
        "recognized": True,
        "gesture": gesture,
        "confidence": confidence,
        "action": action_info["action"],
        "description": action_info["description"]
    }


# -------------------- NAVIGATION ENDPOINTS --------------------

@app.post("/v2/navigation/start")
async def start_navigation(request: NavigationRequest):
    """Start indoor navigation session."""
    import sys
    from pathlib import Path
    from tools.navigation.navigation import load_graph, find_shortest_path
    from tools.navigation.nav_runner import start_navigation as nav_start

    try:
        result = nav_start(request.current_location, request.destination)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/v2/navigation/next/{session_id}")
async def get_next_instruction(session_id: str):
    """Get next navigation instruction."""
    try:
        from tools.navigation.nav_runner import next_navigation_step
        return next_navigation_step(session_id)
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/v2/navigation/locations")
async def get_locations():
    """Get all available navigation locations."""
    try:
        from tools.navigation.navigation import load_graph, get_all_locations
        graph = load_graph()
        locations = get_all_locations(graph)
        return {"locations": sorted(locations)}
    except Exception as e:
        return {"locations": [], "error": str(e)}


# -------------------- QR PRESENCE ENDPOINTS --------------------

@app.post("/v2/qr/visible")
async def qr_visible(request: QRVisibleRequest):
    """
    Register a QR marker as visible and return modal-ready display data.

    Unity should call this when QR is first detected and on updates while visible.
    """
    from tools.navigation.qr_location import update_location_from_qr

    location = update_location_from_qr(request.qr_data)
    if not location:
        try:
            location = json.loads(request.qr_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid QR payload")

    tracking_id = request.tracking_id or location.get("id") or f"qr_{int(time.time() * 1000)}"
    event_ts = request.timestamp or time.time()

    marker = {
        "tracking_id": tracking_id,
        "source": request.source,
        "visible": True,
        "seen_at": event_ts,
        "location": location,
    }
    _active_qr_markers[tracking_id] = marker
    _update_context({"last_qr": marker})

    display = {
        "id": location.get("id"),
        "name": location.get("name", "Unknown location"),
        "building": location.get("building", ""),
        "floor": location.get("floor"),
        "description": location.get("description", ""),
        "additional_info": location.get("additional_info", ""),
    }

    return {
        "success": True,
        "tracking_id": tracking_id,
        "visible": True,
        "display": display,
        "active_count": len(_active_qr_markers),
    }


@app.post("/v2/qr/hidden")
async def qr_hidden(request: QRHiddenRequest):
    """Register a QR marker as no longer visible."""
    removed = _active_qr_markers.pop(request.tracking_id, None)

    # Fallback: remove by qr_id if tracking_id was not found
    if removed is None and request.qr_id:
        for tid, marker in list(_active_qr_markers.items()):
            location = marker.get("location", {})
            if location.get("id") == request.qr_id:
                removed = _active_qr_markers.pop(tid)
                break

    return {
        "success": True,  # Idempotent for client simplicity
        "tracking_id": request.tracking_id,
        "visible": False,
        "was_active": removed is not None,
        "active_count": len(_active_qr_markers),
    }


@app.get("/v2/qr/active")
async def qr_active():
    """List currently visible QR markers."""
    return {
        "active_count": len(_active_qr_markers),
        "markers": list(_active_qr_markers.values()),
    }


@app.post("/v2/qr/telemetry")
async def qr_telemetry(request: QRTelemetryRequest):
    """Receive QR-modal telemetry from Unity clients."""
    entry = {
        "tracking_id": request.tracking_id,
        "qr_id": request.qr_id,
        "event": request.event,
        "payload": request.payload,
        "source": request.source,
        "timestamp": request.timestamp or time.time(),
    }

    _qr_telemetry_log.append(entry)
    if len(_qr_telemetry_log) > _MAX_QR_TELEMETRY:
        del _qr_telemetry_log[:-_MAX_QR_TELEMETRY]

    _update_context({"last_qr_event": {"event": request.event, "tracking_id": request.tracking_id}})

    return {
        "success": True,
        "logged": True,
        "telemetry_count": len(_qr_telemetry_log),
    }


# -------------------- CONTEXT AWARENESS --------------------

@app.post("/v2/context/update")
async def update_context(data: MultimodalInput):
    """
    Update context with sensor data from glasses.

    This enables context-aware behavior:
    - Detect when user is struggling (slow movement, repeated commands)
    - Proactive suggestions based on environment
    - Adaptive responses based on user state
    """
    context_updates = {}

    if data.gesture:
        context_updates["gesture"] = data.gesture.dict()

    if data.sensors:
        # Analyze movement patterns
        acc = data.sensors.accelerometer
        acc_magnitude = (acc[0]**2 + acc[1]**2 + acc[2]**2)**0.5

        # Detect shaking/struggling (high acceleration variance)
        if acc_magnitude > 20:  # m/s^2
            context_updates["user_state"] = "moving_rapidly"
        elif acc_magnitude < 1:
            context_updates["user_state"] = "still"
        else:
            context_updates["user_state"] = "normal"

    if data.audio:
        # Could add VAD results here
        context_updates["audio_present"] = True

    _update_context(context_updates)

    return {"status": "updated", "context": context_updates}


@app.get("/v2/context/suggest")
async def get_context_suggestions():
    """
    Get proactive suggestions based on context.

    This is where the "Smart Companion" feature lives -
    understanding when the user might need help.
    """
    context = _get_recent_context()

    suggestions = []

    # Check for struggling patterns
    last_gestures = [c for c in _context_history if "gesture" in c]
    if len(last_gestures) > 5:
        repeated_fails = sum(1 for g in last_gestures[-5:] if g.get("action") == "retry")
        if repeated_fails >= 3:
            suggestions.append({
                "type": "proactive_help",
                "message": "You seem to be having trouble. Say 'help' for assistance.",
                "urgency": "low"
            })

    # Time-based suggestions
    import datetime
    hour = datetime.datetime.now().hour
    if 6 <= hour < 9:
        suggestions.append({
            "type": "time_based",
            "message": "Good morning! Your first meeting is at 9 AM.",
            "urgency": "low"
        })

    # Location-based (if available)
    if context.get("location"):
        suggestions.append({
            "type": "location_based",
            "message": f"You're at {context['location']}",
            "urgency": "low"
        })

    return {
        "suggestions": suggestions,
        "user_state": context.get("user_state", "unknown"),
        "context_timestamp": context.get("timestamp")
    }


# -------------------- TTS ENDPOINTS --------------------

@app.post("/v2/tts/synthesize")
async def synthesize_speech(text: str, language: str = "en"):
    """
    Synthesize speech from text using Edge-TTS or Piper TTS.
    
    Returns immediately while TTS plays in background.
    """
    # Start TTS in background (non-blocking) with safe exception handling.
    task = asyncio.create_task(text_to_speech(text))
    def _on_tts_done(t):
        try:
            _ = t.exception()
        except Exception:
            pass
    task.add_done_callback(_on_tts_done)
    
    return {
        "text": text,
        "language": language,
        "status": "playing",
        "message": "TTS started in background"
    }


# -------------------- DEVICE MANAGEMENT --------------------

@app.get("/v2/device/status")
async def get_device_status():
    """Get device connection and capability status."""
    return {
        "connected": True,
        "battery_level": None,  # Would come from device
        "capabilities": {
            "camera": True,
            "microphone": True,
            "speaker": True,
            "imu": True,
            "ble": True,
            "wifi": True
        },
        "firmware_version": "2.0.0",
        "last_sync": time.time()
    }


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    print(f"[API v2] Starting Smart Glasses Server v2 on {API_HOST}:{API_PORT}")
    uvicorn.run(app, host=API_HOST, port=API_PORT + 1)  # Run on port 8001
