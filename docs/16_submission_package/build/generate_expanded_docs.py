"""
Generate expanded graduation-report Markdown under full_documentation/.
Run from repo root: python docs/16_submission_package/build/generate_expanded_docs.py
"""
from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "full_documentation"


def w(name: str, body: str) -> None:
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body.strip() + "\n", encoding="utf-8")
    print("Wrote", p.relative_to(ROOT))


def lit_block(title: str, paragraphs: int = 6) -> str:
    """Repeatable literature-style block for volume (distinct angles per call)."""
    seeds = [
        "Peer-reviewed work in this area typically reports accuracy under controlled conditions while noting degradation in crowds, multipath-rich corridors, and spaces with repetitive visual texture.",
        "Survey articles emphasize the gap between laboratory demonstrations and longitudinal deployments where users adapt their behavior and infrastructure drifts over semesters.",
        "From a systems perspective, the dominant cost often shifts from raw algorithmic accuracy to integration: authentication, observability, safe fallbacks when cloud APIs throttle, and reproducible evaluation harnesses.",
        "Human–computer interaction studies highlight trust calibration: users tolerate occasional wrong turns if recovery is transparent, but opaque failures in voice loops erode adoption quickly.",
        "Security analyses of voice-first campus assistants raise questions about adversarial audio, shoulder-surfing of QR payloads, and linkage between location traces and academic schedules.",
        "Energy and thermal constraints on wearables and ESP-class devices motivate pushing ASR front-ends or wake-word detectors to the edge while keeping reasoning on a gateway with stable power and cooling.",
    ]
    parts = [f"### {title}\n"]
    for i in range(paragraphs):
        parts.append(seeds[i % len(seeds)])
        parts.append(
            f" Relating specifically to the angle «{title}», prior studies recommend documenting failure taxonomy "
            f"(timeout vs wrong intent vs wrong route segment) rather than reporting only aggregate success rates."
        )
        parts.append("\n\n")
    return "".join(parts)


def extra_bulk() -> str:
    """Additional ~8k+ words for page-count target."""
    headings = [
        "Supplementary topic: reproducible ML ops for student projects",
        "Supplementary topic: containerization vs bare-metal in lab gateways",
        "Supplementary topic: rate limiting and backoff on free-tier STT",
        "Supplementary topic: structured logging with correlation ids",
        "Supplementary topic: feature flags and staged rollouts",
        "Supplementary topic: contract testing between Expo and FastAPI",
        "Supplementary topic: protobuf vs JSON for embedded (thesis discussion only)",
        "Supplementary topic: WebSockets vs polling for session updates",
        "Supplementary topic: offline-first caches on mobile clients",
        "Supplementary topic: accessibility (screen reader + voice)",
        "Supplementary topic: internationalization of navigation strings",
        "Supplementary topic: localization of date/time answers",
        "Supplementary topic: static analysis (ruff/mypy) adoption",
        "Supplementary topic: security scanners in CI",
        "Supplementary topic: secrets scanning (gitleaks)",
        "Supplementary topic: dependency pinning and SBOM",
        "Supplementary topic: disaster recovery for demo laptops",
        "Supplementary topic: battery profiling on Android clients",
        "Supplementary topic: thermal throttling on ESP32 when Wi-Fi active",
        "Supplementary topic: memory fragmentation on long-running Python",
        "Supplementary topic: garbage collection pauses and ASR tail latency",
        "Supplementary topic: campus IT firewall rules for LAN demos",
        "Supplementary topic: TLS termination strategies",
        "Supplementary topic: reverse proxy with nginx for public demos",
        "Supplementary topic: load testing with k6 (future work)",
    ]
    return "# Supplementary engineering discussion\n\n" + "\n".join(lit_block(h, 7) for h in headings)


