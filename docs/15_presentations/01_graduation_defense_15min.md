# Graduation Defense Deck (15 Minutes)

Target duration: 15 minutes + Q&A
Audience: graduation committee

## Slide 1 - Title (0:30)

- Smart Glasses Distilled: A Multimodal Wearable Assistant
- Student, supervisor, department, date

Speaker note:

Introduce the core value in one sentence: hands-free guidance and interaction across wearable and companion devices.

## Slide 2 - Problem and Motivation (1:00)

- Users need hands-free support while moving indoors.
- Existing phone-first interaction is disruptive.
- Wearables require reliable multimodal orchestration, not isolated features.

Speaker note:

Frame this as an assistive systems engineering problem, not just an app feature problem.

## Slide 3 - Objectives and Scope (1:00)

- Unified backend for text, audio, vision-assisted prompting.
- Unity navigation intent and session flow.
- ESP endpoint compatibility and TTS fetch path.
- Full-stack validation strategy.

Speaker note:

State what was intentionally out of scope (production-scale multi-tenant deployment).

## Slide 4 - System Architecture (1:30)

Visual:

- Use diagram from [../14_graduation/architecture_and_dataflow_diagrams.md](../14_graduation/architecture_and_dataflow_diagrams.md)

Key points:

- One gateway, modular services.
- Contract-based clients (Unity, Streamlit, ESP).
- Cloud-first LLM with fallback behavior.

## Slide 5 - Core Backend Design (1:20)

- Gateway endpoint groups and routing model.
- Assistant service responsibilities.
- Navigation and QR state management.

Speaker note:

Emphasize why modular services inside one runtime improved speed and maintainability.

## Slide 6 - Unity and Navigation Flow (1:10)

- Voice command -> intent -> navigation session.
- Runtime API endpoint resolver for local/LAN/public scenarios.
- Local NavMesh execution with server-assisted intent.

## Slide 7 - ESP and Embedded Contract (1:10)

- `/esp/process` returns both `text` and `response` for compatibility.
- Firmware accepts fallback parse and normalizes relative `tts_url`.
- `/esp/tts/{filename}` fetch flow.

## Slide 8 - Testing Methodology (1:20)

- Unit tests + integration smoke.
- Firmware native tests.
- Unity EditMode tests.
- Live HIL HTTP smoke checks.

Visual:

- Pipeline diagram from [../14_graduation/architecture_and_dataflow_diagrams.md](../14_graduation/architecture_and_dataflow_diagrams.md)

## Slide 9 - Evaluation Results (1:10)

- Full stack runner status: pass.
- Live HIL checker status: pass.
- Artifacts:
   - [../../artifacts/test_report.json](../../artifacts/test_report.json)
   - [../../artifacts/live_hil_report.json](../../artifacts/live_hil_report.json)

## Slide 10 - Key Decisions and Tradeoffs (1:20)

- Single gateway vs split services.
- Cloud-first inference vs local-only.
- Compatibility alias during migration.
- In-memory sessions accepted as temporary debt.

Reference:

- [../14_graduation/design_decisions_and_tradeoffs.md](../14_graduation/design_decisions_and_tradeoffs.md)

## Slide 11 - Limitations and Risk Controls (1:00)

- In-memory state durability limits.
- Security hardening still in progress.
- Network variability in multi-device setups.
- Mitigation plan and staged hardening.

## Slide 12 - Future Roadmap (1:00)

- 0-3 months: reliability and security baseline.
- 3-6 months: navigation intelligence and voice robustness.
- 6-12 months: observability and productization.

Reference:

- [../14_graduation/future_roadmap_and_research.md](../14_graduation/future_roadmap_and_research.md)

## Slide 13 - Live Demo Plan (1:00)

1. Health and debug endpoints.
2. Unity voice command and navigation lifecycle.
3. ESP processing and TTS fetch.
4. Show generated artifacts.

## Slide 14 - Conclusion (0:40)

- Delivered a validated multimodal wearable assistant architecture.
- Demonstrated cross-device contract stability.
- Established a credible path from prototype to robust continuation.

## Slide 15 - Q&A (Remaining time)

- Keep backup slides ready from technical deep-dive deck.
