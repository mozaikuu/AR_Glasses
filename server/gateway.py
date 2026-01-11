"""HTTP gateway for Streamlit to connect to AI directly."""
import asyncio
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from models.requests import MultimodalRequest, TextRequest
from tools.speech.transcription import transcribe_audio_bytes

# Direct LLM access with error handling in endpoints


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Simple lifespan - no complex startup logic
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    try:
        status = {
            "status": "ok",
            "service": "smart-glasses-gateway",
            "llm_integration": "direct-api",
            "transcription": "available",
            "message": "Gateway is running with direct LLM integration"
        }
        return status
    except Exception as e:
        return {"status": "error", "message": f"Health check failed: {str(e)}"}


@app.get("/debug")
async def debug_info():
    """Debug endpoint to check system status."""
    import os
    from pathlib import Path

    project_root = Path(__file__).parent.parent
    python_exe = sys.executable

    return {
        "llm_integration": "direct-api",
        "transcription_engines": ["google-speech", "whisper-fallback"],
        "python_executable": python_exe,
        "project_root": str(project_root),
        "pythonpath": os.environ.get("PYTHONPATH", "not set"),
        "sys_path": sys.path[:5],  # First 5 entries
        "message": "Gateway is running with direct LLM integration and speech transcription"
    }


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
    print(f"DEBUG: Combined text: '{combined_text}'", file=sys.stderr)
    print(f"DEBUG: Text parts: {text_parts}", file=sys.stderr)

    # Determine mode
    mode = req.mode or "quick"
    if not combined_text.strip():
        return {"response": "No input provided. Please provide text or audio."}

    # Process with direct LLM call
    print(f"[HTTP] Calling LLM with mode='{mode}'", file=sys.stderr)
    try:
        from agent.llm import generate_chat
        messages = [{"role": "user", "content": combined_text}]
        result = await generate_chat(messages, max_tokens=512, temperature=0.1)
        print(f"[HTTP] LLM response received: {result[:100]}...", file=sys.stderr)
    except Exception as e:
        error_msg = f"LLM processing failed: {str(e)}"
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        return {
            "response": f"TEST ERROR: {error_msg}",
            "transcription": transcribed_text if transcribed_text else None
        }

    return {
        "response": result,
        "transcription": transcribed_text if transcribed_text else None
    }

