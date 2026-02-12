"""
Unified Smart Glasses Server

Consolidated server that provides:
- HTTP API endpoints (merged from api_v2)
- Web dashboard with static files (replaces Flask on port 5000)
- MCP agent integration
- TTS and speech processing

This replaces the previous 4-process architecture with a single server.
"""
import asyncio
import sys
import os
import json
import time
from contextlib import asynccontextmanager, AsyncExitStack
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from models.requests import MultimodalRequest, TextRequest
from tools.speech.transcription import transcribe_audio_bytes

# Project root for static files
PROJECT_ROOT = Path(__file__).parent.parent

# MCP client for tool access
mcp_client = None # try mcp_session 
mcp_connected = False # try mcp_session.connected

# Get project root
project_root = Path(__file__).parent.parent
mcp_server_path = project_root / "server" / "server.py"


# Store context managers at module level to keep them alive
_stdio_transport_context = None
_mcp_session_context = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    global mcp_client, mcp_connected, _stdio_transport_context, _mcp_session_context, _keepalive_task

    print("[HTTP] Starting gateway server...", file=sys.stderr)
    _keepalive_task = asyncio.create_task(_keepalive_heartbeat())
    stack = AsyncExitStack()

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        print(f"[HTTP] Initializing MCP client connection to {mcp_server_path}", file=sys.stderr)
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(mcp_server_path)],
            env=dict(os.environ, PYTHONPATH=str(project_root))
        )

        read_stream, write_stream = await stack.enter_async_context(stdio_client(server_params))
        mcp_session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
        await mcp_session.initialize()

        tools = await mcp_session.list_tools()
        print(f"[HTTP] MCP connected successfully! Available tools: {[t.name for t in tools.tools]}", file=sys.stderr)

        mcp_client = mcp_session
        mcp_connected = True
        _stdio_transport_context = True
        _mcp_session_context = mcp_session

    except Exception as e:
        print(f"[WARNING] MCP unavailable, running gateway in fallback mode: {e}", file=sys.stderr)
        mcp_connected = False
        mcp_client = None

    try:
        yield
    finally:
        print("[HTTP] Shutting down gateway", file=sys.stderr)
        await stack.aclose()

        if _keepalive_task:
            _keepalive_task.cancel()
            try:
                await _keepalive_task
            except asyncio.CancelledError:
                pass

        mcp_connected = False
        mcp_client = None
        _stdio_transport_context = None
        _mcp_session_context = None


async def _keepalive_heartbeat():
    """Background task to keep connection alive."""
    global mcp_connected
    while True:
        await asyncio.sleep(30)  # Heartbeat every 30 seconds
        # Verify MCP connection is still active
        if mcp_connected and mcp_client:
            try:
                await mcp_client.list_tools()
                print("[HTTP] Keepalive: MCP connection active", file=sys.stderr)
            except Exception as e:
                print(f"[HTTP] Keepalive: MCP connection lost: {e}", file=sys.stderr)
                mcp_connected = False


app = FastAPI(lifespan=lifespan)

# CORS middleware for mobile gateway access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    global mcp_client, mcp_connected
    
    try:
        # Check MCP connection
        mcp_status = "connected" if mcp_connected and mcp_client else "disconnected"
        
        # Try to list tools if connected
        available_tools = []
        if mcp_connected and mcp_client:
            try:
                tools = await mcp_client.list_tools()
                available_tools = [t.name for t in tools.tools]
            except:
                pass
        
        status = {
            "status": "ok" if mcp_connected else "degraded",
            "service": "smart-glasses-gateway",
            "mcp_status": mcp_status,
            "mcp_tools": available_tools,
            "llm_integration": "mcp-agent-loop" if mcp_connected else "fallback-direct",
            "transcription": "available",
            "message": "Gateway is running with MCP integration" if mcp_connected else "Gateway running but MCP not connected"
        }
        return status
    except Exception as e:
        return {"status": "error", "message": f"Health check failed: {str(e)}"}


@app.get("/debug")
async def debug_info():
    """Debug endpoint to check system status."""
    global mcp_client, mcp_connected
    
    python_exe = sys.executable
    
    debug_info = {
        "mcp_connected": mcp_connected,
        "mcp_client_exists": mcp_client is not None,
        "mcp_server_path": str(mcp_server_path),
        "mcp_server_exists": mcp_server_path.exists(),
        "llm_integration": "mcp-agent-loop" if mcp_connected else "fallback-direct",
        "transcription_engines": ["google-speech", "whisper-fallback"],
        "python_executable": python_exe,
        "project_root": str(project_root),
        "pythonpath": os.environ.get("PYTHONPATH", "not set"),
        "sys_path": sys.path[:5],
    }
    
    if mcp_connected and mcp_client:
        try:
            tools = await mcp_client.list_tools()
            debug_info["available_tools"] = [{"name": t.name, "description": t.description} for t in tools.tools]
            debug_info["tool_count"] = len(tools.tools)
        except Exception as e:
            debug_info["tool_list_error"] = str(e)
            debug_info["mcp_connected"] = False  # Mark as disconnected if we can't list tools
    
    return debug_info


