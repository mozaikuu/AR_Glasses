# Appendix B — Testing matrix

| Test module | Primary behavior under test | Last run (fill in Word) |
|-------------|-----------------------------|-------------------------|
| `tests/test_gateway.py` | FastAPI gateway routes and response contracts | |
| `tests/test_assistant_service.py` | Assistant pipeline, wake-word branches, vision shortcuts | |
| `tests/test_navigation_service.py` | Destination resolution, session lifecycle | |
| `tests/test_qr_service.py` | QR visibility, telemetry append | |
| `tests/test_audio_service.py` | Device list, selection, wakeword flag | |
| `tests/test_agent_loop.py` | Agent iteration limits | |
| `tests/test_llm.py` | LLM adapter integration | |
| `tests/test_models.py` | Pydantic request/response models | |
| `tests/test_system_integration_smoke.py` | Cross-module smoke assumptions | |
| `tests/test_voice_command_routing.py` | Unity-style voice command routing | |
| `tests/test_nav_runner.py` | Navigation runner utilities | |
| `tests/test_settings_helpers.py` | Settings parsing from env / JSON | |
| `tests/test_compat_imports.py` | Import compatibility guards | |

**Canonical command (repository root):** `pytest tests/ -q`

Continuous integration: if the team adds GitHub Actions or similar, record the workflow name and badge URL in the final Word document.
