# Developer Guide

## Local Setup

1. Create/activate virtual environment
2. Install dependencies (`uv sync` preferred)
3. Configure environment variables (API keys, model/runtime settings)
4. Start backend with `python start.py`
5. Optionally add audio sidecar: `python start.py --with-audio`

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

