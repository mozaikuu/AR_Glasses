# Migration Notes

## New Structure

The project has been refactored to a domain-driven architecture:

-  `ui/` - Streamlit frontend
-  `agent/` - LLM agent logic
-  `tools/` - MCP tools (vision, search, speech, navigation)
-  `server/` - MCP server and HTTP gateway
-  `models/` - Data models
-  `config/` - Configuration
-  `shared/` - Shared utilities

## Old Files (Can be removed after verification)

### Duplicate/Replaced Files

-  `src/mcp_server/client.py` → Replaced by `server/gateway.py`
-  `src/mcp_server/http.py` → Replaced by `server/gateway.py`
-  `src/mcp_server/gateway.py` → Replaced by `server/gateway.py`
-  `src/mcp_server/agent.py` → Replaced by `agent/agent_loop.py` and `agent/modes.py`
-  `src/mcp_server/llm.py` → Moved to `agent/llm.py`

### Tool Files (Moved)

-  `src/mcp_server/tools/search_web/search_web.py` → `tools/search/search_web.py`
-  `src/mcp_server/tools/computer_vision/*` → `tools/vision/*`
-  `src/mcp_server/tools/speech_recognition/*` → `tools/speech/transcription.py`
-  `src/mcp_server/tools/text_to_speech/*` → `tools/speech/tts.py`

### UI Files (Moved)

-  `src/streamlit/app.py` → `ui/app.py`

## Running the Application

### Start the HTTP Gateway

```bash
uvicorn server.gateway:app --host localhost --port 8000
```

### Start the Streamlit App

```bash
streamlit run ui/app.py
```

## Configuration

Update environment variables in `config/settings.py` or set them as environment variables:

-  `MODEL_ID` - LLM model identifier
-  `DEVICE` - cuda or cpu
-  `API_HOST` - Gateway host (default: localhost)
-  `API_PORT` - Gateway port (default: 8000)
