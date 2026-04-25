# Smart Glasses Distilled - Chapterized Thesis Draft

This document is a thesis-style draft built from the project implementation and verification artifacts in this repository.

## Front Matter Draft

- Project title: Smart Glasses Distilled: A Multimodal Wearable Assistant for Indoor Navigation and Contextual Interaction
- Student: [Your Name]
- Department: [Department Name]
- University: [University Name]
- Supervisor: [Supervisor Name]
- Date: March 2026

## Abstract

This thesis presents Smart Glasses Distilled, a multimodal assistive system that integrates voice interaction, indoor navigation, and cross-device operation across a Python backend, Unity AR client, and ESP32 firmware. The work addresses the practical challenge of hands-free interaction in campus-like environments where users need low-friction guidance and contextual responses while moving.

The implemented architecture uses a unified API gateway for multimodal orchestration, an LLM adapter for cloud-first inference with local fallback behavior, and contract-based integrations for Unity and ESP clients. To improve reliability, the project introduces layered validation: automated unit and integration testing, firmware native tests, Unity EditMode tests, and a live hardware-in-the-loop style HTTP smoke checker.

Results demonstrate successful end-to-end operation for key pathways including voice-command routing, navigation session lifecycle, QR telemetry, and ESP processing with TTS file retrieval. The thesis concludes with tradeoffs, limitations, and a roadmap toward production hardening and research extensions.

## Chapter 1 - Introduction

### 1.1 Background

Wearable assistants promise natural interaction but often struggle with practical integration across speech, navigation, and embedded hardware. Most prototypes focus on one modality or one device class, resulting in fragmented user experience.

### 1.2 Problem Statement

How can a student-built system provide reliable, hands-free, multimodal assistance for indoor environments while remaining technically testable, extensible, and demo-ready?

### 1.3 Research Questions

1. Can a single gateway architecture serve multiple client types without severe contract drift?
2. Can multimodal orchestration remain robust under real-world development constraints?
3. What test strategy provides credible evidence of full-system behavior beyond unit tests?

### 1.4 Objectives

1. Build a unified backend runtime for text, audio, and device command paths.
2. Integrate Unity navigation and ESP processing with stable API contracts.
3. Establish verification pipeline from module tests to live integrated checks.
4. Document decisions, tradeoffs, and future evolution plan.

### 1.5 Contributions

1. A practical architecture for multimodal wearable assistant development.
2. A compatibility migration strategy for ESP payload contracts.
3. A repeatable validation approach combining automated and live checks.
4. A full engineering documentation package suitable for graduation review.

### 1.6 Thesis Structure

- Chapter 1: Introduction
- Chapter 2: Related Context and System Requirements
- Chapter 3: System Design and Architecture
- Chapter 4: Implementation Details
- Chapter 5: Evaluation and Results
- Chapter 6: Discussion, Limitations, and Risks
- Chapter 7: Future Work and Roadmap
- Chapter 8: Conclusion

## Chapter 2 - Related Context and Requirements

### 2.1 Context

This project sits at the intersection of:

1. Multimodal conversational systems.
2. Indoor navigation support systems.
3. Embedded-to-cloud integration patterns.

### 2.2 Functional Requirements

1. Accept text and audio requests.
2. Route Unity voice commands into actionable intents.
3. Start and track navigation sessions.
4. Process ESP prompts and provide optional audio retrieval links.
5. Expose diagnostics for health and network state.

### 2.3 Non-Functional Requirements

1. Fast local startup and repeatable environment configuration.
2. High demonstrability for academic defense.
3. Clear API contracts across clients.
4. Basic security hooks for endpoint protection.

### 2.4 Constraints

1. Student timeline and resource limits.
2. Mixed maturity of client components.
3. Dependence on external inference providers in cloud-first mode.
4. Hardware variability and network instability in live scenarios.

## Chapter 3 - System Design and Architecture

### 3.1 Architectural Style

The project uses a gateway-centered modular monolith style:

1. One canonical launcher.
2. One API gateway as orchestrator.
3. Service-layer modules for assistant logic, navigation, and QR state.
4. Client-specific behavior at API boundaries rather than direct coupling.

### 3.2 Core Runtime Components

1. Launcher: [../../start.py](../../start.py)
2. Gateway: [../../app/api/gateway.py](../../app/api/gateway.py)
3. Assistant service: [../../app/services/assistant_service.py](../../app/services/assistant_service.py)
4. Navigation service: [../../app/services/navigation_service.py](../../app/services/navigation_service.py)
5. QR service: [../../app/services/qr_service.py](../../app/services/qr_service.py)
6. LLM adapters: [../../app/agent/llm.py](../../app/agent/llm.py), [../../app/agent/api_llm.py](../../app/agent/api_llm.py)

### 3.3 Data and Control Flow Summary

1. Client request enters gateway.
2. Gateway validates and routes payload.
3. Assistant service handles modality-specific logic and response composition.
4. Optional navigation/QR/ESP paths execute as needed.
5. Response and metadata are returned to client.

### 3.4 Key Design Decisions

1. Single gateway over split microservices.
2. Cloud-first LLM with fallback behavior.
3. Compatibility-first API contract for ESP migration.
4. In-memory sessions for current phase with explicit future upgrade path.

