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
Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «3.1.3 Requirements elicitation and iteration log», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.
