# Smart Glasses Distilled

This workspace was reorganized into a clean, role-based layout focused on a single Python backend and multiple client integrations.

## Folder Structure

```text
.
├── app/                # Core Python application
│   ├── api/            # HTTP and websocket endpoints
│   ├── agent/          # LLM orchestration and reasoning loop
│   ├── tools/          # Tool integrations (vision/search/navigation/speech)
│   ├── services/       # Runtime services (ASR/TTS/session/routing)
│   ├── models/         # Request/response and domain models
│   ├── config/         # Settings and environment config
│   └── shared/         # Shared helpers
├── bus_system/         # Isolated Smart Bus Tracking MVP workspace
├── clients/            # External client adapters/projects
│   ├── unity/          # Unity/HoloLens integration assets
│   ├── esp32/          # ESP firmware integration notes/assets
│   ├── mobile/         # Mobile client integration
│   └── browser/        # Browser/web integration
├── docs/               # Product and technical documentation
├── scripts/            # Utility scripts for setup/dev/ops
├── tests/              # Automated and smoke tests
├── assets/             # Static assets and models
└── archive/            # Legacy or deprecated snapshots
```

## Startup Contract

- Keep one launcher at project root: `start.py`.
- Core runtime code should live under `app/`.
- Clients should consume APIs only (no direct imports from internal modules).

## Bus System Workspace

All Smart Bus Tracking MVP modules are grouped under `bus_system/` for easier access:

- `bus_system/backend/` API and simulation runtime integration
- `bus_system/frontend/` Next.js dashboard and PWA
- `bus_system/simulation/` route and prediction modules
- `bus_system/agent_tools/` Cerebro tool wrappers
- `bus_system/docs/bus_tracking_mvp/` MVP docs

## Next Move

Place your current backend files under `app/` by responsibility (api/agent/tools/services/etc.), then update imports to use package paths from `app`.
