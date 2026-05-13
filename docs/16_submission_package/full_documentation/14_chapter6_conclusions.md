# Chapter 6 — CONCLUSIONS

Smart Glasses Distilled demonstrates that a **single FastAPI gateway** with explicit service modules can support multimodal campus assistance
across Expo, Android, and ESP-class clients while remaining testable with pytest. Navigation sessions, QR flows, and ESP TTS fetch paths are
first-class HTTP concerns rather than ad-hoc sockets.

Future work should prioritize durable session storage, richer building models feeding `navigation_service`, and expanded user studies beyond lab pilots.

## Team contribution statement

This graduation project was completed as a team effort under the Faculty of Computer Science and Engineering, New Mansoura University.
**Ahmed Mohamed Moussa (222101392)**, **Sandy Samy Samir (222101524)**, and **Basma Ahmed Elmorsy (221101164)** jointly contributed to
architecture discussions, implementation, testing, documentation, and demonstration materials. Individual file-level authorship can be
annotated in Git history and in the advisor-approved contribution form required by the faculty.

### 6.1 Closing reflections
Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «6.1 Closing reflections», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.
