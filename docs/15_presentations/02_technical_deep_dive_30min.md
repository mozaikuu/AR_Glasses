# Technical Deep-Dive Deck (30 Minutes)

Target duration: 25-30 minutes + detailed Q&A
Audience: technical examiners and engineering reviewers

## Section A - Context and Requirements

### Slide 1 - Title and Scope
- Technical deep dive: architecture, implementation, validation, and roadmap.

### Slide 2 - Requirements Matrix
- Functional and non-functional requirements.
- Explicit constraints and assumptions.

### Slide 3 - Runtime Boundaries
- Canonical launcher and active runtime paths.

## Section B - Architecture

### Slide 4 - Architecture Diagram
- Present component architecture.
- Explain gateway-centered modular monolith strategy.

### Slide 5 - Service Responsibilities
- Assistant service.
- Navigation service.
- QR service.
- LLM adapter.

### Slide 6 - API Contract Taxonomy
- Endpoint grouping by function.
- Contract consistency strategy across clients.

## Section C - Implementation Detail

### Slide 7 - Assistant Pipeline
- Wakeword gating.
- Modality handling logic.
- Prompt shaping and response post-processing.

### Slide 8 - Navigation Session Model
- Destination normalization.
- Session lifecycle.
- Current state model and limitations.

### Slide 9 - Unity Integration
- Runtime URL/key resolver.
- Voice command router integration.
- Local movement with server intent resolution.

### Slide 10 - ESP Integration
- Process endpoint contract.
- Compatibility alias decision.
- TTS URL normalization logic and fetch path.

### Slide 11 - Configuration Model
- `local.settings.json` and environment precedence.
- Runtime profile behavior and tradeoffs.

## Section D - Validation and Evidence

### Slide 12 - Test Strategy
- Why layered validation was necessary.
- Unit vs integration vs live checks.

### Slide 13 - Unified Runner Walkthrough
- `scripts/run_all_tests.py` phases.
- Result interpretation.

### Slide 14 - Live HIL Checker Walkthrough
- `scripts/run_live_hil_check.py` check list.
- Endpoint lifecycle coverage.

### Slide 15 - Evidence Artifacts
- `artifacts/test_report.json`
- `artifacts/live_hil_report.json`

### Slide 16 - Failure Modes and Recovery
- Missing toolchains (PlatformIO/Unity).
- Endpoint mismatch risk.
- Network instability.

## Section E - Decisions, Tradeoffs, and Risks

### Slide 17 - Key Decisions
- Summarize D1-D8 from decision log.

### Slide 18 - Accepted Technical Debt
- In-memory sessions.
- Legacy documentation drift.
- Mixed client maturity.

### Slide 19 - Security Posture
- Existing controls.
- Gaps and hardening plan.

## Section F - Future Directions

### Slide 20 - 0-3 Month Plan
- Reliability, security, CI.

### Slide 21 - 3-6 Month Plan
- Navigation intelligence and voice quality.

### Slide 22 - 6-12 Month Plan
- Observability, deployment, and release governance.

### Slide 23 - Research Tracks
- Explainability, personalization, sensor fusion, and hallucination control.

## Section G - Closing

### Slide 24 - Technical Summary
- Architecture viability, integration quality, validation maturity.

### Slide 25 - Q&A
- Move to Q&A bank.

## Backup Slides (Optional)

1. Detailed endpoint table.
2. Navigation JSON schema excerpts.
3. Firmware command/response examples.
4. Test execution logs and summary snapshots.
