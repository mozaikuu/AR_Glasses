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
import datetime
import re
import base64
from contextlib import asynccontextmanager, AsyncExitStack
from pathlib import Path
import numpy as np
from fastapi import FastAPI, Query, Request
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

    # Start wakeword listening by default when dependencies are available.
    try:
        service = _get_wakeword_service()
        if service:
            service.initialize()
            if service.wakeword_system and not service.wakeword_system.is_running:
                service.start_listening()
            print("[HTTP] Wakeword auto-start attempted", file=sys.stderr)
    except Exception as e:
        print(f"[WARNING] Wakeword auto-start failed: {e}", file=sys.stderr)

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


def _return_wakeword_to_idle():
    """Best-effort reset of wakeword state after request processing."""
    service = _get_wakeword_service()
    if service and service.wakeword_system:
        try:
            service.wakeword_system.return_to_idle()
        except Exception as e:
            print(f"[WARNING] Failed to return wakeword to idle: {e}", file=sys.stderr)


def _maybe_speak_response(text: str, req: MultimodalRequest) -> None:
    """
    Optionally trigger server-side TTS after inference.

    Enabled by default for voice/audio requests and controllable with:
    SERVER_TTS_AFTER_INFERENCE=0
    """
    if not text or not text.strip():
        return

    # Default ON now that browser speech synthesis is disabled.
    enabled = os.getenv("SERVER_TTS_AFTER_INFERENCE", "1").strip() not in {"0", "false", "False"}
    if not enabled:
        return

    # By default, speak both text and audio inference responses.
    # Set SERVER_TTS_FOR_TEXT=0 to mute text-only requests.
    if req.audio is None and os.getenv("SERVER_TTS_FOR_TEXT", "1").strip() in {"0", "false", "False"}:
        return

    def _on_tts_done(task: asyncio.Task) -> None:
        try:
            exc = task.exception()
            if exc:
                print(f"[WARNING] TTS task failed: {exc}", file=sys.stderr)
        except asyncio.CancelledError:
            pass
        except Exception as cb_err:
            print(f"[WARNING] TTS callback failed: {cb_err}", file=sys.stderr)

    try:
        from tools.speech.tts import text_to_speech
        task = asyncio.create_task(text_to_speech(text))
        task.add_done_callback(_on_tts_done)
        print("[HTTP] TTS task scheduled", file=sys.stderr)
    except Exception as e:
        print(f"[WARNING] TTS trigger failed: {e}", file=sys.stderr)


def _local_time_date_answer(user_query: str) -> str | None:
    """Handle simple local date/time questions without invoking tool loops."""
    q = (user_query or "").strip().lower()
    if not q:
        return None

    is_time = any(k in q for k in ("time", "clock", "what time"))
    is_day = any(k in q for k in ("what day", "day is it", "today", "date"))
    has_external_intent = any(k in q for k in ("news", "stock", "price", "weather", "search", "web"))

    if has_external_intent or (not is_time and not is_day):
        return None

    now = datetime.datetime.now().astimezone()
    parts = []
    if is_day:
        parts.append(f"Today is {now.strftime('%A, %B %d, %Y')}.")
    if is_time:
        parts.append(f"The current local time is {now.strftime('%I:%M %p %Z').lstrip('0')}.")
    return " ".join(parts).strip() or None


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
            # #region agent log
            _debug_log(
                "baseline",
                "H4",
                "server/gateway.py:process_multimodal",
                "audio transcription attempted",
                {
                    "audio_bytes_len": len(audio_bytes),
                    "audio_dtype": audio_dtype,
                    "transcribed_len": len(transcribed_text or ""),
                    "transcribed_blank": not bool((transcribed_text or "").strip()),
                },
            )
            # #endregion
            print(f"DEBUG: Transcribed text: '{transcribed_text}' (length: {len(transcribed_text)})", file=sys.stderr)
        except Exception as e:
            # #region agent log
            _debug_log(
                "baseline",
                "H4",
                "server/gateway.py:process_multimodal",
                "audio transcription failed",
                {"error": str(e)},
            )
            # #endregion
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
        _return_wakeword_to_idle()
        return {"response": "No input provided. Please provide text or audio."}

    # Fast-path basic local time/date questions to avoid unnecessary tool loops.
    local_time_answer = _local_time_date_answer(" ".join(text_parts))
    if local_time_answer:
        _maybe_speak_response(local_time_answer, req)
        _return_wakeword_to_idle()
        return {
            "response": local_time_answer,
            "transcription": transcribed_text if transcribed_text else None
        }

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
                _return_wakeword_to_idle()
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
            _return_wakeword_to_idle()
            return {
                "response": f"Error: {error_msg}",
                "transcription": transcribed_text if transcribed_text else None
            }

    _maybe_speak_response(result, req)
    _return_wakeword_to_idle()
    return {
        "response": result,
        "transcription": transcribed_text if transcribed_text else None
    }


