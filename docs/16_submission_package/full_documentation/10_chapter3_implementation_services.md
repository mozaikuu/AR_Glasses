## 3.3 Implementation — Assistant service (detailed)

### Constructor and wake-word compilation

On construction, `AssistantService` merges `settings.wake_words` and `settings.wake_word_aliases`, deduplicates, and compiles regex patterns
with `_compile_wake_patterns` so that multi-token phrases tolerate flexible separators (`_compile_wake_patterns` uses `re.findall` tokenization
and joins tokens with a separator class allowing whitespace and punctuation between wake tokens).

### Wake context and follow-up window

`_append_wake_context` maintains a rolling transcript tail per `client` key bounded by `wake_context_chars`. `_arm_wake_followup` sets a
monotonic deadline for accepting a command continuation after a wake hit without requiring the wake word on the very next chunk—critical
for streaming STT chunk boundaries.

### `process()` audio branch

When `audio_base64` is supplied, `transcribe_audio_detailed` produces `raw_transcript` and debug metadata. If `always_listen` is true and
no wake word is detected, the method may return early with `ignored_audio` metadata explaining `wakeword_not_detected`. When wake word fires
with empty post-wake text, `_arm_wake_followup` arms continuation. Vision shortcuts occur when `image_base64` is set or `_vision_intent(text)` matches.

### Vision fallbacks

`_run_vision_from_image_with_fallback` prefers MCP tool `POST /tools/vision/analyze-image-moondream` when enabled, else local `tools.vision.moondream.analyze_image`.
Camera path mirrors with `/tools/vision/capture-moondream` vs `analyze_live_camera`.

### Post-processing

`_postprocess_answer` strips planning-like preambles and caps sentences using `settings.max_answer_sentences`.

## 3.3 Implementation — Navigation service

`_load_navigation_json` reads optional `navigation.json`; `_seed_fallback_ids` supplies default campus-like ids if JSON absent.
`start` builds a deterministic four-step template including coordinate text when metadata provides `x` and `y`.

## 3.3 Implementation — QR and Audio services

QR service is intentionally minimal—suitable for demonstration and extension. Audio service provides deterministic device entries for UI demos.

## 3.3 Implementation — Floorplan processor

The module is extensive; key public-facing behavior is mesh load via trimesh, wall extraction via face normals relative to `vertical_axis`,
slicing at `slice_height`, and JSON emission for navigation MVP consumption (see `clients/Expo` navigation assets).

### 3.3.2 Implementation lessons learned
Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «3.3.2 Implementation lessons learned», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.
