# Migration Notes

## 2026-03-21 - Structure Consolidation

Because the workspace content was absent at migration time, a clean folder scaffold was created to enforce a maintainable architecture:

- `app/` for backend runtime and business logic
- `clients/` for integration surfaces (unity, esp32, mobile, browser)
- `docs/`, `scripts/`, `tests/`, `assets/`, `archive/` for clear boundaries

This structure keeps startup simple with a single root `start.py` and moves all runtime internals under `app/`.
