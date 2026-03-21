# Project Index (Monorepo)

This repository contains multiple sub-projects (Python agent + UI + MCP server, a Unity HoloLens campus navigation app, firmware, mobile, and review prototypes).

## Primary “current” Python stack (agent + UI + server)

- **What it is**: Multimodal assistant (text/voice/image) with a Streamlit UI and an HTTP gateway / MCP server.
- **Start here**: `README.md` and `QUICKSTART.md`
- **Key entrypoints**
  - **Streamlit UI**: `ui/app.py`
  - **Gateway / server startup**: `start_gateway.py`, `start_server.py`, `run_flask.py`
  - **MCP server**: `server/server.py`
  - **Agent loop**: `agent/agent_loop.py`
  - **Config**: `config/settings.py`, `config/model_config.py`
  - **Shared utilities**: `shared/`
  - **Tools (MCP / capabilities)**: `tools/`
- **Dependencies**
  - **uv**: `pyproject.toml`, `uv.lock`
  - **pip**: `requirements.txt`

## Navigation data

- **Root navigation file**: `navigation.json`
- **Unity navigation file**: `hololens2-campus-nav/Assets/StreamingAssets/Campus/navigation.json`
- **Note**: These appear to overlap; decide which one is canonical before deleting/moving either.

## Unity / HoloLens campus navigation app

- **Project**: `hololens2-campus-nav/`
- **What it is**: Unity project targeting XR (HoloLens / OpenXR). Includes navigation, localization, and location info popups.
- **Start here**
  - `hololens2-campus-nav/README.md`
  - `hololens2-campus-nav/Docs/` (some files may be stale per `docs/REPO_CLEANUP_CANDIDATES.md`)
- **Key areas**
  - **Scripts**: `hololens2-campus-nav/Assets/Scripts/`
  - **Streaming assets** (navigation json): `hololens2-campus-nav/Assets/StreamingAssets/`
  - **Project settings**: `hololens2-campus-nav/ProjectSettings/`

## Firmware

- **ESP32 firmware**: `firmware/smart_glasses_esp32/`
- **Docs**:
  - `firmware/smart_glasses_esp32/HARDWARE_WIRING.md`
  - `firmware/smart_glasses_esp32/COMPONENTS_GUIDE.md`
  - `firmware/smart_glasses_esp32/WIFI_PHONE_TEST_GUIDE.md`

## Mobile

- **Native mobile**: `mobile_native/` (see `mobile_native/README.md`)
- **Other mobile prototypes / review builds**: `Review/` (see note below)

## Review prototypes / experiments

- **Review area**: `Review/`
  - `Review/smart_glasses_web/` is a Vite web dashboard prototype (untracked in git status snapshot).
  - Other archived Unity/mobile experiments may exist under `Review/`.
- **Note**: `docs/REPO_CLEANUP_CANDIDATES.md` suggests moving `Review/` to a deprecated/archive area after confirming it’s not actively used.

## Research, analysis, and misc

- **Competitive analysis & reports**: `Comp_Analysis/`
- **Models / wakeword**: `models/`, `wakeword_models/`
- **Utilities / scripts**: `scripts/`, `tools/`, `src/`
- **Temporary work**: `Temp/` (likely not canonical)

## Repo hygiene notes

- **Cleanup candidates**: `docs/REPO_CLEANUP_CANDIDATES.md`

