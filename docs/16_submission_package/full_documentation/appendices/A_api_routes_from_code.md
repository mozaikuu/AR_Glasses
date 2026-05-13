# Appendix A — HTTP route inventory (gateway)

**Source of truth:** `app/api/gateway.py` (verify after any refactor).

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

**Separate ASGI app:** `app/api/audio_sidecar.py` hosts additional audio-oriented routes for the sidecar process launched from `start.py`.

**Cross-check:** compare this table to `docs/07_api/api_reference.md`; any endpoint documented only in Markdown should be flagged for deletion or implementation.
