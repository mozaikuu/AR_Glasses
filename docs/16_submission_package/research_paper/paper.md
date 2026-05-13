% Smart Glasses Distilled — Research summary
% Ahmed Mohamed Moussa; Sandy Samy Samir; Basma Ahmed Elmorsy
% 2026-05-09

# Abstract

Wearable and companion devices need **low-friction**, **hands-free** assistance in indoor environments. This paper presents **Smart Glasses Distilled**, implemented as a Python **FastAPI** gateway (`app/api/gateway.py`) coordinating assistant, navigation, QR, and audio services, with heterogeneous clients under `clients/` (Expo, mobile, and additional integration trees) and firmware under `firmware/`. We summarize the **contract-first** HTTP surface (see `docs/16_submission_package/SOURCE_ALIGNMENT.md`), multimodal **assistant** behavior including wake-word gating and optional vision fallbacks (`app/services/assistant_service.py`), and **navigation** sessions (`app/services/navigation_service.py`). Validation is grounded in a **pytest** suite under `tests/`. We discuss limitations—single-instance session design, provider coupling—and future work toward durable state and formal user studies. Extended literature review and methodology appear in the graduation report (`full_documentation/`). Engineering reference: [@distilled2026].

**Keywords:** wearable computing, multimodal assistant, indoor navigation, FastAPI, ESP32, Expo

**Authors:** Ahmed Mohamed Moussa (222101392); Sandy Samy Samir (222101524); Basma Ahmed Elmorsy (221101164). Faculty of Computer Science and Engineering, New Mansoura University.

# 1. Introduction

University campuses combine dense indoor topology and information needs that arise while walking. Phone-first interaction competes for visual attention. This **team** project implements a **unified gateway** so Expo, Android, and embedded clients share one orchestration layer instead of diverging ad-hoc scripts.

# 2. Related work (summary)

Indoor positioning spans Wi-Fi fingerprinting, BLE beacons, UWB, pedestrian dead reckoning, and visual-inertial odometry; surveys emphasize deployment fragility versus lab accuracy. Voice assistants and LLM tool-use literature motivate bounded agent loops (`MAX_AGENT_LOOPS`) and concise answers (`MAX_ANSWER_SENTENCES`). Wearable HCI work motivates transparent failure recovery. **Full survey (50+ pages equivalent)** is consolidated in Chapter 2 of the companion graduation report generated from `build/generate_expanded_docs.py`.

# 3. System and methods

## 3.1 Runtime and process model

`start.py` launches `uvicorn app.api.gateway:app` with optional Streamlit, Flask (`run_flask.py`), audio sidecar (`app.api.audio_sidecar:app`), and MCP (`server.server:app`) depending on `LAUNCHER_PROFILE` and CLI flags.

## 3.2 Gateway and routes

`app/api/gateway.py` exposes health, diagnostics, `/process`, navigation, Unity voice command, ESP, and QR endpoints (complete table in `SOURCE_ALIGNMENT.md` §2).

## 3.3 Assistant and agent loop

The assistant service performs STT for audio payloads, wake-word detection with rolling context and follow-up windows, vision intent routing (image base64, Moondream via MCP or local), and LLM composition via `compose_answer` with post-processing caps.

## 3.4 Navigation

Navigation loads optional `navigation.json`; sessions are UUID-keyed with templated step lists including optional floor and coordinate text from metadata.

## 3.5 Clients and firmware

Expo and `clients/mobile` are the primary mobile surfaces; `firmware/platformio.ini` defines ESP32-WROVER kit environments (`PROFILE_FULL`, `PROFILE_WIFI_ONLY`, audio/camera/minimal variants).

# 4. Evaluation

The repository ships **pytest** modules covering gateway, assistant, navigation, QR, audio, agent loop, LLM adapter, models, integration smoke, and compatibility imports. **Quantitative latency tables** should be pasted from instrumented runs (e.g. `httpx` or client timers) into the Word export before defense; the report body intentionally separates **reproducible commands** from **lab-dependent numbers**.

# 5. Discussion

Strengths: modular monolith clarity, explicit REST contracts, multi-client reuse. Limitations: in-memory sessions, cloud dependence, documentation drift risk mitigated by code-first alignment files.

# 6. Conclusion

Smart Glasses Distilled demonstrates a pragmatic architecture for multimodal wearable assistance. Future work: durable session backing store, offline degradation modes, and statistically rigorous user studies.
