% Smart Glasses Distilled — Graduation Defense
% Ahmed Mohamed Moussa; Sandy Samy Samir; Basma Ahmed Elmorsy
% 2026-05-09

# Smart Glasses Distilled

Multimodal wearable assistant — team defense deck

**Team:** Ahmed Mohamed Moussa (222101392) · Sandy Samy Samir (222101524) · Basma Ahmed Elmorsy (221101164)

**Institution:** Faculty of Computer Science and Engineering — New Mansoura University — Academic year 2025–2026

# Problem

- Indoor and campus movement needs **hands-free** guidance and Q&A
- Phone-first UIs compete for attention while walking
- Wearables need a **single orchestrated backend**, not siloed demos

# Objectives

- One **FastAPI gateway** for text, audio, navigation, QR, and ESP-friendly flows
- **Cloud-first LLM** path with bounded agent loops and safe post-processing
- **Multiple clients**: Expo, mobile, Unity, browser, ESP32 (see `clients/` tree)
- **Testable** architecture: services + HTTP contract + `tests/` pytest suite

# What actually runs

- Launcher: `start.py` → `uvicorn app.api.gateway:app` (default port from `app/config/settings.py`)
- Profiles: `production-local` (gateway + Streamlit + audio sidecar + MCP) vs `gateway-only`
- Optional: `app/api/audio_sidecar.py`, Streamlit app, `run_flask.py`, `server.server:app` for MCP

# System architecture

- **Gateway** `app/api/gateway.py`: HTTP routes, CORS, Unity API key guard when `UNITY_API_KEY` is set
- **Services** `app/services/`: assistant, navigation, QR, audio, floorplan helper
- **Agent** `app/agent/`: `llm.py`, `api_llm.py`, `agent_loop.py`
- **Clients** call HTTP only — thin UI, fat server

# Assistant pipeline

- Entry: `POST /process` and `POST /run` → `assistant_service`
- Wakeword / always-listen policy uses `settings.wakeword_rollout_scope` and client metadata
- Startup warmup thread reduces first-token latency when `preload_on_startup` is enabled

# Navigation

- Endpoints under `/navigation/*` and `POST /navigate`
- `navigation_service`: sessions, steps, cancel — in-memory store (see `app/services/navigation_service.py`)
- Unity path: `POST /unity/voice-command` with optional `X-Unity-Api-Key`

# ESP and TTS

- `POST /esp/process` — compatibility fields in response (see `app/api/gateway.py`)
- `GET /esp/tts/{filename}` — WAV retrieval path for embedded clients

# QR and telemetry

- `POST /qr/visible`, `/qr/hidden`, `GET /qr/active`, `POST /qr/telemetry`
- Demo flows where markers drive context (`app/services/qr_service.py`)

# Clients in this repository

- `clients/Expo` — navigation MVP, companion, classfinder, GLB viewers
- `clients/mobile` — Android React Native (`com.cerebro.mobile`)
- `clients/unity`, `clients/browser`, `clients/esp32` — integration trees; firmware under `firmware/`

**Defense tip:** name only the client surfaces you will live-demo.

# Security and configuration

- Secrets via environment variables and optional `local.settings.json` (`app/config/settings.py`)
- Never put API keys on slides; describe **rotation** and **least privilege** only

# Evaluation approach

- **Automated:** `pytest tests/ -q` at repository root — record passed/failed counts in the written report
- **Manual:** scripted walkthrough: health `GET /`, `POST /process` text, navigation session from Expo or mobile
- **Assets:** stills and clips indexed from `docs/00_Materials/` (213 files in asset library)

# Results (representative — update numbers after your last run)

| Metric | How measured | Representative value |
|--------|----------------|----------------------|
| Pytest suite | `pytest tests/ -q` | Paste “N passed” before defense |
| Gateway cold health | `GET /` after `start.py` | JSON health payload |
| Text round-trip | `POST /process` small prompt | Subjective until instrumented |

# Limitations and future work

- Single-instance navigation sessions; no horizontal session store yet
- Cloud provider dependence for full LLM/STT capability
- Formal user study with statistically significant N — planned future work

# Demo script (about 3 minutes)

1. `python start.py` — default profile `production-local` from `settings.launcher_profile`; use `python start.py --profile gateway-only` if sidecars are unavailable
2. Browser: `http://127.0.0.1:8000/` (or LAN IP from `GET /network/info`) for health JSON
3. `POST /process` with short text JSON body via client or REST tool
4. Start navigation: `POST /navigation/start` then `POST /navigation/next` with returned `session_id`
5. Optional: QR visibility or ESP path if hardware is on the bench

# Thank you

**Smart Glasses Distilled** — New Mansoura University, FCS&E — Team project 2025–2026

Questions?

Speaker notes: keep `docs/16_submission_package/SOURCE_ALIGNMENT.md` synchronized with `app/api/gateway.py` before each milestone review.
