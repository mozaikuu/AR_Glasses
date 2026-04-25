# Smart Glasses Distilled - Full Project Documentation

## 1. Abstract

Smart Glasses Distilled is a multimodal assistant platform that combines voice, text, vision-assisted prompting, and indoor navigation into one wearable-oriented system. The project integrates a Python backend, Unity-based AR navigation client, ESP32 firmware, and web/mobile-facing runtime surfaces.

The design goal is practical assistive interaction: the user should be able to ask questions, request navigation, and receive guidance through lightweight devices in real time. The implementation balances academic depth with engineering pragmatism by combining cloud-first language inference, local fallbacks, deterministic endpoint contracts, and layered testing from unit level to live HTTP hardware-in-the-loop (HIL) checks.

## 2. Problem Statement and Motivation

### 2.1 Problem

Users in campus-like environments often need hands-free assistance for navigation and contextual information retrieval. Traditional phone-first apps require visual attention and manual interaction, which is inconvenient while walking or carrying equipment.

### 2.2 Motivation

This project explores whether a wearable-centered system can deliver:

1. Low-friction voice interaction.
2. Navigation assistance integrated with AR clients.
3. Device interoperability (Unity, browser, ESP32, mobile bridges).
4. A practical architecture that is testable and extensible in a student project timeline.

### 2.3 Project Vision

Create a modular assistive platform where clients remain thin and the backend carries intelligence, orchestration, and integration logic.

## 3. Objectives and Scope

### 3.1 Core Objectives

1. Build a single runtime gateway that serves all client types.
2. Support multimodal input processing (text, audio, image).
3. Provide navigation intent routing and stepwise session tracking.
4. Integrate ESP32-friendly processing and TTS file fetch flow.
5. Establish repeatable full-stack validation (Python + firmware + Unity + live HIL).

### 3.2 In-Scope

1. FastAPI gateway and request orchestration.
2. LLM adapter and bounded response formatting.
3. Unity command routing and destination normalization.
4. ESP32 text loop compatibility with optional audio URL fetch.
5. Automated and live smoke testing scripts.

### 3.3 Out-of-Scope (Current Phase)

1. Multi-tenant production orchestration at scale.
2. Persistent distributed session state.
3. Full privacy-preserving on-device LLM stack.
4. Certified medical/safety compliance.

## 4. System Overview

### 4.1 Repository and Runtime Entry

Primary launcher: [start.py](../../start.py)

Key runtime modules:

1. Gateway API: [app/api/gateway.py](../../app/api/gateway.py)
2. Core assistant orchestration: [app/services/assistant_service.py](../../app/services/assistant_service.py)
3. Navigation sessions: [app/services/navigation_service.py](../../app/services/navigation_service.py)
4. QR activity service: [app/services/qr_service.py](../../app/services/qr_service.py)
5. Configuration system: [app/config/settings.py](../../app/config/settings.py)

### 4.2 High-Level Architecture

```text
Clients (Unity / Streamlit / ESP32 / Mobile)
            |
            v
      FastAPI Gateway
  (routing + orchestration)
            |
            +--> AssistantService (intent, wakeword gating, prompt shaping)
            |
            +--> NavigationService (sessions, steps, destination normalization)
            |
            +--> QRService (visibility + telemetry)
            |
            +--> AudioService / TTS utility paths
            |
            +--> LLM adapter (cloud-first, fallback path)
```

### 4.3 Startup Profiles

From [start.py](../../start.py):

1. `production-local`: gateway + streamlit + audio sidecar + MCP server.
2. `gateway-only`: gateway process only.
3. Custom flag-driven mode using configuration defaults and command arguments.

## 5. Subsystem Documentation

### 5.1 API Gateway

File: [app/api/gateway.py](../../app/api/gateway.py)

Responsibilities:

1. Expose health, debug, and network diagnostics endpoints.
2. Route `/process` multimodal requests to assistant pipeline.
3. Serve Unity voice-command and navigation endpoints.
4. Serve ESP endpoints for text processing and WAV retrieval.
5. Manage QR visibility and telemetry endpoints.
6. Apply optional Unity API key guard on selected routes.

Notable implementation details:

1. Runtime warmup on startup to reduce first-response latency.
2. Optional wakeword auto-start behavior.
3. Temporary WAV generation and auto-delete for ESP TTS fetch.
4. Migration compatibility in `/esp/process` by returning both `text` and `response` keys.

### 5.2 Assistant Service

File: [app/services/assistant_service.py](../../app/services/assistant_service.py)

Responsibilities:

