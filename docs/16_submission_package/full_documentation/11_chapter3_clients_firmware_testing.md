## 3.3 Implementation — Clients (`clients/`)

### Expo (`clients/Expo`)

Primary mobile codebase using Expo Router. Notable libraries: `clients/Expo/lib/navigation-mvp/` (graph, edges, route), `clients/Expo/lib/indoor-nav/`,
`clients/Expo/lib/building-viewers/` (GLB viewing), `clients/Expo/lib/companion/` for capture and TTS helpers, `clients/Expo/lib/classfinder/` for campus room parsing.

### Mobile Android (`clients/mobile`)

React Native app with Kotlin modules for audio and camera under `clients/mobile/android/app/src/main/java/com/cerebro/mobile/`.

### Firmware (`firmware/`)

`firmware/platformio.ini` defines `native` Unity tests for C++ helpers, and multiple `esp32-wrover-*` environments (`PROFILE_FULL`, `PROFILE_WIFI_ONLY`,
`PROFILE_AUDIO_TEST`, `PROFILE_MINIMAL`, `PROFILE_CAMERA_TEST`, and a camera-only entry variant). Board: `esp-wrover-kit` with PSRAM flags.

## 3.4 Testing

Pytest modules under `tests/` validate gateway contracts, assistant behavior, navigation sessions, QR telemetry, audio service, agent loop, LLM adapter,
models, voice command routing, and a system integration smoke test. Run `pytest tests/ -q` from repository root in the project virtual environment.

## 3.3 System Software (summary)

- **Python:** FastAPI, Uvicorn, pydantic settings.
- **Node:** Expo / React Native client builds.
- **C++/Arduino:** PlatformIO firmware environments.

### Demo runbook (representative lab profile)

1. Create Python venv and install backend requirements per repository instructions.
2. `python start.py` (default `production-local` profile enables gateway, Streamlit, audio sidecar, MCP—adjust flags if MCP unavailable).
3. Point Expo `clients/Expo` API base URL at the LAN IP printed by `/network/info` or configured `PUBLIC_BASE_URL`.
4. Exercise `GET /`, `POST /process` with small JSON, and a navigation session.

### 3.4.1 Continuous integration and release hygiene

A minimal CI pipeline should run `pytest tests/ -q` on pull requests and block merges on failures. Optional jobs can run ruff or mypy if configured.

Tag submission builds with the commit hash printed in the report appendix.

Keep release notes short: what changed in routes, settings, and client environment variables.
