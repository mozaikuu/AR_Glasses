# Meta Quest Location Popup Memory

## Purpose

This file is the working memory for the university place-info popup task so we can restart future sessions without losing context.

## Current Direction

- Target platform: Meta Quest / Android.
- Localization path: MultiSet SDK for Unity on Android, not HoloLens/UWP.
- Popup behavior: show nearby place information when the user is close to an office, lecture room, lab, or other POI.
- Data source: `Assets/StreamingAssets/Campus/navigation.json`.

## Why The Direction Changed

- The installed MultiSet package in this repo documents iOS and Android flows.
- The local `MultiSetSDK.dll.meta` disables `Windows Store Apps`, which makes the earlier HoloLens-first plan risky.
- Meta Quest keeps the project aligned with the installed SDK and the current Android player settings.

## What Was Found

- A first draft of the popup system already existed under `Assets/Scripts/LocationInfo`.
- The draft was incomplete:
  - `LocationTrigger` depended on player colliders and would not work well for headset-only AR.
  - `LocationDataManager` expected a `TextAsset`, but the JSON is in `StreamingAssets`, which needs Android-safe loading.
  - `LocalizationWrapper` was mostly a simulation stub.
  - `SampleScene` was not wired with the popup system.
  - Old QR docs and QR sample data still exist.

## Changes Made In This Pass

### Code

- Updated `Assets/Scripts/LocationInfo/LocationDataModels.cs`
  - Added `deskLabel` and `coursesTaught` to office staff entries.
  - Added helper methods for checking whether a staff member is available today.

- Reworked `Assets/Scripts/LocationInfo/LocationDataManager.cs`
  - Loads from `StreamingAssets/Campus/navigation.json` by default.
  - Supports Android/Quest-safe loading through `UnityWebRequest` when needed.
  - Added load state/events and a public `DebugMode` getter.

- Reworked `Assets/Scripts/LocationInfo/LocationTrigger.cs`
  - Added distance-check mode for localized/headset pose proximity.
  - Kept collider-trigger fallback mode.
  - Removed the private `debugMode` access bug.

- Reworked `Assets/Scripts/LocationInfo/LocationInfoPopup.cs`
  - Replaced corrupted text characters with ASCII-safe labels.
  - Added display support for desk labels, courses taught, and today's availability.

- Reworked `Assets/Scripts/LocationInfo/LocationInfoSetup.cs`
  - Ensures the data manager is configured before loading.
  - Can create trigger objects without a prefab if needed.
  - Defaults toward distance-based proximity for headset AR.

- Reworked `Assets/Scripts/Navigation/LocalizationWrapper.cs`
  - Quest-first MultiSet bridge.
  - Subscribes to MultiSet localization events when available.
  - Keeps the live pose synced to the tracked camera after localization.
  - Still supports editor simulation.

- Updated `Assets/Scripts/Navigation/NavigationSetup.cs`
  - Default navigation target names now better match the JSON ids.

### Data

- Updated both copies of `navigation.json`
  - Added desk labels and example courses taught for office staff.

## Important Remaining Manual Unity Steps

1. Open the Unity project so it imports the pasted scripts and generates missing `.meta` files.
2. Create a world-space popup prefab and assign the `LocationInfoPopup` references.
3. Add `LocationInfoSetup` to the scene.
4. Assign the popup prefab to `LocationInfoSetup`.
5. Add or confirm a MultiSet localization manager in the scene.
6. Add `LocalizationWrapper` to a bootstrap object and assign the proper MultiSet manager if auto-find does not pick it up.
7. Run `LocationInfoSetup -> Setup: Create Location Triggers`.
8. Test proximity using the localized camera pose on Quest.

## Cleanup Candidates To Review Later

- Generated folders to delete, not archive:
  - `hololens2-campus-nav/Library`
  - `hololens2-campus-nav/Build`
  - `hololens2-campus-nav/Logs`
  - `hololens2-campus-nav/obj`
  - `hololens2-campus-nav/UserSettings`
  - `hololens2-campus-nav/.vs`
  - `hololens2-campus-nav/.utmp`
  - `hololens2-campus-nav/Android`

- Candidates to move into `Depricated` only after you approve:
  - `qr_codes`
  - `Review`
  - `Temp`
  - `server.log`
  - `server_startup.log`
  - zero-byte junk files at repo root

- Do not move automatically:
  - `hololens2-campus-nav/Assets/Samples/MultiSet-SDK`
  - either `navigation.json` copy until one source of truth is chosen
  - `Assets/MultiSet.7z`

## Next Best Step

Open the Unity project, let it reimport, then wire the popup prefab and test the Quest localization scene with the updated scripts.
