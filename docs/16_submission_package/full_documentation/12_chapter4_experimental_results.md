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

### 4.2.1 Qualitative observations from pilot users

Pilot users often mention confidence after the first successful navigation loop, frustration with false wake events, and surprise at LAN-only setup steps.

Capture anonymized quotes (with consent) and map them to UX changes implemented before defense.

Qualitative themes complement—not replace—latency tables.

### 4.3 Instrumentation methodology

Instrumentation should record wall-clock timings per pipeline stage and basic counters (sessions started, cancellations). Use consistent units (ms) in tables.

For audio, log buffer sizes and sample rates whenever comparing devices.

Describe hardware (phone model, ESP board, router) beside any numbers so results are reproducible.
