# Feature Flows

## Multimodal Assistant

1. Client sends text/image/audio.
2. Gateway decodes and transcribes audio if present.
3. Gateway builds combined prompt and selects mode (`quick`/`thinking`).
4. Agent loop may call MCP tools.
5. Response returned; optional TTS triggered.

## Wakeword (Always-On Target)

- Wakeword service initializes at gateway startup when dependencies are available.
- State machine:
  - `IDLE`: listen for wake phrase
  - `ACTIVE`: capture command
  - `PROCESSING`: waiting on backend response
- Watchdog returns stuck state back to `IDLE`.

## Indoor Navigation

- Intent endpoint: `/unity/voice-command`
- Route endpoints: `/navigation/locations`, `/navigation/start`, `/navigation/next`, `/navigation/status`, `/navigation/cancel`
- Unity executes local movement using NavMesh after intent resolution.

## Speech and Audio

- STT: Google SR preferred, Whisper fallback.
- TTS: Piper local generation, with optional immediate playback and ESP WAV serving.
- Android advanced path can stream audio over websocket sidecar.

## ESP32 Integration Modes

- Mode A: ESP32 <-> Android phone via BLE; phone relays to backend.
- Mode B: ESP32 direct server communication over WiFi (intended architecture mode).