1. Process text/audio/image requests.
2. Perform wakeword-aware gating for always-listen mode.
3. Trigger vision tools when image input or vision intent is detected.
4. Route Unity commands by intent category (`navigate`, `cancel_navigation`, `time_date`, `general_query`).
5. Compose final answers through LLM adapter with controlled post-processing.

Reasoning safeguards:

1. Response post-processing removes planning-like preambles.
2. Sentence count cap based on configuration (`MAX_ANSWER_SENTENCES`).
3. Runtime date/time context is injected for real-time queries.

### 5.3 Navigation Service

File: [app/services/navigation_service.py](../../app/services/navigation_service.py)

Responsibilities:

1. Normalize destination names from aliases and free text.
2. Load optional metadata from [navigation.json](../../navigation.json).
3. Create session IDs and stepwise instructions.
4. Support start, next-step, status, and cancel flows.

Current design:

1. In-memory session store.
2. Deterministic synthetic step plan with optional floor/coordinate details.
3. Suitable for single-instance runtime; not horizontally distributed yet.

### 5.4 QR Service

File: [app/services/qr_service.py](../../app/services/qr_service.py)

Responsibilities:

1. Track active visible QR markers.
2. Store append-only telemetry records with timestamps.
3. Expose active marker snapshots and telemetry counts.

### 5.5 LLM Adapter Layer

Files:

1. [app/agent/llm.py](../../app/agent/llm.py)
2. [app/agent/api_llm.py](../../app/agent/api_llm.py)

Current strategy:

1. Cloud-first model provider path (`cerebras`) through chat-completions API.
2. Fallback path to local decision loop wrapper when cloud mode is not selected.
3. Prompt style controls direct, concise response behavior.

### 5.6 Unity Navigation Client Integration

Key files:

1. [AR-campus-nav/Assets/Scripts/Navigation/ApiEndpointResolver.cs](../../AR-campus-nav/Assets/Scripts/Navigation/ApiEndpointResolver.cs)
2. [AR-campus-nav/Assets/Scripts/Navigation/VoiceNavigationController.cs](../../AR-campus-nav/Assets/Scripts/Navigation/VoiceNavigationController.cs)
3. [AR-campus-nav/Assets/Scripts/Navigation/NavigationManager.cs](../../AR-campus-nav/Assets/Scripts/Navigation/NavigationManager.cs)

Capabilities:

1. Runtime API URL resolution order:
   - PlayerPrefs override
   - environment variable fallback
   - serialized default URL
2. Optional Unity API key override and forwarding.
3. Speech command routing to server endpoint `/unity/voice-command`.
4. Server-assisted destination resolution with local NavMesh movement execution.

### 5.7 ESP32 Firmware Integration

Key file:

1. [Firmware/esp32_test_wifi/esp32_test_wifi.ino](../../Firmware/esp32_test_wifi/esp32_test_wifi.ino)

Supporting hardware docs:

1. [Firmware/HARDWARE_WIRING.md](../../Firmware/HARDWARE_WIRING.md)
2. [Firmware/deprecated/smart_glasses_esp32/COMPONENTS_GUIDE.md](../../Firmware/deprecated/smart_glasses_esp32/COMPONENTS_GUIDE.md)

Current runtime compatibility behavior:

1. Firmware parses `response` first, then falls back to `text`.
2. Relative `tts_url` values are normalized to absolute server URLs before fetch.
3. ESP can request backend processing via `/esp/process` and fetch audio via `/esp/tts/{filename}`.

## 6. API Contracts and Request Models

Request/response model definitions:

1. [app/models/requests.py](../../app/models/requests.py)
2. [app/models/responses.py](../../app/models/responses.py)

Representative endpoint groups:

1. Core: `/`, `/process`, `/run`, `/debug`, `/network/info`.
2. Audio control: `/audio/devices`, `/audio/select`, `/control/start`, `/control/stop`, `/record`.
3. Unity navigation: `/unity/voice-command`, `/navigation/start`, `/navigation/next`, `/navigation/status`, `/navigation/cancel`, `/navigate`.
4. ESP: `/esp/process`, `/esp/tts/{filename}`.
5. QR: `/qr/visible`, `/qr/hidden`, `/qr/active`, `/qr/telemetry`.

## 7. Data and State

### 7.1 Persistent Artifacts

1. Configuration file: [local.settings.json](../../local.settings.json).
2. Navigation metadata: [navigation.json](../../navigation.json).
3. Test reports: [artifacts/test_report.json](../../artifacts/test_report.json), [artifacts/live_hil_report.json](../../artifacts/live_hil_report.json).

### 7.2 In-Memory Runtime State

1. Navigation sessions (session ID keyed map).
2. QR active marker map and telemetry list.
3. Assistant wake-context cache by client key.
4. Gateway runtime warmup status flags.

### 7.3 Data Design Notes

