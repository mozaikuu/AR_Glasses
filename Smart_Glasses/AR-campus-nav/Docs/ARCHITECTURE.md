# Architecture for Campus Navigation

## Core flow
1. QR scan gives anchor identity.
2. Anchor identity maps to nearest campus graph node.
3. User selects destination node.
4. Router computes shortest path in graph.
5. Avatar follows path and gives guidance.
6. App relocalizes when a new QR code is detected.

## Recommended runtime modules
- `HoloLensQrTracker`: detects QR and sends visibility events.
- `BackendApiClient`: sends QR events and receives metadata.
- `CampusGraphProvider` (to implement): loads graph JSON.
- `RoutePlanner` (to implement): A* or Dijkstra.
- `AvatarGuideController` (to implement): path-following and animations.
- `NavigationUI` (to implement): destination picker + progress.

## Data contracts
- `qr_anchors.sample.json`: maps QR payload -> node ID.
- `campus_graph.sample.json`: nodes + edges + metadata.

## Fallback strategy
- If MultiSet is not HoloLens-compatible, ship QR+graph navigation first.
- Keep the localization interface abstract so MultiSet can be plugged in later.
