## 3.2 Design Overview

The runtime follows a **layered architecture**:

1. **Transport:** FastAPI + Uvicorn ASGI server (`start.py` default).
2. **API layer:** `app/api/gateway.py` validates pydantic models from `app/models/requests.py` and maps to services.
3. **Domain services:** `assistant_service`, `navigation_service`, `qr_service`, `audio_service`, `floorplan_processor`.
4. **Intelligence adapters:** `app/agent/llm.py`, `app/agent/api_llm.py`, `app/agent/agent_loop.py`.
5. **Tooling:** `tools/speech/transcription.py`, `tools/vision/moondream.py`, optional MCP HTTP calls.

## 3.2.1 Module A — API Gateway (`app/api/gateway.py`)

The gateway module constructs `FastAPI` app `app`, registers CORS, and defines routes listed in Appendix A. Startup hooks optionally
start wakeword (`audio_service.start_wakeword`) and spawn a daemon thread for LLM warmup via `assistant_service.compose_answer(text="warmup", mode="quick")`.

## 3.2.2 Module B — Assistant pipeline (`app/services/assistant_service.py`)

The assistant service encapsulates wake-word compilation from configured phrases, transcript normalization, always-listen follow-up windows,
vision intent heuristics, MCP vs local Moondream fallbacks, and final answer composition through `compose_answer`.

## 3.2.3 Module C — Navigation (`app/services/navigation_service.py`)

Navigation loads optional `navigation.json` beside the repo root (two parents up from `navigation_service.py`). It merges authoritative
location ids, aliases, and metadata (floor, coordinates). Sessions live in `_sessions` dict keyed by UUID string.

## 3.2.4 Module D — QR (`app/services/qr_service.py`)

QR service maintains `_active` markers and append-only `_telemetry` entries with UTC timestamps—suitable for demos and lightweight analytics.

## 3.2.5 Module E — Audio (`app/services/audio_service.py`)

Presents a curated device list and tracks selected device id; toggles wakeword running flag used for status reporting.

## 3.2.6 Module F — Floorplan processor (`app/services/floorplan_processor.py`)

Converts LiDAR / textured mesh inputs into multi-floor 2D floorplan JSON using trimesh, numpy, and OpenCV; supports vertical axis selection,
wall face extraction, slicing, and segment filtering (`DEFAULT_MESH_MIN_SEGMENT_M`).

### 3.2.7 Design tradeoffs captured in code

Notable tradeoffs include in-memory navigation sessions, optional MCP calls with local Moondream fallback, and sentence caps on assistant answers. Each encodes a preference for demo stability over maximal cleverness.

CORS wide-open settings may exist for LAN demos; tighten for any public exposure.

Document tradeoffs beside the code blocks you show in the thesis to satisfy methodology rubrics.
