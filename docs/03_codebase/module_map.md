# Codebase Map (Core Only)

## Entry and Startup

- `start.py`: canonical launcher and process supervisor
- `config/settings.py`: environment-driven runtime settings

## Backend

- `server/gateway.py`: main FastAPI app, multimodal processing, wakeword integration, navigation routes
- `server/server.py`: FastMCP tool server
- `server/api_v2.py`: alternate legacy API surface (non-canonical runtime)

## Agent

- `agent/agent_loop.py`: bounded iterative decision + tool-call loop
- `agent/llm.py`: compatibility wrapper around API-based LLM implementation

## Tools

- Speech:
  - `tools/speech/transcription.py` (Google SR -> Whisper fallback)
  - `tools/speech/tts.py` (Piper synthesis, playback, file generation)
- Vision:
  - `tools/vision/moondream.py` (preferred VLM path)
  - `tools/vision/yolo.py` (fallback object detection)
- Navigation:
  - `tools/navigation/navigation.py` (A* graph route + directions)
  - `tools/navigation/nav_runner.py` (session-based step delivery)
- Wakeword:
  - `tools/wakeword/wakeword_system.py` (always-listen state machine)

## Clients

- Flask primary interface target: `flask.py` (**expected but currently missing**)
- Unity MetaQuest base: `hololens2-campus-nav/Assets/Scripts/...`
- Android gateway: `mobile_native/android/app/src/main/java/...`
- ESP32 firmware: `firmware/smart_glasses_esp32/*.ino`

## Known Structural Risk

- `run_flask.py` imports `web_app.create_app`, but `web_app` package is not present in current core tree.
- Path duplication appears (`server/gateway.py` and `server\gateway.py`), indicating potential tooling/path normalization issues on Windows.