@app.get("/mcp-status")
async def mcp_status():
    """Check MCP connection status."""
    global mcp_client, mcp_connected
    
    status = {
        "connected": mcp_connected,
        "client_exists": mcp_client is not None
    }
    
    if mcp_connected and mcp_client:
        try:
            tools = await mcp_client.list_tools()
            status["tools"] = [t.name for t in tools.tools]
            status["tool_count"] = len(tools.tools)
            status["status"] = "ready"
        except Exception as e:
            status["status"] = "error"
            status["error"] = str(e)
            status["connected"] = False
    else:
        status["status"] = "disconnected"
        status["tools"] = []
        status["tool_count"] = 0
    
    return status


@app.post("/run")
async def run_agent(req: TextRequest):
    """Legacy endpoint for text-only requests."""
    try:
        from agent.llm import generate_chat
        messages = [{"role": "user", "content": req.text}]
        result = await generate_chat(messages, max_tokens=512, temperature=0.1)
        return {"response": result}
    except Exception as e:
        error_msg = f"LLM processing failed: {str(e)}"
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        return {"response": f"Error: {error_msg}"}


@app.post("/process")
async def process_multimodal(req: MultimodalRequest):
    """
    Process multimodal request (text + image + audio) using direct LLM calls.

    Combines all inputs into a unified prompt:
    - Transcribes audio if provided
    - Combines text + transcribed audio
    - Uses direct LLM call instead of MCP
    """

    # Transcribe audio if provided
    transcribed_text = ""
    if req.audio:
        try:
            # req.audio is base64 encoded string from JSON
            import base64
            audio_bytes = base64.b64decode(req.audio)
            # Get dtype from request if available (default to float32 for WebRTC)
            audio_dtype = getattr(req, "audio_dtype", "float32")
            transcribed_text = transcribe_audio_bytes(audio_bytes, dtype=audio_dtype)
            print(f"DEBUG: Transcribed text: '{transcribed_text}' (length: {len(transcribed_text)})", file=sys.stderr)
        except Exception as e:
            print(f"Audio transcription error: {e}", file=sys.stderr)
            transcribed_text = "[Audio transcription failed]"

    # Combine text inputs
    text_parts = []
    if req.text:
        text_parts.append(req.text)
    if req.audio:
        # We received audio - include transcription if available
        if transcribed_text and transcribed_text.strip():
            text_parts.append(f"[Voice input: {transcribed_text.strip()}]")
        else:
            # Audio was sent but transcription failed or was empty
            text_parts.append("[Voice input: (unclear audio)]")

    combined_text = " ".join(text_parts) if text_parts else "[No text input]"
    # Force one-paragraph response by embedding instruction in user message
    combined_text = f"INSTRUCTION: Answer this question in ONE SINGLE PARAGRAPH with no headers, no bullet points, no lists, and no formatting. Keep it brief. QUESTION: {combined_text}"
    print(f"DEBUG: Combined text: '{combined_text}'", file=sys.stderr)
    print(f"DEBUG: Text parts: {text_parts}", file=sys.stderr)

    # Determine mode
    mode = req.mode or "quick"
    if not combined_text.strip():
        return {"response": "No input provided. Please provide text or audio."}

    # Process with MCP agent loop (if connected) or fallback to direct LLM
    print(f"[HTTP] Processing request with mode='{mode}'", file=sys.stderr)
    
    global mcp_client, mcp_connected
    
    # Verify MCP connection is still active
    if mcp_connected and mcp_client:
        try:
            # Test connection by listing tools
            tools = await mcp_client.list_tools()
            print(f"[HTTP] MCP connection verified. Available tools: {[t.name for t in tools.tools]}", file=sys.stderr)
        except Exception as e:
            print(f"[WARNING] MCP connection test failed: {e}. Marking as disconnected.", file=sys.stderr)
            mcp_connected = False
    
    if mcp_connected and mcp_client:
        # Use agent loop with MCP tools
        print(f"[HTTP] Using MCP agent loop with tools", file=sys.stderr)
        try:
            from agent.agent_loop import agent_loop
            
            # Verify MCP connection is still working
            try:
                tools_check = await mcp_client.list_tools()
                print(f"[HTTP] MCP connection verified. Tools: {[t.name for t in tools_check.tools]}", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] MCP connection lost: {e}. Falling back to direct LLM.", file=sys.stderr)
                mcp_connected = False
                raise Exception("MCP connection lost")
            
            # Remove the instruction prefix for agent loop - we'll add it to the final response instead
            user_query = combined_text.replace("INSTRUCTION: Answer this question in ONE SINGLE PARAGRAPH with no headers, no bullet points, no lists, and no formatting. Keep it brief. QUESTION: ", "")

            print(f"[HTTP] User query (after cleanup): '{user_query[:200]}...'", file=sys.stderr)
            
            # Run agent loop with MCP client
            agent_result = await agent_loop(mcp_client, user_query, mode, image=req.image)
            if isinstance(agent_result, dict):
                result = agent_result.get("answer", "")
                tool_used = agent_result.get("tool_calls")
                iterations = agent_result.get("iterations", 0)
            else:
                result = str(agent_result)
                tool_used = None
                iterations = 1

            print(f"[HTTP] Agent loop completed in {iterations} iteration(s), tool_used={tool_used}, result length: {len(result) if result else 0}", file=sys.stderr)

            # Add one-paragraph instruction to the final result if it's too long
            if result and ('\n\n' in result or result.count('\n') > 3):
                # Try to extract first paragraph
                paragraphs = result.split('\n\n')
                if paragraphs:
                    result = paragraphs[0]
                else:
                    # Split by single newlines and take first few sentences
                    lines = result.split('\n')
                    result = ' '.join(lines[:3])

            # Ensure one-paragraph response
            if result and '\n\n' in result:
                # Take first paragraph only
                result = result.split('\n\n')[0]
            
        except Exception as e:
            error_msg = f"MCP agent loop failed: {str(e)}"
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            
            # Fallback to direct LLM call
            print(f"[HTTP] Falling back to direct LLM call", file=sys.stderr)
            try:
                from agent.llm import generate_chat
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant. Always respond in exactly ONE SINGLE PARAGRAPH with no headers, no bullet points, no lists, and no formatting. Keep it brief."},
                    {"role": "user", "content": combined_text}
                ]
                result = await generate_chat(messages, max_tokens=512, temperature=0.1)
                print(f"[HTTP] Fallback LLM response received: {result[:100]}...", file=sys.stderr)
            except Exception as e2:
                return {
                    "response": f"Error: Both MCP agent loop and direct LLM failed. MCP error: {error_msg}. LLM error: {str(e2)}",
                    "transcription": transcribed_text if transcribed_text else None
                }
    else:
        # Fallback to direct LLM call if MCP not connected
        print(f"[HTTP] MCP not connected, using direct LLM call", file=sys.stderr)
        try:
            from agent.llm import generate_chat
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Always respond in exactly ONE SINGLE PARAGRAPH with no headers, no bullet points, no lists, and no formatting. Keep it brief."},
                {"role": "user", "content": combined_text}
            ]
            result = await generate_chat(messages, max_tokens=512, temperature=0.1)
            print(f"[HTTP] Direct LLM response received: {result[:100]}...", file=sys.stderr)
        except Exception as e:
            error_msg = f"LLM processing failed: {str(e)}"
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            return {
                "response": f"Error: {error_msg}",
                "transcription": transcribed_text if transcribed_text else None
            }

    return {
        "response": result,
        "transcription": transcribed_text if transcribed_text else None
    }