def _normalize_location_name(value: str) -> str:
    if not value:
        return ""
    lowered = value.strip().lower().replace("_", " ")
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def _extract_destination_query(command: str) -> str:
    normalized = _normalize_location_name(command)
    prefixes = [
        "go to",
        "navigate to",
        "take me to",
        "guide me to",
        "i want to go to",
        "where is",
        "how do i get to",
    ]
    for prefix in prefixes:
        if normalized.startswith(prefix + " "):
            return normalized[len(prefix):].strip()
    return normalized


def _score_destination(query: str, candidate: str) -> int:
    if not query or not candidate:
        return 0
    if query == candidate:
        return 100
    if candidate.startswith(query):
        return 90
    if query in candidate:
        return 80
    query_tokens = [t for t in query.split(" ") if t]
    if not query_tokens:
        return 0
    hits = sum(1 for token in query_tokens if token in candidate)
    return int((hits / len(query_tokens)) * 70)


@app.post("/unity/voice-command")
async def unity_voice_command(req: dict):
    """
    Structured command router for Unity.
    Returns:
      - action: speak | navigate | cancel_navigation | error
      - response_text: assistant text for TTS/UI
      - destination: destination name when action=navigate
      - intent: high-level intent label
    """
    command = (req.get("command") or "").strip()
    mode = (req.get("mode") or "quick").strip()
    if not command:
        return {
            "action": "error",
            "intent": "invalid",
            "response_text": "I did not hear a command.",
            "destination": None,
            "confidence": 0.0,
        }

    command_lower = command.lower()

    # 1) Fast path for local date/time questions.
    local_answer = _local_time_date_answer(command)
    if local_answer:
        return {
            "action": "speak",
            "intent": "time_date",
            "response_text": local_answer,
            "destination": None,
            "confidence": 0.98,
        }

    # 2) Navigation cancellation intent.
    if any(p in command_lower for p in ("stop navigation", "cancel navigation", "stop guiding", "stop guidance")):
        return {
            "action": "cancel_navigation",
            "intent": "navigation_cancel",
            "response_text": "Okay, navigation has been cancelled.",
            "destination": None,
            "confidence": 0.95,
        }

    # 3) Navigation intent with destination matching.
    is_navigation_intent = any(
        p in command_lower
        for p in ("go to", "navigate to", "take me to", "guide me to", "where is", "direction", "directions")
    )
    if is_navigation_intent:
        try:
            from tools.navigation.navigation import load_graph, get_all_locations
            graph = load_graph()
            locations = get_all_locations(graph)
        except Exception as e:
            return {
                "action": "error",
                "intent": "navigation_error",
                "response_text": f"I could not load navigation locations: {e}",
                "destination": None,
                "confidence": 0.3,
            }

        destination_query = _extract_destination_query(command)
        best = None
        best_score = -1
        for location in locations:
            candidate_norm = _normalize_location_name(location)
            score = _score_destination(destination_query, candidate_norm)
            if score > best_score:
                best_score = score
                best = location

        if best and best_score >= 45:
            return {
                "action": "navigate",
                "intent": "navigation_start",
                "response_text": f"Starting navigation to {best}.",
                "destination": best,
                "confidence": min(0.99, best_score / 100.0),
            }

        return {
            "action": "speak",
            "intent": "navigation_unknown_destination",
            "response_text": "I could not find that destination. Please repeat the location name.",
            "destination": None,
            "confidence": 0.4,
        }

    # 4) General task -> route through your MCP/LLM processing.
    try:
        result = await process_multimodal(MultimodalRequest(text=command, mode=mode))
        response_text = (result.get("response") or "").strip()
        if not response_text:
            response_text = "I could not generate a response. Please try again."
        return {
            "action": "speak",
            "intent": "general_query",
            "response_text": response_text,
            "destination": None,
            "confidence": 0.8,
        }
    except Exception as e:
        return {
            "action": "error",
            "intent": "llm_error",
            "response_text": f"I hit an issue while processing your request: {e}",
            "destination": None,
            "confidence": 0.2,
        }


