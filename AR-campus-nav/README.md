# HoloLens 2 Campus Navigation (Spike)

This folder is an isolated Unity spike for HoloLens 2 without changing your existing Unity projects.

## What was prepared

- Base Unity project copied from `ar-nav-multiset` (`Assets`, `Packages`, `ProjectSettings` only).
- Existing HoloLens QR scripts copied from `AR_Cerebro/Assets` into `Assets/Scripts/HoloLens`.
- Step-by-step setup, architecture, and data templates added.

## Important compatibility note

- This copied project currently has Unity `6000.2.8f1` in `ProjectSettings/ProjectVersion.txt`.
- Microsoft HoloLens 2 OpenXR guidance states support was discontinued after June 23, 2025 for versions beyond OpenXR `1.14.3`, Unity `2022.3.62f1`, and Unity `6000.0.49f1`.
- For lowest risk, run this spike on `2022.3.62f1` (or `6000.0.49f1` if you validate your stack).

See `Docs/STEP_BY_STEP.md` first.
