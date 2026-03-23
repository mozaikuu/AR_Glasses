# Step-by-Step Setup

## 1) Install tooling
1. Unity Hub with one of these editors:
   - Preferred: `2022.3.62f1` (HoloLens 2 safer baseline)
   - Optional: `6000.0.49f1` (if you validate all packages)
2. In Unity installer, include:
   - Universal Windows Platform Build Support
   - Windows Build Support (IL2CPP)
3. Visual Studio 2022 with:
   - Desktop development with C++
   - Universal Windows Platform development
   - Windows 10/11 SDK

## 2) Open this project folder
1. In Unity Hub, Add project: `hololens2-campus-nav`.
2. Let package restore complete.
3. Open a sample scene from `Assets/Samples/MultiSet-SDK/...` only for reference.

## 3) Configure HoloLens 2 build target
1. File -> Build Settings -> Universal Windows Platform -> Switch Platform.
2. Target Device: `HoloLens`.
3. Architecture: `ARM64`.
4. Build Type: `D3D Project`.
5. Build and Run on: `Remote Device` (or `Local Machine` for emulator).

## 4) Configure XR and capabilities
1. Project Settings -> XR Plug-in Management:
   - Enable OpenXR for UWP.
2. OpenXR -> Features:
   - Enable Microsoft HoloLens feature group and hand tracking features you need.
3. Player Settings -> Publishing Settings -> Capabilities:
   - InternetClient
   - InternetClientServer (if backend requires it)
   - PrivateNetworkClientServer (same LAN testing)
   - Webcam
   - SpatialPerception

## 5) Wire QR localization
1. Add `BackendApiClient`, `HoloLensQrTracker`, and `QrModalController` to a bootstrap GameObject.
2. Set backend URL in `BackendApiClient`.
3. Make sure QR permission prompt appears on first device run.
4. Test with a printed QR code and check backend logs.

## 6) Add campus map and destinations
1. Edit `Assets/StreamingAssets/Campus/campus_graph.sample.json`.
2. Edit `Assets/StreamingAssets/Campus/qr_anchors.sample.json`.
3. Define building nodes, walkable edges, and destination IDs.

## 7) Add avatar guide behavior
1. Use a humanoid or robot avatar prefab.
2. Spawn avatar at user position after localization.
3. Compute route from current node -> destination node.
4. Animate avatar along waypoints and show arrow/path UI.

## 8) MultiSet decision gate (must do early)
1. Verify with MultiSet support if UWP/HoloLens 2 is officially supported now.
2. If yes:
   - Integrate MultiSet localization/navigation pipeline.
3. If no:
   - Keep MultiSet for mobile only, and use QR + graph routing for HoloLens.

## 9) Build and deploy
1. Build UWP from Unity.
2. Open generated solution in Visual Studio.
3. Set configuration: Release / ARM64 / Device.
4. Deploy to HoloLens 2 (USB or Wi-Fi).

## 10) Validate acceptance criteria
1. User scans QR and gets localized.
2. User chooses destination.
3. Route appears with clear instructions.
4. Avatar leads user to destination.
5. Relocalization works after losing tracking.

