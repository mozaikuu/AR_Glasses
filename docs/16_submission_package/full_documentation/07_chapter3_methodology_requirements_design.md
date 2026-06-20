# Chapter 3 — METHODOLOGY

## 3.1 Requirement Analysis

Functional requirements are traced to **FastAPI routes** in `app/api/gateway.py` and to **service classes** in `app/services/`.
Non-functional requirements (configurability, CORS, testability) are traced to `app/config/settings.py` and `tests/`.

### 3.1.1 Stakeholder view

Primary users are **students and visitors** navigating indoor spaces. Secondary stakeholders are **developers** maintaining clients
and **operators** running the gateway on a lab machine. The system prioritizes **developer velocity** (typed models in `app/models/`,
pytest) over premature distribution.

### 3.1.2 Conflicts and priorities

When latency conflicts with rich LLM answers, `MAX_ANSWER_SENTENCES` caps verbosity. When privacy conflicts with cloud STT,
the deployment must be configured with appropriate keys and retention policies—code exposes hooks but does not replace institutional policy.

### 3.1.3 Requirements elicitation and iteration log

Requirements emerged from faculty briefings, advisor checkpoints, and integration pain discovered while wiring Expo to LAN IPs. Non-functional requirements (latency, wake-word annoyance) appeared only after live walkthroughs.

Each iteration should be recoverable in Git tags or short notes in the team log—not only in chat histories.

Requirements trace to pytest cases where possible to prevent silent regressions during “quick fixes.”
