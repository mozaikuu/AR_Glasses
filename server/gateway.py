"""HTTP gateway for Streamlit to connect to AI via MCP."""
import asyncio
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from models.requests import MultimodalRequest, TextRequest
from tools.speech.transcription import transcribe_audio_bytes

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

    # Start keepalive heartbeat task
    _keepalive_task = asyncio.create_task(_keepalive_heartbeat())

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        print(f"[HTTP] Initializing MCP client connection to {mcp_server_path}", file=sys.stderr)

        # Create MCP server parameters
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(mcp_server_path)],
            env=dict(os.environ, PYTHONPATH=str(project_root))
        )

        # Use nested async context managers properly
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as mcp_session:
                # Initialize the session
                await mcp_session.initialize()

                # List available tools
                tools = await mcp_session.list_tools()
                print(f"[HTTP] MCP connected successfully! Available tools: {[t.name for t in tools.tools]}", file=sys.stderr)

                # Store references
                mcp_client = mcp_session
                mcp_connected = True
                _stdio_transport_context = stdio_client(server_params)  # Keep reference
                _mcp_session_context = mcp_session  # Keep reference

                # Yield - context managers stay alive until we exit
                yield

                # Cleanup happens automatically when exiting context

    except Exception as e:
        print(f"[ERROR] Failed to connect to MCP server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        mcp_connected = False
        mcp_client = None

    # Final cleanup
    print("[HTTP] Shutting down gateway", file=sys.stderr)

    # Cancel keepalive task
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
            
            # Check if user explicitly requests tool usage
            tool_requested = False
            tool_name = None
            if "use" in user_query.lower() and "search_web" in user_query.lower():
                tool_requested = True
                tool_name = "search_web"
            elif "use" in user_query.lower() and ("vision" in user_query.lower() or "VisionDetect" in user_query):
                tool_requested = True
                tool_name = "VisionDetect"
            elif ("search" in user_query.lower() and ("web" in user_query.lower() or "internet" in user_query.lower())) or "current time" in user_query.lower():
                tool_requested = True
                tool_name = "search_web"
            
            if tool_requested:
                user_query = f"CRITICAL INSTRUCTION: The user explicitly requested to use the {tool_name} tool. You MUST use this tool to answer their question. Do not say you don't have access to tools - you have access to {tool_name}. Original question: {user_query}"
                print(f"[HTTP] Tool usage explicitly requested: {tool_name}", file=sys.stderr)
            
            print(f"[HTTP] User query (after cleanup): '{user_query[:200]}...'", file=sys.stderr)
            
            # Run agent loop with MCP client
            result = await agent_loop(mcp_client, user_query, mode, image=req.image)
            
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
            
            print(f"[HTTP] Agent loop completed, result length: {len(result) if result else 0}", file=sys.stderr)
            
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

