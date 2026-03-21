# API Reference (Core)

## Base Runtime

- Main backend: `server.gateway` (via `start.py`)
- Default host/port from `config/settings.py` (`API_HOST`, `API_PORT`)

## Core Endpoints

- `GET /` health/status
- `POST /process` multimodal processing (text/image/audio)
- `POST /run` legacy text processing route

## Audio and Wakeword Endpoints

- `GET /audio/devices` list input devices
- `POST /audio/select` select active device
- `POST /control/start` start wakeword listening
- `POST /control/stop` stop wakeword listening
- `POST /record` record and process server-side mic audio

## Unity and Navigation Endpoints

- `POST /unity/voice-command` structured command router
- `GET /navigation/locations`
- `POST /navigation/start`
- `POST /navigation/next`
- `GET /navigation/status`
- `POST /navigation/cancel`

## ESP/Device Endpoints

- `POST /esp/process` ESP-targeted process route with optional WAV response URL
- `GET /esp/tts/{filename}` serve synthesized WAV for ESP playback

## QR/Presence Endpoints

- `POST /qr/visible`
- `POST /qr/hidden`
- `GET /qr/active`
- `POST /qr/telemetry`

## Notes

- Some older routes/scripts may still exist but are not canonical under `start.py`.
- API keys and sensitive config must come from environment variables, not hardcoded values.

