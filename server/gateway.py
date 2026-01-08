"""HTTP gateway for Streamlit to connect to MCP server."""
import asyncio
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastmcp import Client
from fastmcp.client import StdioTransport
from agent.agent_loop import agent_loop
from models.requests import MultimodalRequest, TextRequest
from tools.speech.transcription import transcribe_audio_bytes
from config.settings import MCP_TRANSPORT

# MCP Client
client: Client | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    global client
    try:
        # Use python -m fastmcp to ensure proper module resolution
        import sys
        import os
        from pathlib import Path
        
        python_exe = sys.executable
        project_root = Path(__file__).parent.parent
        
        # Ensure PYTHONPATH includes project root
        current_pythonpath = os.environ.get("PYTHONPATH", "")
        if str(project_root) not in current_pythonpath:
            os.environ["PYTHONPATH"] = str(project_root) + (os.pathsep + current_pythonpath if current_pythonpath else "")
        
        # Add to sys.path for this process
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # Debug info
        print(f"[HTTP] Python executable: {python_exe}", file=sys.stderr)
        print(f"[HTTP] Project root: {project_root}", file=sys.stderr)
        print(f"[HTTP] PYTHONPATH: {os.environ.get('PYTHONPATH', 'not set')}", file=sys.stderr)
        
        # Try importing server module to catch import errors early
        try:
            from server.server import mcp
            print("[HTTP] Server module imported successfully", file=sys.stderr)
        except Exception as import_error:
            print(f"[ERROR] Failed to import server module: {import_error}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            print(f"[ERROR] This will cause MCP client to fail. Fix import errors first.", file=sys.stderr)
            # Continue anyway - the subprocess will show the real error
        
        # Create transport with proper Python executable
        # The subprocess should inherit PYTHONPATH from environment
        transport = StdioTransport(
            command=python_exe,
            args=["server/server.py"]
        )

        print(f"[HTTP] Command: {python_exe} server/server.py", file=sys.stderr)
        
        print(f"[HTTP] Starting MCP client...", file=sys.stderr)
        # print(f"[HTTP] Command: {python_exe} -m fastmcp run server.server:mcp --transport {MCP_TRANSPORT}", file=sys.stderr)
        
        # Try to connect with timeout handling
        try:
            client = await Client(transport).__aenter__()
            print("[HTTP] MCP client ready", file=sys.stderr)
        except Exception as connect_error:
            print(f"[ERROR] MCP client connection failed: {connect_error}", file=sys.stderr)
            print(f"[ERROR] The MCP server subprocess may have crashed. Check:", file=sys.stderr)
            print(f"[ERROR] 1. Is 'fastmcp' installed in the venv?", file=sys.stderr)
            print(f"[ERROR] 2. Can 'server.server:mcp' be imported?", file=sys.stderr)
            print(f"[ERROR] 3. Are all dependencies for server tools installed?", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise  # Re-raise to be caught by outer exception handler
    except Exception as e:
        print(f"[ERROR] Failed to initialize MCP client: {e}", file=sys.stderr)
        print(f"[ERROR] Make sure 'fastmcp' is installed and 'server.server:mcp' is accessible", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Don't fail startup, but client will be None
        client = None
    
    yield
    
    # Shutdown
    if client:
        try:
            await client.__aexit__(None, None, None)
        except Exception as e:
            print(f"[ERROR] Error closing MCP client: {e}", file=sys.stderr)


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    status = {
        "status": "ok" if client is not None else "degraded",
        "service": "smart-glasses-gateway",
        "mcp_client": "connected" if client is not None else "disconnected"
    }
    return status


@app.get("/debug")
async def debug_info():
    """Debug endpoint to check MCP client status."""
    import os
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    python_exe = sys.executable
    
    return {
        "mcp_client_initialized": client is not None,
        "python_executable": python_exe,
        "project_root": str(project_root),
        "pythonpath": os.environ.get("PYTHONPATH", "not set"),
        "sys_path": sys.path[:5],  # First 5 entries
        "message": "Check gateway terminal logs for detailed MCP connection errors" if client is None else "MCP client is connected"
    }


@app.post("/run")
async def run_agent(req: TextRequest):
    """Legacy endpoint for text-only requests."""
    if client is None:
        return {
            "response": "Error: MCP client not initialized. The gateway server started but couldn't connect to the MCP server subprocess. Check the gateway terminal/logs for detailed error messages. Common causes: import errors in server.server module, missing dependencies, or PYTHONPATH issues."
        }
    result = await agent_loop(client, req.text, mode="thinking")
    return {"response": result}


@app.post("/process")
async def process_multimodal(req: MultimodalRequest):
    """
    Process multimodal request (text + image + audio).
    
    Combines all inputs into a unified prompt:
    - Transcribes audio if provided
    - Combines text + transcribed audio
    - Includes image reference if provided
    """
    if client is None:
        return {
            "response": "Error: MCP client not initialized. The gateway server started but couldn't connect to the MCP server subprocess. Check the gateway terminal/logs for detailed error messages. Common causes: import errors in server.server module, missing dependencies, or PYTHONPATH issues."
        }
    
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
    print(f"DEBUG: Combined text: '{combined_text}'", file=sys.stderr)
    print(f"DEBUG: Text parts: {text_parts}", file=sys.stderr)

    # Determine mode
    mode = req.mode or "thinking"
    if not combined_text.strip() and not req.image:
        return {"response": "No input provided. Please provide text, audio, or image."}
    
    # Process with agent
    result = await agent_loop(
        client,
        combined_text,
        mode=mode,
        image=req.image
    )

    return {
        "response": result,
        "transcription": transcribed_text if transcribed_text else None
    }

