# Legacy and Migration (Isolated from Main Docs)

This file tracks broken or transitional paths without polluting primary architecture docs.

## 1) Missing `flask.py` (Primary Interface Target)

- **What is broken:** `flask.py` is designated as primary interface but is missing from repo.
- **Why it exists:** architecture intent evolved, but implementation drifted during refactors.
- **Action:** **Refactor/restore** (do not delete concept). Recreate `flask.py` as canonical Flask surface aligned to `start.py` ecosystem.

## 2) `run_flask.py` Import Path Drift

- **What is broken:** `run_flask.py` imports `web_app.create_app`, but core `web_app` package is absent.
- **Why it exists:** earlier Flask architecture likely removed/moved without full launcher cleanup.
- **Action:** **Refactor** by either:
  - restoring `web_app` package, or
  - updating launcher to import canonical `flask.py` app factory.

## 3) Multiple Startup Scripts (`start_gateway.py`, `start_server.py`, old docs)

- **What is broken:** startup story is inconsistent with source-of-truth runtime (`start.py`).
- **Why it exists:** incremental migration from older split services to unified gateway flow.
- **Action:** **Refactor** docs/scripts around `start.py`; keep alternates only if explicitly needed and labeled.

## 4) Path Duplication Artifact (`server/gateway.py` and `server\gateway.py`)

- **What is broken:** duplicate path representations can confuse tooling and contributors.
- **Why it exists:** Windows path normalization and git/editor interactions.
- **Action:** **Refactor** repository hygiene and path references; enforce normalized paths in docs/scripts.

## 5) Sidecar Ambiguity (`server_audio.audio_stream_server`)

- **What is broken:** optional component may be treated as required by some clients.
- **Why it exists:** advanced Android streaming needs sidecar, while baseline runtime does not.
- **Action:** **Refactor docs/config** to make required-vs-optional explicit per client profile.

