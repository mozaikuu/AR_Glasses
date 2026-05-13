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
Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «3.4.1 Continuous integration and release hygiene», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.
