# Developer Guide

## Local Setup

1. Create/activate virtual environment
2. Install dependencies (`uv sync` preferred)
3. Configure environment variables (API keys, model/runtime settings)
4. Start backend with `uv run python start.py`
5. Optionally add audio sidecar: `uv run python start.py --with-audio`

## Single Command Local Production Run

- Start full stack (gateway + flask + sidecar + mcp):
   - `uv run python start.py --profile production-local`
- This uses `local.settings.json` by default so env vars are not required.

## Recommended Developer Flows

- Backend validation:
   - check `GET /`
   - test `POST /process` text-only first
- Speech validation:
   - test `/audio/devices`
   - test `/record` with selected mic
- Navigation validation:
   - test `/navigation/locations` then `/navigation/start`
- Unity validation:
   - confirm `serverBaseUrl` points to active backend host

## Flask Mic STT to LLM Check

- Open Flask UI at `http://localhost:5000`.
- Click `Mic STT - LLM Test`.
- Browser speech recognition transcribes microphone speech and sends it through `/api/process`.

## Easy Full Test Run

- One command automated checks:
   - `uv run python scripts/run_all_tests.py`
- This runs:
   - unit tests under `tests/`
   - gateway smoke checks for core API paths
   - writes JSON report to `artifacts/test_report.json`
- Live HIL smoke check against a running gateway:
   - `uv run python scripts/run_live_hil_check.py --base-url http://127.0.0.1:8000`
- Live HIL report output:
   - `artifacts/live_hil_report.json`
- Manual voice-router validation sheet:
   - `docs/07_api/10_command_test_sheet.md`

## Environment Policy

- Use environment variables for:
   - API keys (Cerebras and any provider keys)
   - network host/port overrides
   - optional model/runtime toggles
- Do not commit secrets in code or config files.

## Debugging Priorities

- First verify runtime/port alignment (`start.py` path only).
- Then verify client network reachability to backend host.
- Then inspect inference/tool errors from gateway logs.
