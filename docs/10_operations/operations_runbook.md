# Operations Runbook

## Runtime Modes

- Standard all-in-one local production profile (gateway + flask + audio + mcp):
   - `uv run python start.py --profile production-local`
- Gateway only:
   - `uv run python start.py --profile gateway-only`

## Local Config Without Env Vars

- Use `local.settings.json` at repo root to configure ports and toggles.
- Environment variables are optional overrides when needed.

## Health Checks

- Backend health: `GET /`
- MCP status: `GET /mcp-status`
- Debug status: `GET /debug`
- Audio devices: `GET /audio/devices`

## Test Commands

- Automated full test run:
   - `uv run python scripts/run_all_tests.py`
- Manual voice command validation:
   - follow `docs/07_api/10_command_test_sheet.md`

## Failure Scenarios

- Backend starts but no AI response:
   - verify API key env vars
   - verify MCP connection and tool availability
- Mic not working:
   - verify selected input device and permissions
   - verify source client path (browser/mobile/unity/server mic)
- Unity navigation mismatch:
   - destination exists in Unity scene but not in server graph (or vice versa)
- Android streaming failure:
   - sidecar disabled while app expects websocket path

## Operational Risks

- Single-process in-memory state loss on restart.
- No orchestration layer for multi-instance production scale.
- Optional sidecar can create mode confusion if client assumptions differ.

## Suggested Reliability Upgrades

- Add structured telemetry and request tracing IDs.
- Externalize session state for navigation/wakeword events.
- Add startup self-check endpoint for dependencies and model readiness.