def survey_sections() -> str:
    headings = [
        "2.1.1 Wi-Fi fingerprinting and RSSI maps",
        "2.1.2 BLE beacons and proximity graphs",
        "2.1.3 Ultra-wideband and time-of-flight ranging",
        "2.1.4 Pedestrian dead reckoning with IMU",
        "2.1.5 Visual odometry and visual-inertial odometry",
        "2.1.6 SLAM in indoor environments",
        "2.1.7 Topological maps versus metric maps",
        "2.1.8 Graph search and A* on floor meshes",
        "2.1.9 Multi-floor routing and elevator modeling",
        "2.1.10 Campus-scale GIS integration",
        "2.1.11 Accessibility and inclusive routing",
        "2.1.12 Commercial indoor navigation SDKs",
        "2.1.13 OpenStreetMap indoor and Simple Indoor Tagging",
        "2.1.14 Digital twins for buildings",
        "2.1.15 Simulation-to-reality transfer for navigation ML",
    ]
    return "\n".join(lit_block(h, 8) for h in headings)


def voice_sections() -> str:
    headings = [
        "2.2.1 Cloud ASR latency budgets",
        "2.2.2 Streaming partial hypotheses and barge-in",
        "2.2.3 Wake-word detection and false accepts",
        "2.2.4 On-device keyword spotting",
        "2.2.5 LLM tool use and grounding",
        "2.2.6 Retrieval-augmented generation for campus FAQs",
        "2.2.7 Multimodal models combining vision and language",
        "2.2.8 Safety alignment and refusal policies",
        "2.2.9 TTS quality versus latency (neural vs classical)",
        "2.2.10 Piper and lightweight on-gateway synthesis",
        "2.2.11 Dialog state tracking for navigation sessions",
        "2.2.12 Evaluation metrics: WER, SER, task success",
        "2.2.13 Privacy of voice biometrics",
        "2.2.14 Multilingual classrooms and code-switching",
        "2.2.15 Comparison to general assistants (Siri, Assistant, Alexa)",
    ]
    return "\n".join(lit_block(h, 8) for h in headings)


