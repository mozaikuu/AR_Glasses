# Product Narrative

## What This Product Is

A multimodal smart-glasses assistant that helps users navigate spaces and interact hands-free using voice, text, and vision across wearable and companion devices.

## User Experience Model

- User speaks via wearable/device channel.
- System detects wakeword and captures command.
- Assistant responds quickly with actionable answer.
- Navigation prompts are delivered as stepwise guidance.
- Feedback channels include voice output, visual cues, and device relays.

## Real-Time Constraints

- Wakeword loop must stay responsive under noisy conditions.
- STT + inference + response loop must remain low-latency enough for conversational use.
- Navigation updates must be stable and synchronized with user movement context.

## Top 15 Improvements (Prioritized)

1. Reintroduce/fix canonical `flask.py` primary interface implementation.
2. Consolidate startup scripts to one authoritative runtime path.
3. Standardize port map and publish environment-driven defaults.
4. Add end-to-end integration tests across Unity/mobile/ESP flows.
5. Add centralized telemetry and request tracing.
6. Add robust audio diagnostics endpoint and health scoring.
7. Externalize session state for multi-user scalability.
8. Harden auth for non-local API exposure.
9. Normalize destination naming between Unity and server graphs.
10. Add strict config schema validation on boot.
11. Move hardcoded mobile server URLs to runtime config.
12. Introduce feature flags for sidecar and fallback mode control.
13. Improve wakeword false-positive suppression logic.
14. Add model readiness checks and warmup paths.
15. Define release profiles (dev/demo/prod) with documented behavior.

## If Rebuilt Today

- Keep `start.py` as single launcher.
- Split gateway into clear services:
  - API gateway
  - speech service
  - navigation service
  - inference orchestration service
- Add event bus for cross-device state updates.
- Move transient globals to persisted, typed state store.
- Define contract-first APIs for Unity/mobile/ESP channels.

## Demo Narrative (Graduation-Friendly)

- Start with real problem: hands-free guidance and assistant for wearable use.
- Show live wakeword + command + response.
- Show navigation handoff: voice intent -> route -> guided steps.
- Show multi-device continuity: Unity + Android + ESP mode switch.
- Emphasize hybrid AI resilience: cloud-first with local fallback.
- Close with engineering maturity plan (security, scale, reliability roadmap).

