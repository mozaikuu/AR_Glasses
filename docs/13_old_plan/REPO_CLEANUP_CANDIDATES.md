# Repo Cleanup Candidates

This is a cautious review list. Nothing here should be moved or deleted automatically without your approval.

## Delete Rather Than Archive

These are generated folders for the active Unity project and are usually recreated by Unity:

- `hololens2-campus-nav/Library`
- `hololens2-campus-nav/Build`
- `hololens2-campus-nav/Logs`
- `hololens2-campus-nav/obj`
- `hololens2-campus-nav/UserSettings`
- `hololens2-campus-nav/.vs`
- `hololens2-campus-nav/.utmp`
- `hololens2-campus-nav/Android`

## Strong Move-To-Deprecated Candidates

- `qr_codes`
- `Review`
- `Temp`
- `server.log`
- `server_startup.log`
- root zero-byte junk files:
  - `'3.13'`
  - `start_frame]`
  - `uv`

## Likely Stale In The Unity Project

- `hololens2-campus-nav/Assets/_Recovery/0.unity`
- `hololens2-campus-nav/Assets/StreamingAssets/Campus/qr_anchors.sample.json`

## Stale Docs To Review

These still describe the QR-based flow and should not be treated as authoritative:

- `hololens2-campus-nav/README.md`
- `hololens2-campus-nav/Docs/STEP_BY_STEP.md`
- `hololens2-campus-nav/Docs/NAVIGATION_SETUP.md`
- `hololens2-campus-nav/Docs/ARCHITECTURE.md`

## Needs A Decision First

- root `navigation.json` versus `hololens2-campus-nav/Assets/StreamingAssets/Campus/navigation.json`
- `hololens2-campus-nav/Assets/MultiSet.7z`
- `hololens2-campus-nav/Assets/Samples/MultiSet-SDK`

## Do Not Move Automatically

- `hololens2-campus-nav/Assets/Scripts`
- `hololens2-campus-nav/Assets/Scenes`
- `hololens2-campus-nav/Packages`
- `hololens2-campus-nav/ProjectSettings`
- `hololens2-campus-nav/Assets/StreamingAssets/Campus/navigation.json`