(Expanded in [design_decisions_and_tradeoffs.md](design_decisions_and_tradeoffs.md))

## Chapter 4 - Implementation

### 4.1 Backend API Layer

Implemented endpoint groups include:

1. Health and diagnostics: `/`, `/debug`, `/network/info`, `/mcp-status`.
2. Processing: `/process`, `/run`.
3. Unity routing: `/unity/voice-command`, `/navigate`.
4. Navigation lifecycle: `/navigation/start`, `/navigation/next`, `/navigation/status`, `/navigation/cancel`.
5. ESP integration: `/esp/process`, `/esp/tts/{filename}`.
6. QR telemetry: `/qr/visible`, `/qr/hidden`, `/qr/active`, `/qr/telemetry`.

### 4.2 Assistant Logic

The assistant service implements:

1. Wakeword-aware audio gating for always-listen behavior.
2. Audio transcription flow and fallback responses.
3. Vision intent handling for image or camera-triggered prompts.
4. Unity command intent routing with normalized action payloads.
5. Post-processed LLM responses with sentence constraints.

### 4.3 Navigation Module

Current navigation implementation focuses on deterministic, session-based step progression:

1. Destination normalization via aliases and metadata.
2. Session ID generation and state progression.
3. Status and cancellation support.

### 4.4 Unity Client Integration

Unity scripts support:

1. Runtime base URL and API key resolution.
2. Voice command capture and backend routing.
3. Local NavMesh movement after destination resolution.

### 4.5 ESP Integration

ESP pathway includes:

1. POST processing endpoint for assistant response generation.
2. WAV retrieval endpoint for TTS playback fetch.
3. Compatibility behavior where both `text` and `response` are accepted/returned.
4. Relative TTS URL normalization in firmware.

## Chapter 5 - Evaluation and Results

### 5.1 Evaluation Methodology

A layered strategy was used:

1. Unit testing of core Python modules.
2. Integration smoke testing for cross-component API flow.
3. Firmware native testing through PlatformIO.
4. Unity EditMode testing.
5. Live HIL-style endpoint sweep against a running gateway.

### 5.2 Test Tooling

1. Unified runner: [../../scripts/run_all_tests.py](../../scripts/run_all_tests.py)
2. Live checker: [../../scripts/run_live_hil_check.py](../../scripts/run_live_hil_check.py)

### 5.3 Current Result Snapshot (March 2026)

Based on generated artifacts:

1. Full stack report indicates overall pass status in [../../artifacts/test_report.json](../../artifacts/test_report.json).
2. Live HIL report indicates all configured checks passed in [../../artifacts/live_hil_report.json](../../artifacts/live_hil_report.json).

### 5.4 Interpretation

The results support the core claim that the architecture can run end-to-end and maintain contract consistency across major paths.

## Chapter 6 - Discussion, Limitations, and Risks

### 6.1 What Worked Well

1. Unified gateway reduced integration friction.
2. Modular services improved readability and testability.
3. Compatibility-first migration avoided firmware breakage.
4. Live checker provided concrete confidence before demos.

### 6.2 Limitations

1. In-memory state is not durable or distributed.
2. Navigation logic remains simplified.
3. Cloud dependency may affect latency or availability.
4. Security posture is baseline, not production-grade.

### 6.3 Risk Register

1. API key management risk.
2. Client contract drift risk.
3. Network reliability risk in multi-device deployments.
4. Scope expansion risk in academic timeline.

### 6.4 Mitigations

1. Contract tests and compatibility aliases.
2. Validation gates before demo/release.
3. Documentation-first onboarding and operations runbooks.
4. Explicit roadmap with staged hardening priorities.

## Chapter 7 - Future Work

### 7.1 Near-Term

1. Persistent session store for navigation and telemetry.
2. Stronger authentication and rate limiting.
3. CI integration for routine automated checks.

### 7.2 Mid-Term

1. Graph-based route planning enhancements.
2. Better wakeword and STT robustness in noisy environments.
3. Improved firmware playback and network resilience.

### 7.3 Long-Term

1. Service decomposition if load and complexity justify it.
2. Rich observability with tracing and dashboards.
3. Publication-focused experiments on multimodal reasoning quality.

(Expanded roadmap in [future_roadmap_and_research.md](future_roadmap_and_research.md))

## Chapter 8 - Conclusion

Smart Glasses Distilled demonstrates that a student project can deliver a credible multimodal wearable assistant by combining disciplined architecture, compatibility-aware integration, and layered verification. The system is operational today and structured for meaningful extension beyond graduation.

## Appendices

### Appendix A - Reproducibility Commands

```powershell
uv run python start.py --profile production-local
python scripts/run_all_tests.py
python scripts/run_live_hil_check.py --base-url http://127.0.0.1:8000
```

### Appendix B - Key Artifacts

1. [../../artifacts/test_report.json](../../artifacts/test_report.json)
2. [../../artifacts/live_hil_report.json](../../artifacts/live_hil_report.json)
3. [full_project_documentation.md](full_project_documentation.md)
4. [architecture_and_dataflow_diagrams.md](architecture_and_dataflow_diagrams.md)

### Appendix C - Suggested Defense Attachments

1. Architecture diagrams.
2. API contract table.
3. Test reports screenshots.
4. Live demo checklist and fallback plan.
