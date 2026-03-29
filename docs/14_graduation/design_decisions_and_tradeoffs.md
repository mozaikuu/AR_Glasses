# Design Decisions and Tradeoffs

This document records major architecture and implementation decisions made during the Smart Glasses Distilled project.

## 1. Decision Log Summary

| ID  | Decision                                                           | Status             |
| --- | ------------------------------------------------------------------ | ------------------ |
| D1  | Use single FastAPI gateway as primary orchestration boundary       | Accepted           |
| D2  | Keep one launcher (`start.py`) with profile-driven startup         | Accepted           |
| D3  | Use cloud-first LLM provider with local fallback path              | Accepted           |
| D4  | Keep Unity as AR navigation client while backend resolves intent   | Accepted           |
| D5  | Preserve ESP compatibility by returning both `text` and `response` | Accepted           |
| D6  | Use in-memory navigation sessions for current phase                | Accepted with debt |
| D7  | Add unified full-stack runner and live HIL checker                 | Accepted           |
| D8  | Use runtime URL/key override model in Unity endpoint resolver      | Accepted           |

## 2. Detailed Decisions

### D1 - Single FastAPI Gateway

Problem:

The project includes multiple client channels (Unity, Streamlit, ESP) that require shared logic and consistent contracts.

Options considered:

1. Separate service per client.
2. Unified gateway with modular services behind it.

Chosen:

Unified gateway in [app/api/gateway.py](../../app/api/gateway.py).

Why:

1. Faster development and debugging for student timeline.
2. Easier contract consistency across clients.
3. Lower orchestration complexity for local and demo deployments.

Tradeoff:

1. Higher coupling in one runtime process.
2. Requires future decomposition for horizontal scale.

### D2 - Single Launcher with Profiles

Problem:

Multiple startup scripts created confusion and inconsistent runtime behavior.

Options considered:

1. Keep separate launchers for each component.
2. Single launcher with profile/flag controls.

Chosen:

Single launcher [start.py](../../start.py).

Why:

1. Standardized boot process.
2. Reproducible demos and testing.
3. Easier onboarding and documentation.

Tradeoff:

1. Launcher logic becomes a coordination point requiring maintenance.

### D3 - Cloud-First LLM with Fallback

Problem:

Need strong response quality while preserving resilience in case of provider issues.

Options considered:

1. Cloud-only LLM.
2. Local-only model.
3. Cloud-first with fallback path.

Chosen:

Cloud-first Cerebras path with fallback route in [app/agent/llm.py](../../app/agent/llm.py).

Why:

1. Better quality/latency tradeoff for current hardware.
2. Practical reliability fallback.

Tradeoff:

1. Dependency on external API and key management.
2. Potential variability in latency.

### D4 - Unity Handles Local NavMesh Movement

Problem:

Need responsive in-scene motion while still supporting backend intent understanding.

Options considered:

1. Server computes full motion and sends trajectories.
2. Server resolves destination intent; Unity performs local movement.

Chosen:

Hybrid model using [VoiceNavigationController.cs](../../AR-campus-nav/Assets/Scripts/Navigation/VoiceNavigationController.cs) and [NavigationManager.cs](../../AR-campus-nav/Assets/Scripts/Navigation/NavigationManager.cs).

Why:

1. Low latency local movement.
2. Keeps server logic scene-agnostic.

Tradeoff:

1. Requires destination naming consistency between backend and Unity scene.

### D5 - ESP Compatibility Alias (`text` + `response`)

Problem:

Firmware/client paths historically parsed different response keys.

Options considered:

1. Force immediate migration to one key.
2. Temporary compatibility alias to avoid breakage.

Chosen:

Return both keys in `/esp/process` and accept fallback parse in firmware.

Why:

1. Reduces regression risk during active integration.
2. Supports phased migration.

Tradeoff:

1. Slight API redundancy until migration completion.

### D6 - In-Memory Session State (Current Phase)

Problem:

Need working navigation sessions quickly with low complexity.

Options considered:

1. External database/session store.
2. In-memory dictionary in service layer.

Chosen:

In-memory map in [app/services/navigation_service.py](../../app/services/navigation_service.py).

Why:

1. Fast implementation.
2. Zero infrastructure overhead for demos.

Tradeoff:

1. State loss on restart.
2. Not suitable for multi-instance scale.

### D7 - Layered Validation: Unified Runner + Live HIL

Problem:

Unit tests alone cannot prove cross-component behavior.

Options considered:

1. Keep only unit tests.
2. Add integrated runner and live endpoint checker.

Chosen:

1. Unified runner: [scripts/run_all_tests.py](../../scripts/run_all_tests.py)
2. Live checker: [scripts/run_live_hil_check.py](../../scripts/run_live_hil_check.py)

Why:

1. Covers multiple integration boundaries.
2. Provides demonstrable engineering rigor for graduation review.

Tradeoff:

1. More environment prerequisites (Unity executable, PlatformIO).

### D8 - Runtime API URL and Key Resolution in Unity

Problem:

Hardcoded backend URLs break when moving across LAN/public/demo environments.

Options considered:

1. Hardcode endpoint in scripts.
2. Runtime override mechanism with fallback.

Chosen:

Resolver strategy in [ApiEndpointResolver.cs](../../AR-campus-nav/Assets/Scripts/Navigation/ApiEndpointResolver.cs).

Why:

1. Enables fast switching between local/LAN/public endpoints.
2. Keeps build artifacts reusable.

Tradeoff:

1. Requires disciplined environment setup and documentation.

## 3. Accepted Technical Debt

1. Some legacy docs still reference older runtime paths.
2. In-memory state persistence limitations.
3. Mixed client maturity levels (web/unity/firmware not equally productionized).
4. Audio sidecar remains minimal.

## 4. Mitigation Plan

1. Incrementally align legacy docs to canonical app/ runtime paths.
2. Introduce persistent session and telemetry storage.
3. Expand integration tests to include real hardware loops.
4. Add stricter security defaults before external deployment.

## 5. Conclusion

The chosen decisions prioritize delivery, demonstrability, and controlled complexity while preserving clear extension points for future work.
