# Q&A Bank for Graduation Presentation

## Architecture Questions

### Q1: Why did you choose a single gateway instead of microservices?

Answer guidance:

- The project prioritizes integration speed, contract consistency, and demo reliability.
- A unified gateway reduced orchestration overhead under student constraints.
- Service boundaries are modular, so decomposition remains possible later.

### Q2: How do you avoid tight coupling with multiple clients?

Answer guidance:

- Contract-first API design.
- Runtime resolver patterns in Unity.
- Compatibility strategy on ESP path during migration.

## AI and Inference Questions

### Q3: What happens if cloud inference fails?

Answer guidance:

- Cloud-first path is used when configured.
- Fallback path exists in adapter logic.
- System behavior degrades gracefully with explicit error metadata.

### Q4: How do you control response quality?

Answer guidance:

- Prompt style constraints.
- Post-processing to remove planning narration.
- Sentence cap to maintain concise assistive responses.

## Testing and Evaluation Questions

### Q5: Why is your test strategy credible?

Answer guidance:

- It spans unit, integration, firmware native, Unity edit tests, and live endpoint sweeps.
- Evidence is artifact-based and reproducible.

### Q6: Did you validate full-system communication?

Answer guidance:

- Yes, via unified runner and live HIL checker.
- Mention artifact files and key checks that passed.

## Navigation Questions

### Q7: Is navigation fully production-grade?

Answer guidance:

- Current implementation is functional and deterministic.
- It is intentionally simplified for reliability and explainability.
- Roadmap includes richer graph planning and rerouting.

## Hardware Questions

### Q8: How robust is ESP integration?

Answer guidance:

- Endpoints and firmware parser are compatibility-hardened.
- Relative TTS URL normalization solved an integration failure class.
- Further work includes stronger retry and offline behavior.

## Security Questions

### Q9: What are your biggest security gaps today?

Answer guidance:

- Local-first defaults, secret hygiene risk, and limited endpoint auth.
- Mitigation plan includes secret rotation, auth, rate limiting, and CORS tightening.

## Productization Questions

### Q10: What would you do first after graduation?

Answer guidance:

- Reliability baseline: persistent state, tracing, and CI gates.
- Then navigation intelligence and multi-device hardening.

## Delivery Tips

1. Keep each answer under 30 seconds unless asked to expand.
2. Anchor claims to artifacts and specific files.
3. Distinguish between what is done, what is validated, and what is future work.
