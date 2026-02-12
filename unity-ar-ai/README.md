# Unity AR QR Modal (HoloLens 2)

This scaffold implements:
- HoloLens 2 QR tracking
- A modal panel that stays visible while the QR code is visible
- Backend calls to Python gateway/API for visible/hidden/telemetry events

## Added Backend Endpoints

In `server/gateway.py`:
- `POST /qr/visible`
- `POST /qr/hidden`
- `GET /qr/active`
- `POST /qr/telemetry`

In `server/api_v2.py`:
- `POST /v2/qr/visible`
- `POST /v2/qr/hidden`
- `GET /v2/qr/active`
- `POST /v2/qr/telemetry`

## Unity Scripts

- `Assets/Scripts/Networking/BackendApiClient.cs`
- `Assets/Scripts/UI/QrModalController.cs`
- `Assets/Scripts/QR/HoloLensQrTracker.cs`

## Scene Wiring

1. Create a `GameObject` named `Backend`.
2. Add `BackendApiClient` component.
3. Set `baseUrl` to your running gateway, for example:
   - `http://<YOUR_PC_IP>:8000`
4. Create a world-space `Canvas` with a panel and text elements.
5. Add `QrModalController` to a `GameObject` and assign:
   - `modalRoot`: panel object
   - `titleText`: title text
   - `detailsText`: body text
6. Create a `GameObject` named `QrTracker`.
7. Add `HoloLensQrTracker` and reference:
   - `backendClient`
   - `modalController`

## HoloLens 2 Build Prerequisites

1. Unity + OpenXR enabled.
2. Install Mixed Reality OpenXR plugin.
3. Install QR tracking support for HoloLens 2 (`Microsoft.MixedReality.QR` package path used by `HoloLensQrTracker` on UWP).
4. Player Settings:
   - Publishing Settings -> Capabilities: enable `WebCam`, `InternetClient`, `SpatialPerception`
5. Build target: `UWP`, architecture `ARM64`, device `HoloLens`.

## Backend Payload Format

QR code payload should be JSON, compatible with `tools/navigation/qr_location.py`, for example:

```json
{
  "type": "location",
  "id": "hall_2_1_84",
  "name": "Hall 2-1-84",
  "building": "Main Building",
  "floor": 2,
  "coordinates": { "x": 14.2, "y": 5.8 },
  "description": "Lecture hall",
  "additional_info": "Left side corridor"
}
```
