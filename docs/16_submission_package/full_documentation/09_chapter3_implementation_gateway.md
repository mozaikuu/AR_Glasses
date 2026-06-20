## 3.3 Implementation — Gateway (`app/api/gateway.py`)

This section documents the **observable** gateway responsibilities in implementation order relevant to developers.

### Health and diagnostics

- `GET /` returns `HealthResponse` model.
- `GET /debug` exposes runtime flags including MCP reachability via `_probe_mcp`.
- `GET /network/info` enumerates helpful LAN IPs via `_detect_lan_ips`.

### Multimodal processing

- `POST /process` and `POST /run` accept `ProcessRequest` and return `ProcessResponse` after routing to `assistant_service.process`.
- Wakeword rollout adjustments occur in `_apply_wakeword_rollout_scope` before assistant invocation when audio is present.

### Audio UI endpoints

- `GET /audio/devices` lists `audio_service.list_devices()`.
- `POST /audio/select` validates selection.

### Unity and navigation

- `POST /unity/voice-command` validates API key when configured, then delegates to assistant routing for voice commands.
- Navigation endpoints call `navigation_service` methods and return `NavigationSessionResponse` where applicable.

### ESP compatibility

- `POST /esp/process` returns fields compatible with firmware expectations (see code for dual text/response keys).
- `GET /esp/tts/{filename}` streams cached WAV bytes when token resolves.

### QR endpoints

- Visibility and telemetry map directly to `qr_service` methods.

### TTS caching helpers

Private helpers `_store_tts_clip` / `_consume_tts_clip` implement in-memory TTL cache for synthesized audio bytes.

### 3.3.1 Operational notes for gateway deployment

Run `python start.py` from the repo root after activating the virtual environment. Verify `GET /` health, then `GET /network/info` for LAN discovery.

When MCP is unavailable, disable it in settings so clients do not block on long timeouts.

Rotate API keys between development machines; never reuse production keys in screenshots.
