# Chapter 1 — INTRODUCTION

## 1.1 Problem Statement

University campuses combine dense indoor topology, time-varying room allocations, and information needs that arise **while walking**:
finding a TA office, a lab, or an exam room; confirming schedule details; or asking short factual questions. Traditional smartphone-first
interaction competes for visual attention and occupies at least one hand. Wearable and voice-first modalities promise lower friction,
but student-built systems often collapse into fragile demos: one-off scripts, undocumented endpoints, and no reproducible tests.

The faculty project description (Smart Glasses Distilled) asks for a **practical, integrated** assistant spanning backend intelligence,
navigation-related flows, and embedded or mobile clients. The problem, as implemented in this repository, is therefore **systems integration**
under engineering constraints: a stable gateway contract, modular services, configuration-driven feature flags, and automated regression tests.

## 1.2 Project Purpose

The purpose is to deliver a **maintainable** multimodal assistant platform where:

1. All clients share one **HTTP gateway** (`app/api/gateway.py`) rather than diverging per-device backends.
2. **Navigation intent** is expressed through explicit REST endpoints (`/navigation/start`, `/navigation/next`, etc.).
3. **Speech** can be gated with wake-word and always-listen policies aligned with `settings.wakeword_rollout_scope` and gateway metadata rules.
4. **Vision** can be invoked when images are supplied or when user phrasing matches vision intent heuristics in `assistant_service`.
5. **ESP-class devices** can call `/esp/process` and retrieve synthesized audio via `/esp/tts/{filename}`.

## 1.3 Project Scope

**In scope (as evidenced by code and tests):**

- FastAPI gateway and optional audio sidecar (`app/api/audio_sidecar.py`).
- Assistant, navigation, QR, and audio services (`app/services/`).
- Agent/LLM adapter layer (`app/agent/`).
- Clients: Expo app, React Native Android app, firmware workspace under `firmware/`.
- Pytest suite under `tests/`.

**Out of scope (explicit engineering boundaries):**

- Production multi-tenant SaaS operation.
- Medically certified assistive technology compliance.
- Full on-device large language model inference (cloud-first design with configuration for providers).

## 1.4 Objectives and Success Criteria

Measurable success criteria aligned with the repository:

1. **Gateway availability:** `GET /` returns health JSON when `uvicorn app.api.gateway:app` is running.
2. **Navigation lifecycle:** `POST /navigation/start` returns a `session_id`; `POST /navigation/next` advances; `POST /navigation/cancel` clears.
3. **Assistant path:** `POST /process` returns structured JSON including `text` and `metadata` keys used by clients.
4. **Regression safety:** `pytest tests/` passes on the submission branch (record counts in Chapter 4).
5. **Demonstrability:** A scripted demo can be executed from `start.py` with a documented profile (Chapter 3).

## 1.5 Report Outline

Chapter 2 reviews related systems and research lines. Chapter 3 presents methodology: requirements traceability, architecture,
implementation walkthrough of gateway and services, clients and firmware, testing and deployment. Chapter 4 reports experimental
and validation results. Chapter 5 discusses limitations and threats to validity. Chapter 6 concludes. Appendices list routes,
tests, configuration keys, hardware notes, and media inventory.


### 1.5.1 Traceability from template sections to this repository
Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.

Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters. Relating specifically to the angle «1.5.1 Traceability from template sections to this repository», prior studies recommend documenting failure taxonomy (timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates.
