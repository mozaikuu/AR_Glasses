# Smart Glasses System Overview

This document defines the authoritative product shape for this repository.

## Product Definition (Source of Truth)

- Runtime entry point: `start.py`
- Backend: `server.gateway` (FastAPI)
- Primary interface: `flask.py` (active production target)
- Advanced interface: Unity app in `hololens2-campus-nav`
- Mobile: secondary client (`mobile_native/android`)
- AI: hybrid inference (Cerebras preferred, local fallback supported)
- Speech: multi-input (ESP32, phone, browser, Unity)
- Hardware focus: MetaQuest (primary), Android (secondary), plus PC and ESP32
- `Review/` is experimental and excluded from core system docs

## Current Reality vs Target

- `start.py` correctly exists and launches `server.gateway`.
- `flask.py` is currently missing in the repository; this is a critical alignment gap.
- `server_audio.audio_stream_server` is optional but important for advanced Android streaming setups.

## High-Level Architecture

1. Clients collect user input (voice/text/image).
2. Input reaches FastAPI gateway (`server.gateway`).
3. Gateway performs STT (if audio), intent routing, and AI inference orchestration.
4. Agent uses MCP tools (navigation, vision, search) when needed.
5. Gateway returns response and optionally triggers TTS output.
6. Unity/ESP32/mobile clients render actions (speech, navigation, feedback).

## Scope Boundaries

- Included: `start.py`, `server/`, `tools/`, `agent/`, `models/`, `config/`, `mobile_native/`, `hololens2-campus-nav/`, `firmware/`.
- Excluded from core architecture: `Review/`, temporary analysis artifacts, stale prototypes not wired to `start.py`.