@app.post("/esp/process")
async def esp_process(req: dict, request: Request):
    """
    ESP-focused text endpoint.
    Returns model response and optional WAV URL for ESP fetch/playback.
    """
    text = (req.get("text") or "").strip()
    mode = req.get("mode") or "quick"
    if not text:
        return {"error": "No text provided"}

    result = await process_multimodal(MultimodalRequest(text=text, mode=mode))
    response_text = (result.get("response") or "").strip()

    # If agent loop returns a generic fallback, try one direct LLM pass.
    if response_text == "I encountered an issue. Please try again.":
        try:
            from agent.llm import generate_chat
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Respond in one concise paragraph."},
                {"role": "user", "content": text},
            ]
            direct = await generate_chat(messages, max_tokens=384, temperature=0.1)
            if isinstance(direct, str) and direct.strip():
                response_text = direct.strip()
        except Exception as e:
            print(f"[WARNING] ESP direct LLM retry failed: {e}", file=sys.stderr)

    tts_url = None
    tts_file = None
    if response_text and not response_text.lower().startswith("error:"):
        try:
            from tools.speech.tts import synthesize_to_wav_file
            wav_path = await asyncio.to_thread(synthesize_to_wav_file, response_text, "esp")
            if wav_path and wav_path.exists():
                tts_file = wav_path.name
                tts_url = str(request.url_for("serve_esp_tts_file", filename=tts_file))
        except Exception as e:
            print(f"[WARNING] ESP TTS synth failed: {e}", file=sys.stderr)

    return {
        "response": response_text,
        "tts_url": tts_url,
        "tts_file": tts_file,
        "transcription": result.get("transcription"),
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


@app.get("/esp/tts/{filename}", name="serve_esp_tts_file")
async def serve_esp_tts_file(filename: str):
    """Serve generated WAV for ESP playback."""
    from config.settings import TTS_OUTPUT_DIR
    filepath = Path(TTS_OUTPUT_DIR) / filename
    if filepath.exists():
        return FileResponse(str(filepath), media_type="audio/wav")
    return {"error": "Audio file not found"}


@app.get("/config")
async def get_config():
    """Get wake word configuration."""
    from config.settings import WAKE_WORDS
    return {
        "wake_words": WAKE_WORDS,
        "selected_mic_index": _get_selected_mic_index(),
    }


# ==================== WEB APP COMPATIBILITY ENDPOINTS ====================

# Simple in-memory state for web dashboard transient UI flags
_webapp_state = {
    "ai_response": None,
    "error_message": None,
    "selected_mic_index": None,
    "last_updated": None
}

# QR marker state for gateway-facing clients (e.g., Unity on HoloLens 2)
_gateway_active_qr = {}
_gateway_qr_telemetry = []
_MAX_GATEWAY_QR_TELEMETRY = 200


def _debug_log(run_id: str, hypothesis_id: str, location: str, message: str, data: dict):
    try:
        payload = {
            "sessionId": "150f1d",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open("debug-150f1d.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        pass


def _update_state(**kwargs):
    """Update web app state."""
    import time
    _webapp_state.update(kwargs)
    _webapp_state["last_updated"] = time.time()


def _consume_ui_flags():
    flags = {
        "ai_response": _webapp_state["ai_response"],
        "error_message": _webapp_state["error_message"],
    }
    _webapp_state["ai_response"] = None
    _webapp_state["error_message"] = None
    return flags


def _get_wakeword_service():
    try:
        from web_app.services import wakeword_service
        # #region agent log
        _debug_log(
            "baseline",
            "H2",
            "server/gateway.py:_get_wakeword_service",
            "wakeword service import ok",
            {"service_exists": wakeword_service is not None},
        )
        # #endregion
        return wakeword_service
    except Exception as e:
        # #region agent log
        _debug_log(
            "baseline",
            "H2",
            "server/gateway.py:_get_wakeword_service",
            "wakeword service import failed",
            {"error": str(e)},
        )
        # #endregion
        _update_state(error_message=f"Wakeword service unavailable: {e}")
        return None


def _list_input_devices():
    """List available input microphones."""
    devices = []
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                devices.append({
                    "index": i,
                    "name": info.get("name", f"Input {i}"),
                    "channels": int(info.get("maxInputChannels", 0)),
                    "default_rate": int(info.get("defaultSampleRate", 16000)),
                })
        p.terminate()
    except Exception as e:
        _update_state(error_message=f"Failed to list microphones: {e}")
    return devices


def _get_selected_mic_index():
    service = _get_wakeword_service()
    if service and service.device_index is not None:
        return int(service.device_index)
    return _webapp_state.get("selected_mic_index")


@app.get("/audio/devices")
async def get_audio_devices():
    devices = _list_input_devices()
    selected = _get_selected_mic_index()
    # #region agent log
    _debug_log(
        "baseline",
        "H3",
        "server/gateway.py:get_audio_devices",
        "listed audio devices",
        {"device_count": len(devices), "selected_index": selected},
    )
    # #endregion
    return {"devices": devices, "selected_index": selected}


@app.post("/audio/select")
async def select_audio_device(req: dict):
    raw_index = req.get("device_index", None)
    if raw_index in ("", None):
        return {"success": False, "error": "device_index is required"}

    try:
        device_index = int(raw_index)
    except Exception:
        return {"success": False, "error": "device_index must be an integer"}

    devices = _list_input_devices()
    valid_indices = {d["index"] for d in devices}
    if device_index not in valid_indices:
        return {"success": False, "error": f"Invalid microphone index: {device_index}", "devices": devices}

    _update_state(selected_mic_index=device_index)
    service = _get_wakeword_service()
    if service:
        try:
            service.set_input_device(device_index)
        except Exception as e:
            return {"success": False, "error": f"Failed to apply mic to wakeword: {e}", "selected_index": device_index}

    return {"success": True, "selected_index": device_index}


@app.get("/status")
async def get_status(consume: bool = False):
    """Get web dashboard status (replaces Flask /status)."""
    service = _get_wakeword_service()
    if service:
        service.initialize()
        status_data = service.get_status()
    else:
        status_data = {
            "is_running": False,
            "system_state": "idle",
            "wake_word_detected": False,
            "last_wake_word": None,
            "command_received": False,
            "command_text": None,
            "error_message": _webapp_state.get("error_message"),
        }

    if consume:
        if service:
            service.clear_flags()
        status_data = {**status_data, **_consume_ui_flags()}
    else:
        status_data = {
            **status_data,
            "ai_response": None,
            "error_message": _webapp_state.get("error_message"),
        }
    return status_data


@app.post("/control/start")
async def start_listening():
    """Start wake word listening (replaces Flask /control/start)."""
    service = _get_wakeword_service()
    if not service:
        return {"status": "error", "error": _webapp_state.get("error_message")}

    selected_mic = _webapp_state.get("selected_mic_index")
    # #region agent log
    _debug_log(
        "baseline",
        "H2",
        "server/gateway.py:start_listening",
        "start listening requested",
        {
            "service_exists": service is not None,
            "selected_mic": selected_mic,
            "service_device_index": getattr(service, "device_index", None) if service else None,
        },
    )
    # #endregion
    if selected_mic is not None and service.device_index != selected_mic:
        try:
            service.set_input_device(int(selected_mic))
        except Exception as e:
            return {"status": "error", "error": f"Selected mic failed: {e}"}

    service.initialize()
    if service.wakeword_system is None:
        return {"status": "error", "error": service.results.get("error_message", "Wakeword init failed")}
    service.start_listening()
    return {"status": "started"}


@app.post("/control/stop")
async def stop_listening():
    """Stop wake word listening (replaces Flask /control/stop)."""
    service = _get_wakeword_service()
    if not service:
        return {"status": "error", "error": _webapp_state.get("error_message")}
    if service.wakeword_system is None:
        return {"status": "error", "error": service.results.get("error_message", "Wakeword not initialized")}
    service.stop_listening()
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


@app.post("/record")
async def record_audio(req: dict = None):
    """Record audio from server microphone and process it."""
    service = _get_wakeword_service()
    was_running = False
    if service and service.wakeword_system and service.wakeword_system.is_running:
        service.pause()
        was_running = True
        await asyncio.sleep(0.3)

    try:
        import pyaudio

        format_ = pyaudio.paInt16
        channels = 1
        rate = 16000
        chunk = 1024
        record_seconds = 5

        p = pyaudio.PyAudio()
        device_index = None
        requested_index = None
        if req and req.get("device_index") is not None:
            try:
                requested_index = int(req.get("device_index"))
            except Exception:
                requested_index = None

        preferred_indices = []
        if requested_index is not None:
            preferred_indices.append(requested_index)
        selected_index = _webapp_state.get("selected_mic_index")
        if selected_index is not None:
            preferred_indices.append(int(selected_index))
        if service and service.device_index is not None:
            preferred_indices.append(int(service.device_index))

        for idx in preferred_indices:
            try:
                info = p.get_device_info_by_index(idx)
                if info.get("maxInputChannels", 0) > 0:
                    device_index = idx
                    break
            except Exception:
                continue

        if device_index is None:
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    device_index = i
                    break

        if device_index is None:
            # #region agent log
            _debug_log(
                "baseline",
                "H3",
                "server/gateway.py:record_audio",
                "no microphone found",
                {"requested_index": requested_index, "preferred_indices": preferred_indices},
            )
            # #endregion
            return {"error": "No microphone found"}

        # #region agent log
        _debug_log(
            "baseline",
            "H3",
            "server/gateway.py:record_audio",
            "microphone selected for recording",
            {"device_index": device_index, "preferred_indices": preferred_indices},
        )
        # #endregion
        stream = p.open(
            format=format_,
            channels=channels,
            rate=rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk,
        )

        frames = []
        for _ in range(int(rate / chunk * record_seconds)):
            frames.append(stream.read(chunk, exception_on_overflow=False))

        stream.stop_stream()
        stream.close()
        p.terminate()

        audio_data = b"".join(frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0
        if np.max(np.abs(audio_array)) > 1.0:
            audio_array = audio_array / np.max(np.abs(audio_array))

        b64_audio = base64.b64encode(audio_array.tobytes()).decode("utf-8")
        request = MultimodalRequest(mode="quick", audio=b64_audio, audio_dtype="float32")
        result = await process_multimodal(request)
        result["response"] = result.get("response") or result.get("answer") or ""

        _update_state(ai_response=result.get("response"))
        return result
    except Exception as e:
        # #region agent log
        _debug_log(
            "baseline",
            "H4",
            "server/gateway.py:record_audio",
            "record audio failed",
            {"error": str(e)},
        )
        # #endregion
        _update_state(error_message=str(e))
        return {"error": str(e)}
    finally:
        if was_running and service:
            service.resume()


@app.post("/web/record")
async def web_record_audio():
    """Alias for web dashboard compatibility."""
    return await record_audio()