1. Current architecture favors simplicity and fast iteration over distributed state durability.
2. Planned production hardening includes external session storage and unified telemetry schema.

## 8. Testing and Validation Strategy

### 8.1 Unified Automated Test Runner

File: [scripts/run_all_tests.py](../../scripts/run_all_tests.py)

Phases:

1. Python unit tests (`pytest -m not integration`).
2. System integration smoke test (`pytest -m integration`).
3. Firmware native tests via PlatformIO.
4. Unity EditMode tests through batchmode execution.

### 8.2 Live HIL Checker

File: [scripts/run_live_hil_check.py](../../scripts/run_live_hil_check.py)

Checks performed against running gateway:

1. Health and network diagnostics.
2. Debug endpoint.
3. Unity voice command routing.
4. Navigation start/status/next/cancel lifecycle.
5. QR visibility and telemetry lifecycle.
6. ESP process path and TTS file retrieval.

### 8.3 Current Validation Evidence

From latest artifacts:

1. Full stack test runner status is `ok: true` in [artifacts/test_report.json](../../artifacts/test_report.json).
2. Live HIL checker status is `ok: true` in [artifacts/live_hil_report.json](../../artifacts/live_hil_report.json).

## 9. Operations and Deployment

### 9.1 Local Run Modes

1. Unified profile:
   - `uv run python start.py --profile production-local`
2. Gateway only:
   - `uv run python start.py --profile gateway-only`

### 9.2 Live HIL Validation Procedure

1. Start gateway (local host or LAN host).
2. Execute:
   - `python scripts/run_live_hil_check.py --base-url http://127.0.0.1:8000`
3. Inspect generated report in [artifacts/live_hil_report.json](../../artifacts/live_hil_report.json).

### 9.3 Multi-Device Networking

Operational references:

1. [docs/10_operations/multi_device_connectivity.md](../10_operations/multi_device_connectivity.md)
2. [scripts/print_network_info.py](../../scripts/print_network_info.py)

## 10. Security and Privacy Considerations

### 10.1 Existing Controls

1. Unity endpoint key support (`X-Unity-Api-Key`) for selected routes.
2. Environment and local settings based runtime configuration.
3. Typed request validation through Pydantic models.

### 10.2 Identified Risks

1. Secrets may be accidentally committed in local settings during fast iteration.
2. Most endpoints are open in local-first mode unless explicit key protection is configured.
3. In-memory state is vulnerable to process restart loss.

### 10.3 Recommended Hardening

1. Move all secrets to environment or secret manager and rotate leaked values.
2. Add auth and rate limiting for external exposure.
3. Restrict CORS origins for non-local deployment.
4. Introduce centralized audit and request tracing logs.

## 11. Engineering Decisions and Tradeoffs

A formal decision matrix is documented in [design_decisions_and_tradeoffs.md](design_decisions_and_tradeoffs.md). Major themes:

1. Single gateway over fragmented microservices for project velocity.
2. Cloud-first inference with fallback to preserve availability.
3. Compatibility-first API contract during firmware migration.
4. Mixed client architecture while maintaining contract-first backend APIs.

## 12. Known Limitations

1. Limited persistent state and multi-instance scalability.
2. Navigation route planning remains simplified in current service logic.
3. Wakeword and STT performance depend on environment noise and microphone quality.
4. Some repository areas still contain legacy artifacts pending cleanup.

## 13. Measured Outcomes and Project Achievements

1. Unified backend contract serving web, Unity, and ESP-oriented flows.
2. End-to-end validated command pathways including live HTTP smoke checks.
3. Automated full-stack runner covering Python, firmware native, and Unity EditMode tests.
4. Working compatibility bridge for ESP response parsing and TTS URL normalization.

## 14. Graduation Demo Storyline (Recommended)

### 14.1 Problem to Solution Arc

1. Introduce real-world challenge: hands-free campus navigation and assistance.
2. Present architecture with multimodal inputs and cross-device execution.
3. Demonstrate live command routing and navigation lifecycle.
4. Demonstrate ESP interaction and audio fetch contract.
5. Show test evidence artifacts to prove reliability.

### 14.2 Suggested Live Demo Sequence

1. Health and debug checks.
2. Unity voice command intent routing.
3. Navigation start and next-step progression.
4. ESP process and TTS fetch verification.
5. Conclude with roadmap and decision rationale.

## 15. Conclusion

Smart Glasses Distilled demonstrates a practical wearable-assistant platform built with modular architecture, explicit API contracts, and layered validation. The project is intentionally designed to be both demonstrable today and extensible for future research or productization.

For continuation planning, see [future_roadmap_and_research.md](future_roadmap_and_research.md).
