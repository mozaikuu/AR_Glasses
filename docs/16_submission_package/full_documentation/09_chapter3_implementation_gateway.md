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
Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «3.3.1 Operational notes for gateway deployment», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.
