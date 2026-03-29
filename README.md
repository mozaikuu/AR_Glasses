# Smart Glasses Distilled

Smart Glasses Distilled is a multimodal assistant platform for wearable and cross-device interaction (voice, text, image-assisted prompts, indoor navigation, and ESP integration).

## Quick Start

1. Create and activate your Python environment.
2. Install dependencies.
3. Run the unified profile:

```powershell
uv run python start.py --profile production-local
```

This starts the gateway plus the default local companion services defined by the launcher profile.

## Runtime Validation Runbook

### 1) Full Automated Stack Validation

Runs Python unit tests, integration smoke, firmware native tests (if PlatformIO is available), and Unity EditMode tests (if Unity executable is available):

```powershell
python scripts/run_all_tests.py
```

Report output:

- `artifacts/test_report.json`

### 2) Live Hardware-In-The-Loop HTTP Smoke Validation

Run against an already running gateway:

```powershell
python scripts/run_live_hil_check.py --base-url http://127.0.0.1:8000
```

Report output:

- `artifacts/live_hil_report.json`

### 3) Recommended Live Check Sequence

1. Start gateway.
2. Verify `GET /` and `GET /network/info`.
3. Run the live HIL checker.
4. Confirm all checks are `PASS` in the generated artifact.

## Project Structure

```text
.
├── app/                # Core Python runtime (gateway, services, models, agent)
├── AR-campus-nav/      # Unity AR navigation client and edit-mode tests
├── Firmware/           # ESP32 firmware variants and hardware docs
├── docs/               # Architecture, API, operations, product, and graduation docs
├── scripts/            # Test runners, setup helpers, diagnostics
├── tests/              # Python unit and integration tests
├── assets/             # Static assets and generated artifacts input/output
└── start.py            # Canonical launcher
```

## Documentation Index

### Graduation Package (Detailed Submission Set)

1. [docs/14_graduation/README.md](docs/14_graduation/README.md)
2. [docs/14_graduation/full_project_documentation.md](docs/14_graduation/full_project_documentation.md)
3. [docs/14_graduation/design_decisions_and_tradeoffs.md](docs/14_graduation/design_decisions_and_tradeoffs.md)
4. [docs/14_graduation/future_roadmap_and_research.md](docs/14_graduation/future_roadmap_and_research.md)

### Core Technical Docs

1. [docs/01_overview/system_overview.md](docs/01_overview/system_overview.md)
2. [docs/02_architecture/architecture.md](docs/02_architecture/architecture.md)
3. [docs/03_codebase/module_map.md](docs/03_codebase/module_map.md)
4. [docs/04_features/feature_flows.md](docs/04_features/feature_flows.md)
5. [docs/05_ai_system/ai_system.md](docs/05_ai_system/ai_system.md)
6. [docs/06_hardware/hardware_integration.md](docs/06_hardware/hardware_integration.md)
7. [docs/07_api/api_reference.md](docs/07_api/api_reference.md)
8. [docs/08_data/data_and_state.md](docs/08_data/data_and_state.md)
9. [docs/09_dev_guide/development_guide.md](docs/09_dev_guide/development_guide.md)
10.   [docs/10_operations/operations_runbook.md](docs/10_operations/operations_runbook.md)
11.   [docs/11_security/security_notes.md](docs/11_security/security_notes.md)
12.   [docs/12_product/product_narrative.md](docs/12_product/product_narrative.md)

## Design Contract

1. Keep `start.py` as the canonical launcher.
2. Keep business logic in `app/` modules and expose behavior through API contracts.
3. Keep client integrations contract-first (Unity, ESP, web, mobile).
4. Treat `scripts/run_all_tests.py` and `scripts/run_live_hil_check.py` as required pre-demo validation gates.
