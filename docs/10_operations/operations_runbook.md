# Operations Runbook

## Runtime Modes

- Standard all-in-one local production profile (gateway + flask + audio + mcp):
   - `uv run python start.py --profile production-local`
- Gateway only:
   - `uv run python start.py --profile gateway-only`

## Local Config Without Env Vars

- Use `local.settings.json` at repo root to configure ports and toggles.
- Environment variables are optional overrides when needed.
- For LAN/internet multi-device setup, see:
   - `docs/10_operations/multi_device_connectivity.md`

## Health Checks

- Backend health: `GET /`
- MCP status: `GET /mcp-status`
- Debug status: `GET /debug`
- Network profile and LAN/public URL hints: `GET /network/info`
- Audio devices: `GET /audio/devices`

## Test Commands

- Automated full test run:
   - `uv run python scripts/run_all_tests.py`
- Live HIL HTTP smoke check (run against active gateway):
   - `uv run python scripts/run_live_hil_check.py --base-url http://127.0.0.1:8000`
- Network diagnostics:
   - `uv run python -m scripts.print_network_info`
- Manual voice command validation:
   - follow `docs/07_api/10_command_test_sheet.md`

### Validation Artifacts

- Full stack report: `artifacts/test_report.json`
- Live HIL report: `artifacts/live_hil_report.json`

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