# ----------------------------
# NAVIGATION ENDPOINTS
# ----------------------------

@app.get("/navigation/locations")
async def get_navigation_locations():
    """Get all available navigation locations."""
    global mcp_client, mcp_connected

    # First check if we can get locations from nav_runner directly
    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from tools.navigation.navigation import load_graph, get_all_locations
        graph = load_graph()
        locations = get_all_locations(graph)
        return {"locations": sorted(locations)}
    except Exception as e:
        print(f"[HTTP] Error loading navigation locations: {e}", file=sys.stderr)
        return {"locations": [], "error": str(e)}


@app.post("/navigation/start")
async def start_navigation(req: dict):
    """Start indoor navigation from start to destination."""
    global mcp_client, mcp_connected

    start = req.get("start")
    destination = req.get("destination")

    if not start or not destination:
        return {"success": False, "error": "Both 'start' and 'destination' are required"}

    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from tools.navigation.nav_runner import start_navigation
        result = start_navigation(start, destination)
        return result
    except Exception as e:
        print(f"[HTTP] Error starting navigation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {"success": False, "error": str(e)}


@app.post("/navigation/next")
async def next_navigation_step(req: dict = None):
    """Get next navigation instruction."""
    global mcp_client, mcp_connected

    session_id = req.get("session_id") if req else None

    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from tools.navigation.nav_runner import next_navigation_step
        result = next_navigation_step(session_id)
        return result
    except Exception as e:
        print(f"[HTTP] Error getting next step: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {"success": False, "error": str(e)}


@app.get("/navigation/status")
async def get_navigation_status(session_id: str = Query(default=None, description="Optional session ID")):
    """Get current navigation status/progress."""
    global mcp_client, mcp_connected

    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from tools.navigation.nav_runner import get_navigation_status
        result = get_navigation_status(session_id)
        return result
    except Exception as e:
        print(f"[HTTP] Error getting navigation status: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {"success": False, "error": str(e)}


@app.post("/navigation/cancel")
async def cancel_navigation(req: dict = None):
    """Cancel active navigation session."""
    global mcp_client, mcp_connected

    session_id = req.get("session_id") if req else None

    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from tools.navigation.nav_runner import cancel_navigation
        result = cancel_navigation(session_id)
        return result
    except Exception as e:
        print(f"[HTTP] Error cancelling navigation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {"success": False, "error": str(e)}


# ----------------------------
# QR PRESENCE ENDPOINTS
# ----------------------------

@app.post("/qr/visible")
async def qr_visible(req: dict):
    """
    Register that a QR marker is visible and return modal-friendly display info.
    """
    qr_data = req.get("qr_data")
    tracking_id = req.get("tracking_id")
    source = req.get("source", "hololens2")
    event_ts = req.get("timestamp", time.time())

    if not qr_data:
        return {"success": False, "error": "qr_data is required"}

    try:
        from tools.navigation.qr_location import update_location_from_qr

        location = update_location_from_qr(qr_data)
        if not location:
            location = json.loads(qr_data)

        if not tracking_id:
            tracking_id = location.get("id") or f"qr_{int(time.time() * 1000)}"

        marker = {
            "tracking_id": tracking_id,
            "source": source,
            "visible": True,
            "seen_at": event_ts,
            "location": location,
        }
        _gateway_active_qr[tracking_id] = marker

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
            "active_count": len(_gateway_active_qr),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/qr/hidden")
async def qr_hidden(req: dict):
    """Register that a QR marker is no longer visible."""
    tracking_id = req.get("tracking_id")
    qr_id = req.get("qr_id")

    if not tracking_id and not qr_id:
        return {"success": False, "error": "tracking_id or qr_id is required"}

    removed = None
    if tracking_id:
        removed = _gateway_active_qr.pop(tracking_id, None)

    if removed is None and qr_id:
        for tid, marker in list(_gateway_active_qr.items()):
            location = marker.get("location", {})
            if location.get("id") == qr_id:
                removed = _gateway_active_qr.pop(tid)
                break

    return {
        "success": True,  # idempotent behavior for clients
        "visible": False,
        "was_active": removed is not None,
        "active_count": len(_gateway_active_qr),
    }


@app.get("/qr/active")
async def qr_active():
    """Get currently visible QR markers."""
    return {
        "active_count": len(_gateway_active_qr),
        "markers": list(_gateway_active_qr.values()),
    }


@app.post("/qr/telemetry")
async def qr_telemetry(req: dict):
    """Store QR-modal telemetry from clients."""
    tracking_id = req.get("tracking_id")
    if not tracking_id:
        return {"success": False, "error": "tracking_id is required"}

    entry = {
        "tracking_id": tracking_id,
        "qr_id": req.get("qr_id"),
        "event": req.get("event", "displayed"),
        "payload": req.get("payload", {}),
        "source": req.get("source", "hololens2"),
        "timestamp": req.get("timestamp", time.time()),
    }
    _gateway_qr_telemetry.append(entry)
    if len(_gateway_qr_telemetry) > _MAX_GATEWAY_QR_TELEMETRY:
        del _gateway_qr_telemetry[:-_MAX_GATEWAY_QR_TELEMETRY]

    return {
        "success": True,
        "logged": True,
        "telemetry_count": len(_gateway_qr_telemetry),
    }


# ==================== WEB DASHBOARD (REPLACES FLASK) ====================

# Mount static files
static_path = PROJECT_ROOT / "web_app" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

templates_path = PROJECT_ROOT / "web_app" / "templates"

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the web dashboard (replaces Flask app on port 5000)."""
    index_path = templates_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse(content="<h1>Smart Glasses Dashboard</h1><p>Template not found.</p>")


@app.get("/web", response_class=HTMLResponse)
async def web_interface():
    """Alternative route for web interface."""
    return await dashboard()


@app.post("/tts/generate")
async def generate_tts_endpoint(req: dict):
    """Generate TTS audio and return file path."""
    text = req.get("text", "")
    if not text:
        return {"error": "No text provided"}

    try:
        from tools.speech.tts import text_to_speech_sync
        # Generate TTS audio
        text_to_speech_sync(text)
        return {"status": "generated", "text": text}
    except Exception as e:
        return {"error": str(e)}


@app.get("/tts/{filename}")
async def serve_tts_file(filename: str):
    """Serve generated TTS audio file."""
    import tempfile
    temp_dir = tempfile.gettempdir()
    filepath = Path(temp_dir) / filename

    if filepath.exists():
        return FileResponse(str(filepath), media_type="audio/mp3")
    return {"error": "Audio file not found"}, 404


@app.get("/config")
async def get_config():
    """Get wake word configuration."""
    from config.settings import WAKE_WORDS
    return {"wake_words": WAKE_WORDS}


# ==================== WEB APP COMPATIBILITY ENDPOINTS ====================

# Simple in-memory state for web dashboard (no Flask dependency)
_webapp_state = {
    "is_running": False,
    "system_state": "idle",  # idle, active, processing
    "wake_word_detected": False,
    "last_wake_word": None,
    "command_received": False,
    "command_text": None,
    "ai_response": None,
    "error_message": None,
    "last_updated": None
}

# QR marker state for gateway-facing clients (e.g., Unity on HoloLens 2)
_gateway_active_qr = {}
_gateway_qr_telemetry = []
_MAX_GATEWAY_QR_TELEMETRY = 200


def _update_state(**kwargs):
    """Update web app state."""
    import time
    _webapp_state.update(kwargs)
    _webapp_state["last_updated"] = time.time()


def _consume_flags():
    """Consume one-time flags (reset after reading)."""
    flags = {
        "wake_word_detected": _webapp_state["wake_word_detected"],
        "last_wake_word": _webapp_state["last_wake_word"],
        "command_received": _webapp_state["command_received"],
        "command_text": _webapp_state["command_text"],
        "ai_response": _webapp_state["ai_response"],
        "error_message": _webapp_state["error_message"],
    }
    # Reset one-time flags
    _webapp_state["wake_word_detected"] = False
    _webapp_state["command_received"] = False
    _webapp_state["ai_response"] = None
    _webapp_state["error_message"] = None
    return flags


@app.get("/status")
async def get_status(consume: bool = False):
    """Get web dashboard status (replaces Flask /status)."""
    if consume:
        flags = _consume_flags()
        return {
            "is_running": _webapp_state["is_running"],
            "system_state": _webapp_state["system_state"],
            **flags
        }
    return {
        "is_running": _webapp_state["is_running"],
        "system_state": _webapp_state["system_state"],
        "wake_word_detected": False,
        "last_wake_word": None,
        "command_received": False,
        "command_text": None,
        "ai_response": None,
        "error_message": None
    }


@app.post("/control/start")
async def start_listening():
    """Start wake word listening (replaces Flask /control/start)."""
    _update_state(is_running=True, system_state="idle")
    return {"status": "started"}


@app.post("/control/stop")
async def stop_listening():
    """Stop wake word listening (replaces Flask /control/stop)."""
    _update_state(is_running=False, system_state="idle")
    return {"status": "stopped"}


@app.post("/web/process")
async def web_process_text(req: dict):
    """
    Process text from web dashboard (replaces Flask /process).
    Note: Using /web/process to avoid conflict with the main /process endpoint.
    """
    text = req.get("text", "")
    mode = req.get("mode", "quick")

    if not text:
        return {"error": "No text provided"}

    try:
        # Update state
        _update_state(system_state="processing")

        # Call the main process endpoint logic
        from models.requests import MultimodalRequest
        request = MultimodalRequest(text=text, mode=mode)
        result = await process_multimodal(request)

        # Extract response
        response_text = result.get("response", "")

        # Update state with response
        _update_state(system_state="idle", ai_response=response_text)

        return {
            "response": response_text,
            "transcription": result.get("transcription")
        }

    except Exception as e:
        _update_state(system_state="idle", error_message=str(e))
        return {"error": str(e)}


@app.post("/web/record")
async def web_record_audio():
    """
    Record audio from web dashboard (replaces Flask /record).
    Note: This is a simplified version that prompts the user to use the /process endpoint instead.
    """
    return {
        "error": "Direct recording not supported in unified server. Please use text input or the /process endpoint with audio data.",
        "suggestion": "Use the text input or upload audio to /process endpoint"
    }

