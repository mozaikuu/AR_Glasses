# System Architecture

## Runtime Topology

- Process 1 (required): `start.py` -> `uvicorn` -> `server.gateway:app`
- Process 2 (optional): `server_audio.audio_stream_server` (via `start.py --with-audio`)
- MCP subprocess (managed by gateway lifespan): `server/server.py`

## Component Diagram (ASCII)

```text
[ESP32] --BLE/WiFi--> [Android Gateway] --WS--> [server_audio] (optional)
    |                         |                          |
    |                         +------HTTP/WS------------+
    |                                                   v
[Unity MetaQuest] --------HTTP--------------------> [FastAPI gateway]
[Browser/Flask UI] ------HTTP---------------------> [server.gateway]
                                                     |
                                                     v
                                              [MCP server + tools]
                                                     |
                                                     v
                                          [LLM (Cerebras preferred)]
                                          [Local fallback (speech/vision)]
```

## Backend Layers

- API and orchestration: `server/gateway.py`
- Tool execution server: `server/server.py`
- Agent reasoning loop: `agent/agent_loop.py`
- Inference adapter: `agent/llm.py` (delegates to API path)
- Request models: `models/requests.py`

## Design Notes

- Gateway owns end-to-end multimodal orchestration.
- MCP client inside gateway allows tool-aware responses.
- Navigation is hybrid:
  - server-side intent/routing and route data
  - Unity-side NavMesh execution and in-scene movement

## Optional Audio Sidecar

- `server_audio.audio_stream_server` is an optional component.
- Used in advanced setups (not required for all deployments).
- Primary use case: continuous Android streaming and low-friction voice transport.

