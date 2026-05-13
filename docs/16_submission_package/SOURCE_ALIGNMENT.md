# Source alignment (code-first)

This file records **facts taken from the repository implementation**, not from narrative docs. When `docs/` or `README.md` disagree with the code, **the code wins** for submission materials.

**Project team (graduation report):** Ahmed Mohamed Moussa (222101392); Sandy Samy Samir (222101524); Basma Ahmed Elmorsy (221101164).  
**Faculty:** Faculty of Computer Science and Engineering, New Mansoura University.

**Last verified:** 2026-05-09 (update this date and re-run `build/verify-paths.ps1` before each export).

**Repository revision:** run `git rev-parse HEAD` locally and paste the SHA into the Word cover / revision log when submitting.

---

## 1. Launcher (`start.py`)

| Item | From code |
|------|-----------|
| Gateway process | `python -m uvicorn app.api.gateway:app` with `--host` / `--port` from CLI or `settings.api_host` / `settings.api_port` |
| Default host/port | `app/config/settings.py`: `API_HOST` default `0.0.0.0`, `API_PORT` default `8000` |
| Profiles | `--profile production-local` → enables audio sidecar, Streamlit, MCP (Flask off). `gateway-only` → gateway only. Else: flags `--with-audio`, `--with-flask`, `--with-streamlit`, `--with-mcp` or `settings.enable_*` |
| Audio sidecar | `uvicorn app.api.audio_sidecar:app` on `AUDIO_SIDECAR_HOST` / `AUDIO_SIDECAR_PORT` (defaults `0.0.0.0` / `8010`) |
| Streamlit | `streamlit run` + `settings.streamlit_app_path` (default `streamlit_app.py`) |
| Flask (optional) | `python run_flask.py` (file exists at repo root) |
| MCP (optional) | `uvicorn server.server:app` (`server/server.py`) on `MCP_HOST` / `MCP_PORT` (defaults `127.0.0.1` / `8020`) |

---

## 2. Gateway HTTP routes (`app/api/gateway.py`)

Derived from FastAPI decorators in `app/api/gateway.py` (not from markdown API docs).

| Method | Path |
|--------|------|
| GET | `/` |
| GET | `/mic-test` |
| GET | `/mcp-status` |
| GET | `/debug` |
| GET | `/network/info` |
| POST | `/process` |
| POST | `/run` |
| GET | `/audio/devices` |
| POST | `/audio/select` |
| POST | `/control/start` |
| POST | `/control/stop` |
| POST | `/record` |
| POST | `/unity/voice-command` |
| GET | `/navigation/locations` |
| POST | `/navigation/start` |
| POST | `/navigation/next` |
| GET | `/navigation/status` |
| POST | `/navigation/cancel` |
| POST | `/navigate` |
| POST | `/esp/process` |
| GET | `/esp/tts/{filename}` |
| POST | `/qr/visible` |
| POST | `/qr/hidden` |
| GET | `/qr/active` |
| POST | `/qr/telemetry` |

---

## 3. Core backend modules (`app/`)

| Concern | Primary modules |
|---------|-----------------|
| HTTP surface | `app/api/gateway.py`, `app/api/audio_sidecar.py` |
| Assistant / multimodal | `app/services/assistant_service.py` |
| Navigation sessions | `app/services/navigation_service.py` |
| QR state / telemetry | `app/services/qr_service.py` |
| Audio / wakeword | `app/services/audio_service.py` |
| Floorplan helper | `app/services/floorplan_processor.py` |
| LLM | `app/agent/` (e.g. `llm.py`, `api_llm.py` — confirm in tree) |
| Configuration | `app/config/settings.py` (env + optional `local.settings.json`) |

---

## 4. Client projects (`clients/`)

Top-level directories present in the repo:

| Client root | Role (high level) |
|-------------|-------------------|
| `clients/Expo` | Expo / React Native app (navigation MVP, companion, classfinder, etc.) |
| `clients/mobile` | React Native Android project (`com.cerebro.mobile`) |
| `clients/unity` | Unity integration assets |
| `clients/browser` | Web client integration |
| `clients/esp32` | ESP32 firmware / notes |

**Note:** Older docs may mention only Unity or HoloLens; the **live tree** includes Expo and `mobile` as first-class clients. Submission text should name what you actually demo.

---

## 5. Tests and validation

| Area | Location |
|------|----------|
| Python tests | `tests/` (pytest layout — enumerate `tests/` for your report) |
| Client tests | Per-client (`clients/Expo`, `clients/mobile`, etc.) per package config |

Fill concrete commands (e.g. `pytest tests/ -q`) after you confirm the canonical test entrypoint for your branch.

---

## 6. Known doc drift (examples)

| Doc / claim | Codebase reality |
|-------------|------------------|
| `docs/01_overview/system_overview.md` references `server.gateway`, `hololens2-campus-nav` | Gateway is `app.api.gateway:app`; clients live under `clients/` (Expo, mobile, unity, …) |
| Narrative “flask.py at root” | Launcher uses `run_flask.py` when `--with-flask` / `ENABLE_FLASK` |

Update this table whenever you discover additional mismatches between narrative docs and code.

---

## 7. Cross-check: `docs/07_api/api_reference.md`

After generating the route table above, diff against `docs/07_api/api_reference.md`. As of the last manual alignment pass, the **gateway route set** in §2 matches the FastAPI registrations in `app/api/gateway.py`; any future drift should be listed as bullet points below:

- *(None recorded — re-run comparison after editing `gateway.py` or the API reference.)*