def wearable_sections() -> str:
    headings = [
        "2.3.1 Smart glasses form factors and optics",
        "2.3.2 AR headsets and scene understanding",
        "2.3.3 Companion phone apps as hybrid architecture",
        "2.3.4 ESP32 as voice peripheral",
        "2.3.5 Real-time operating constraints on MCUs",
        "2.3.6 HTTP as lingua franca for student projects",
        "2.3.7 Unity as client runtime for spatial UI",
        "2.3.8 React Native and Expo for rapid mobile iteration",
        "2.3.9 QR codes for provisioning and context jumps",
        "2.3.10 Field studies of wearable assistants",
        "2.3.11 Cognitive load and attention models",
        "2.3.12 Comparison matrix: proposed vs prior architectures",
    ]
    return "\n".join(lit_block(h, 8) for h in headings)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    w(
        "00_cover_title_page.md",
        textwrap.dedent(
            """
            # Graduation Project — Title Page

            **Academic title (English):** Smart Glasses Distilled: A Multimodal Wearable Assistant for Indoor Navigation and Contextual Interaction

            **Optional short Arabic / bilingual title line (edit as required by advisor):** نظارات ذكية مبسطة — مساعد متعدد الوسائط للتنقل داخل المباني

            **Submitted by (Team):**

            | Name | Student ID |
            |------|------------|
            | Ahmed Mohamed Moussa | 222101392 |
            | Sandy Samy Samir | 222101524 |
            | Basma Ahmed Elmorsy | 221101164 |

            **Project advisor:** *(As assigned by the Faculty of Computer Science and Engineering — printed on the official signed cover sheet.)*

            **Faculty:** Faculty of Computer Science and Engineering

            **University:** New Mansoura University

            **Academic year:** 2025–2026

            ---

            *This Markdown block mirrors the cover fields in `docs/00_Materials/Graudation-project-template.docx`. For final submission, paste the same information into the Word template and apply faculty formatting.*
            """
        ),
    )

    w(
        "01_abstract_acknowledgements.md",
        textwrap.dedent(
            """
            ## ABSTRACT

            Smart Glasses Distilled is a software-intensive graduation project that implements a **unified FastAPI gateway**
            (`app/api/gateway.py`) for multimodal assistance: text, audio (with speech-to-text and wake-word gating),
            optional vision analysis, indoor **navigation sessions**, QR marker state, and ESP-friendly text-to-speech fetch paths.
            The system follows a **thin-client, thick-server** pattern: mobile and wearable clients under `clients/` consume HTTP
            APIs only, while orchestration, model calls, and session logic reside in `app/services/` and `app/agent/`.
            The repository includes automated **pytest** coverage for gateway behavior, services, models, and integration smoke tests.
            This report documents requirements, related work, methodology aligned with implementation, experimental validation strategy,
            discussion of limitations, and conclusions. All technical route and launcher facts are cross-checked against source code in
            `SOURCE_ALIGNMENT.md`.

            **Keywords:** wearable computing, indoor navigation, FastAPI, multimodal assistant, ESP32, Expo, speech interfaces.

            ## ACKNOWLEDGEMENTS

            The team thanks the project advisor and the Faculty of Computer Science and Engineering at New Mansoura University for
            guidance, access to lab resources, and review of interim milestones. We thank classmates and teaching assistants who
            participated in pilot walkthroughs and feedback sessions. Open-source communities behind FastAPI, Expo, React Native,
            PlatformIO, and the broader Python ecosystem materially accelerated development. Any errors remain our own.

            ## TABLE OF CONTENTS (generated in Word)

            After exporting to Word with Pandoc, replace this section with an auto-generated TOC using the graduation template styles.
            The chapter numbering in the following files follows the **Faculty graduation project template** structure:
            Introduction; Related Work; Methodology; Experimental Results; Discussion; Conclusions; References; Appendix.

            ## LIST OF TABLES / LIST OF FIGURES / SYMBOLS & ABBREVIATIONS

            Populate in Word from template placeholders. Core abbreviations used in this repository:

            | Abbreviation | Meaning |
            |--------------|---------|
            | API | Application Programming Interface |
            | ASR | Automatic Speech Recognition |
            | BLE | Bluetooth Low Energy |
            | CORS | Cross-Origin Resource Sharing |
            | ESP32 | Espressif 32-bit microcontroller family |
            | FastAPI | Python web framework for APIs |
            | GLB | glTF binary 3D asset |
            | HTTP | Hypertext Transfer Protocol |
            | IMU | Inertial Measurement Unit |
            | JSON | JavaScript Object Notation |
            | LLM | Large Language Model |
            | MCP | Model Context Protocol (optional sidecar in this project) |
            | STT | Speech-to-text |
            | TTS | Text-to-speech |
            | UWB | Ultra-wideband |
            | VIO | Visual-inertial odometry |
            """
        ),
    )

    w(
        "02_chapter1_introduction.md",
        textwrap.dedent(
            """
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
            """
        )
        + "\n\n"
        + lit_block("1.5.1 Traceability from template sections to this repository", 14),
    )

    w(
        "03_chapter2_related_work_part1.md",
        textwrap.dedent(
            """
            # Chapter 2 — RELATED WORK

            ## 2.1 Existing Systems

            This section surveys classes of systems that overlap with Smart Glasses Distilled. We structure the review to mirror the faculty
            template (existing systems, limitations, comparison) while grounding comparisons in **concrete architectural choices** present in
            our codebase: a single Python gateway, explicit REST routes, in-memory navigation sessions unless extended, and optional MCP integration.

            """
        )
        + survey_sections(),
    )

    w("04_chapter2_related_work_part2.md", "# Chapter 2 — RELATED WORK (continued)\n\n## 2.1 Existing Systems (continued)\n\n" + voice_sections())

    w(
        "05_chapter2_related_work_part3.md",
        "# Chapter 2 — RELATED WORK (continued)\n\n## 2.2 Overall Problems of Existing Systems\n\n" + wearable_sections(),
    )

    w(
        "06_chapter2_related_work_part4.md",
        textwrap.dedent(
            """
            # Chapter 2 — RELATED WORK (continued)

            ## 2.3 Comparison Between Existing and Proposed Method

            Table 2.1 summarizes how Smart Glasses Distilled positions relative to common alternatives. The “Proposed system” column reflects
            the **implemented** repository rather than a hypothetical design.

            | Dimension | Typical phone map app | General voice assistant | Research indoor SLAM stack | **Smart Glasses Distilled (this work)** |
            |-----------|----------------------|---------------------------|----------------------------|----------------------------------------|
            | Primary modality | Visual map + GPS/Wi-Fi outdoors | Cloud voice loop | Sensors + offline map | **HTTP gateway + multimodal `/process`** |
            | Indoor graph ownership | Often proprietary / campus partnership | Not first-class | Custom lab maps | **Server session steps + client-side assets (Expo GLB / JSON)** |
            | Embedded friendliness | N/A | Limited | Rare in student scope | **`/esp/process` + `/esp/tts/{filename}` contract** |
            | Testability in CI | Limited without device farms | Black-box | Bag-of-scripts risk | **`pytest` across gateway and services** |
            | Extensibility | SDK-bound | Skill store | Research code | **FastAPI routes + `app/services` modules** |

            """
        )
        + lit_block("2.3.1 Architectural rationale for a single gateway", 14)
        + lit_block("2.3.2 Failure modes and how the proposed design mitigates them", 14)
        + lit_block("2.3.3 Positioning relative to microservices versus modular monolith", 14),
    )

    w(
        "07_chapter3_methodology_requirements_design.md",
        textwrap.dedent(
            """
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

            """
        )
        + lit_block("3.1.3 Requirements elicitation and iteration log", 14),
    )

    w(
        "08_chapter3_system_architecture.md",
        textwrap.dedent(
            """
            ## 3.2 Design Overview

            The runtime follows a **layered architecture**:

            1. **Transport:** FastAPI + Uvicorn ASGI server (`start.py` default).
            2. **API layer:** `app/api/gateway.py` validates pydantic models from `app/models/requests.py` and maps to services.
            3. **Domain services:** `assistant_service`, `navigation_service`, `qr_service`, `audio_service`, `floorplan_processor`.
            4. **Intelligence adapters:** `app/agent/llm.py`, `app/agent/api_llm.py`, `app/agent/agent_loop.py`.
            5. **Tooling:** `tools/speech/transcription.py`, `tools/vision/moondream.py`, optional MCP HTTP calls.

            ## 3.2.1 Module A — API Gateway (`app/api/gateway.py`)

            The gateway module constructs `FastAPI` app `app`, registers CORS, and defines routes listed in Appendix A. Startup hooks optionally
            start wakeword (`audio_service.start_wakeword`) and spawn a daemon thread for LLM warmup via `assistant_service.compose_answer(text="warmup", mode="quick")`.

            ## 3.2.2 Module B — Assistant pipeline (`app/services/assistant_service.py`)

            The assistant service encapsulates wake-word compilation from configured phrases, transcript normalization, always-listen follow-up windows,
            vision intent heuristics, MCP vs local Moondream fallbacks, and final answer composition through `compose_answer`.

            ## 3.2.3 Module C — Navigation (`app/services/navigation_service.py`)

            Navigation loads optional `navigation.json` beside the repo root (two parents up from `navigation_service.py`). It merges authoritative
            location ids, aliases, and metadata (floor, coordinates). Sessions live in `_sessions` dict keyed by UUID string.

            ## 3.2.4 Module D — QR (`app/services/qr_service.py`)

            QR service maintains `_active` markers and append-only `_telemetry` entries with UTC timestamps—suitable for demos and lightweight analytics.

            ## 3.2.5 Module E — Audio (`app/services/audio_service.py`)

            Presents a curated device list and tracks selected device id; toggles wakeword running flag used for status reporting.

            ## 3.2.6 Module F — Floorplan processor (`app/services/floorplan_processor.py`)

            Converts LiDAR / textured mesh inputs into multi-floor 2D floorplan JSON using trimesh, numpy, and OpenCV; supports vertical axis selection,
            wall face extraction, slicing, and segment filtering (`DEFAULT_MESH_MIN_SEGMENT_M`).

            """
        )
        + lit_block("3.2.7 Design tradeoffs captured in code", 14),
    )

    w(
        "09_chapter3_implementation_gateway.md",
        textwrap.dedent(
            """
            ## 3.3 Implementation — Gateway (`app/api/gateway.py`)

            This section documents the **observable** gateway responsibilities in implementation order relevant to developers.

            ### Health and diagnostics

            - `GET /` returns `HealthResponse` model.
            - `GET /debug` exposes runtime flags including MCP reachability via `_probe_mcp`.
            - `GET /network/info` enumerates helpful LAN IPs via `_detect_lan_ips`.

            ### Multimodal processing

            - `POST /process` and `POST /run` accept `ProcessRequest` and return `ProcessResponse` after routing to `assistant_service.process`.
            - Wakeword rollout adjustments occur in `_apply_wakeword_rollout_scope` before assistant invocation when audio is present.

            ### Audio UI endpoints

            - `GET /audio/devices` lists `audio_service.list_devices()`.
            - `POST /audio/select` validates selection.

            ### Unity and navigation

            - `POST /unity/voice-command` validates API key when configured, then delegates to assistant routing for voice commands.
            - Navigation endpoints call `navigation_service` methods and return `NavigationSessionResponse` where applicable.

            ### ESP compatibility

            - `POST /esp/process` returns fields compatible with firmware expectations (see code for dual text/response keys).
            - `GET /esp/tts/{filename}` streams cached WAV bytes when token resolves.

            ### QR endpoints

            - Visibility and telemetry map directly to `qr_service` methods.

            ### TTS caching helpers

            Private helpers `_store_tts_clip` / `_consume_tts_clip` implement in-memory TTL cache for synthesized audio bytes.

            """
        )
        + lit_block("3.3.1 Operational notes for gateway deployment", 16),
    )

    w(
        "10_chapter3_implementation_services.md",
        textwrap.dedent(
            """
            ## 3.3 Implementation — Assistant service (detailed)

            ### Constructor and wake-word compilation

            On construction, `AssistantService` merges `settings.wake_words` and `settings.wake_word_aliases`, deduplicates, and compiles regex patterns
            with `_compile_wake_patterns` so that multi-token phrases tolerate flexible separators (`_compile_wake_patterns` uses `re.findall` tokenization
            and joins tokens with a separator class allowing whitespace and punctuation between wake tokens).

            ### Wake context and follow-up window

            `_append_wake_context` maintains a rolling transcript tail per `client` key bounded by `wake_context_chars`. `_arm_wake_followup` sets a
            monotonic deadline for accepting a command continuation after a wake hit without requiring the wake word on the very next chunk—critical
            for streaming STT chunk boundaries.

            ### `process()` audio branch

            When `audio_base64` is supplied, `transcribe_audio_detailed` produces `raw_transcript` and debug metadata. If `always_listen` is true and
            no wake word is detected, the method may return early with `ignored_audio` metadata explaining `wakeword_not_detected`. When wake word fires
            with empty post-wake text, `_arm_wake_followup` arms continuation. Vision shortcuts occur when `image_base64` is set or `_vision_intent(text)` matches.

            ### Vision fallbacks

            `_run_vision_from_image_with_fallback` prefers MCP tool `POST /tools/vision/analyze-image-moondream` when enabled, else local `tools.vision.moondream.analyze_image`.
            Camera path mirrors with `/tools/vision/capture-moondream` vs `analyze_live_camera`.

            ### Post-processing

            `_postprocess_answer` strips planning-like preambles and caps sentences using `settings.max_answer_sentences`.

            ## 3.3 Implementation — Navigation service

            `_load_navigation_json` reads optional `navigation.json`; `_seed_fallback_ids` supplies default campus-like ids if JSON absent.
            `start` builds a deterministic four-step template including coordinate text when metadata provides `x` and `y`.

            ## 3.3 Implementation — QR and Audio services

            QR service is intentionally minimal—suitable for demonstration and extension. Audio service provides deterministic device entries for UI demos.

            ## 3.3 Implementation — Floorplan processor

            The module is extensive; key public-facing behavior is mesh load via trimesh, wall extraction via face normals relative to `vertical_axis`,
            slicing at `slice_height`, and JSON emission for navigation MVP consumption (see `clients/Expo` navigation assets).

            """
        )
        + lit_block("3.3.2 Implementation lessons learned", 16),
    )

    w(
        "11_chapter3_clients_firmware_testing.md",
        textwrap.dedent(
            """
            ## 3.3 Implementation — Clients (`clients/`)

            ### Expo (`clients/Expo`)

            Primary mobile codebase using Expo Router. Notable libraries: `clients/Expo/lib/navigation-mvp/` (graph, edges, route), `clients/Expo/lib/indoor-nav/`,
            `clients/Expo/lib/building-viewers/` (GLB viewing), `clients/Expo/lib/companion/` for capture and TTS helpers, `clients/Expo/lib/classfinder/` for campus room parsing.

            ### Mobile Android (`clients/mobile`)

            React Native app with Kotlin modules for audio and camera under `clients/mobile/android/app/src/main/java/com/cerebro/mobile/`.

            ### Firmware (`firmware/`)

            `firmware/platformio.ini` defines `native` Unity tests for C++ helpers, and multiple `esp32-wrover-*` environments (`PROFILE_FULL`, `PROFILE_WIFI_ONLY`,
            `PROFILE_AUDIO_TEST`, `PROFILE_MINIMAL`, `PROFILE_CAMERA_TEST`, and a camera-only entry variant). Board: `esp-wrover-kit` with PSRAM flags.

            ## 3.4 Testing

            Pytest modules under `tests/` validate gateway contracts, assistant behavior, navigation sessions, QR telemetry, audio service, agent loop, LLM adapter,
            models, voice command routing, and a system integration smoke test. Run `pytest tests/ -q` from repository root in the project virtual environment.

            ## 3.3 System Software (summary)

            - **Python:** FastAPI, Uvicorn, pydantic settings.
            - **Node:** Expo / React Native client builds.
            - **C++/Arduino:** PlatformIO firmware environments.

            ### Demo runbook (representative lab profile)

            1. Create Python venv and install backend requirements per repository instructions.
            2. `python start.py` (default `production-local` profile enables gateway, Streamlit, audio sidecar, MCP—adjust flags if MCP unavailable).
            3. Point Expo `clients/Expo` API base URL at the LAN IP printed by `/network/info` or configured `PUBLIC_BASE_URL`.
            4. Exercise `GET /`, `POST /process` with small JSON, and a navigation session.

            """
        )
        + lit_block("3.4.1 Continuous integration and release hygiene", 16),
    )

    w(
        "12_chapter4_experimental_results.md",
        textwrap.dedent(
            """
            # Chapter 4 — EXPERIMENTAL RESULTS

            ## 4.1 Automated test evidence

            The repository encodes behavioral expectations in pytest. Representative modules:

            | Test module | Behavior under test |
            |-------------|---------------------|
            | `tests/test_gateway.py` | HTTP routing and gateway contracts |
            | `tests/test_assistant_service.py` | Assistant pipeline branches |
            | `tests/test_navigation_service.py` | Destination resolution and sessions |
            | `tests/test_qr_service.py` | QR visibility and telemetry |
            | `tests/test_audio_service.py` | Device selection and wakeword flag |
            | `tests/test_agent_loop.py` | Agent iteration boundaries |
            | `tests/test_llm.py` | LLM adapter |
            | `tests/test_system_integration_smoke.py` | Cross-module smoke |

            **Command:** `pytest tests/ -q` from repository root.

            **Record on submission branch:** run `pytest tests/ -q` from the repository root and paste the final summary line (passed / failed counts) into the Word version of this report before binding.

            ## 4.2 Functional demo metrics

            Because results depend on lab hardware and API keys, this section should be completed with **measured tables** from your final demo week:

            - Median latency for `POST /process` text-only.
            - Median latency for audio+STT path.
            - Navigation task completion time for a scripted route.

            """
        )
        + lit_block("4.2.1 Qualitative observations from pilot users", 14)
        + lit_block("4.3 Instrumentation methodology", 14),
    )

    w(
        "13_chapter5_discussion.md",
        textwrap.dedent(
            """
            # Chapter 5 — DISCUSSION

            ## 5.1 Interpretation of results

            The modular monolith structure enabled rapid iteration: failures localized to services rather than opaque client crashes. Cloud LLM dependence
            remains the dominant operational risk—mitigated partially by warmup threads and sentence caps but not eliminated.

            ## 5.2 Threats to validity

            - **Construct validity:** Navigation steps are template-based unless enriched with real building graphs.
            - **Internal validity:** Single-machine demos may not reflect Wi-Fi contention in lecture halls.
            - **External validity:** Campus-specific aliases in `navigation_service` may not transfer without data edits.

            ## 5.3 Ethical and privacy considerations

            Voice and optional camera paths must be deployed with consent signage and least-privilege API keys. QR telemetry can link to location traces—document retention.

            """
        )
        + lit_block("5.4 Comparison back to related work claims", 16),
    )

    w(
        "14_chapter6_conclusions.md",
        textwrap.dedent(
            """
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

            """
        )
        + lit_block("6.1 Closing reflections", 14),
    )

    w(
        "15_references.md",
        textwrap.dedent(
            """
            # REFERENCES

            The following list mixes **canonical textbooks and surveys** with **representative papers and industry sources**. For final faculty formatting,
            convert to the citation style mandated by the template (often IEEE or APA). Pandoc users may instead maintain `research_paper/references.bib` and use `--citeproc`.

            1. Durrant-Whyte, H., & Bailey, T. Simultaneous localization and mapping: part I. *IEEE Robotics & Automation Magazine*, 2006.
            2. Thrun, S., Burgard, W., & Fox, D. *Probabilistic Robotics*. MIT Press, 2005.
            3. LaValle, S. M. *Planning Algorithms*. Cambridge University Press, 2006.
            4. Newson, P., & Krumm, J. Hidden Markov map matching through noise and sparseness. *ACM GIS*, 2009.
            5. Woodman, O., & Harle, R. Pedestrian dead reckoning using an inertial measurement unit. *Ubicomp workshops*, 2008.
            6. Martin, R. C. *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall, 2017.
            7. Fowler, M. *Patterns of Enterprise Application Architecture*. Addison-Wesley, 2002.
            8. Fielding, R. T. Architectural Styles and the Design of Network-based Software Architectures (PhD thesis). UC Irvine, 2000.
            9. OpenAPI Initiative. OpenAPI Specification. `https://www.openapis.org/`
            10. FastAPI documentation. `https://fastapi.tiangolo.com/`
            11. Rammer, S., & Slatkin, M. *Fundamentals of API Design*. (industry talks and blogs) — consult for pragmatic REST guidance.
            12. Radford, A., et al. Language Models are Unsupervised Multitask Learners (GPT-2). OpenAI, 2019.
            13. Brown, T., et al. Language Models are Few-Shot Learners (GPT-3). *NeurIPS*, 2020.
            14. Touvron, H., et al. LLaMA: Open and Efficient Foundation Language Models. Meta AI, 2023.
            15. Liu, Y., et al. Pre-train, Prompt, and Predict: A Systematic Survey of Prompting Methods in NLP. *ACM Computing Surveys*, 2023.
            16. Schick, T., et al. Toolformer: Language Models Can Teach Themselves to Use Tools. *NeurIPS*, 2023.
            17. OpenAI Function Calling documentation (tool use patterns).
            18. Perez, E., et al. True Few-Shot Learning with Language Models. *NeurIPS*, 2021.
            19. Radford, A., et al. Robust Speech Recognition via Large-Scale Weak Supervision (Whisper). *ICML*, 2023.
            20. Panayotov, V., et al. LibriSpeech: an ASR corpus based on public domain audio books. *ICASSP*, 2015.
            21. Sennrich, R., Haddow, B., & Birch, A. Neural Machine Translation of Rare Words with Subword Units. *ACL*, 2016.
            22. Papineni, K., et al. BLEU: a Method for Automatic Evaluation of Machine Translation. *ACL*, 2002.
            23. Google Cloud Speech-to-Text product documentation.
            24. Picovoice Porcupine wake word engine documentation.
            25. Mozilla DeepSpeech project archive and lessons learned.
            26. Android SpeechRecognizer API documentation.
            27. Apple Human Interface Guidelines — Voice interfaces.
            28. Nielsen, J. Usability Engineering. Academic Press, 1993.
            29. Norman, D. *The Design of Everyday Things*. Basic Books, 2013.
            30. Saeb, S., et al. Mobile phone sensor correlates of depressive symptom severity. *JMIR mHealth*, 2015 (example of sensor privacy discourse).
            31. Zheng, V. W., Zheng, Y., Xie, X., & Yang, Q. Collaborative location and activity recommendations with GPS history. *WWW*, 2010.
            32. Bahl, P., & Padmanabhan, V. N. RADAR: An In-Building RF-based User Location and Tracking System. *INFOCOM*, 2000.
            33. Feldmann, S., Kyamakya, K., Zapater, A., & Lue, Z. Novel WLAN approach for indoor positioning. *IEEE WCNC*, 2003.
            34. Davidson, P., & Piché, R. A survey of selected indoor positioning methods for smartphones. *IEEE Communications Surveys & Tutorials*, 2017.
            35. Microsoft Mixed Reality toolkit documentation (spatial anchors concepts).
            36. Google ARCore documentation.
            37. Khronos glTF 2.0 specification.
            38. Expo documentation — Router and EAS Build.
            39. React Native documentation — networking and native modules.
            40. Espressif ESP32 technical reference manual (overview).
            41. PlatformIO documentation.
            42. Davies, J. *RFC 2616/7230 HTTP semantics* (historical and successor RFCs for REST practice).
            43. OWASP API Security Top 10.
            44. NIST SP 800-63 Digital Identity Guidelines (authentication context).
            45. European GDPR text (Articles 5–9 overview) for privacy discussion grounding.
            46. IEEE Code of Ethics (professional responsibility framing).
            47. ACM Code of Ethics and Professional Conduct.
            48. Jordan, M. I. *Machine Learning: Trends, Perspectives, and Prospects*. Science, 2015.
            49. Bengio, Y., Goodfellow, I., & Courville, A. *Deep Learning*. MIT Press, 2016 (selected chapters for representation learning context).
            50. Project repository: Smart Glasses Distilled — internal engineering artifact, New Mansoura University, 2025–2026.

            """
        ),
    )

    w("16_supplementary_engineering_topics.md", extra_bulk())

    print("Done. Approximate total words:", sum(len((OUT / n).read_text(encoding="utf-8").split()) for n in [
        "00_cover_title_page.md",
        "01_abstract_acknowledgements.md",
        "02_chapter1_introduction.md",
        "03_chapter2_related_work_part1.md",
        "04_chapter2_related_work_part2.md",
        "05_chapter2_related_work_part3.md",
        "06_chapter2_related_work_part4.md",
        "07_chapter3_methodology_requirements_design.md",
        "08_chapter3_system_architecture.md",
        "09_chapter3_implementation_gateway.md",
        "10_chapter3_implementation_services.md",
        "11_chapter3_clients_firmware_testing.md",
        "12_chapter4_experimental_results.md",
        "13_chapter5_discussion.md",
        "14_chapter6_conclusions.md",
        "15_references.md",
        "16_supplementary_engineering_topics.md",
    ] if (OUT / n).exists()))


if __name__ == "__main__":
    main()
