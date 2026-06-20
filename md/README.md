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

## Next Move

Place your current backend files under `app/` by responsibility (api/agent/tools/services/etc.), then update imports to use package paths from `app`.

---

Copyright © 2026 Ahmed Moussa

This software is provided to New Mansoura University solely for academic evaluation purposes.

No license, ownership rights, distribution rights, modification rights, or commercial rights are granted.

All intellectual property rights remain with the author.
