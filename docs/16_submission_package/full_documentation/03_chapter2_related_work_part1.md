# Chapter 2 — RELATED WORK

## 2.1 Existing Systems

This section surveys classes of systems that overlap with Smart Glasses Distilled. We structure the review to mirror the faculty
template (existing systems, limitations, comparison) while grounding comparisons in **concrete architectural choices** present in
our codebase: a single Python gateway, explicit REST routes, in-memory navigation sessions unless extended, and optional MCP integration.

### 2.1.1 Wi-Fi fingerprinting and RSSI maps

Wi-Fi fingerprinting records spatial patterns of received signal strength (RSSI) from visible access points and matches live scans to a stored radio map. It is attractive on campuses because infrastructure already exists and client APIs are widely available.

Accuracy is sensitive to device heterogeneity, AP power changes, crowd absorption, and multipath in long corridors. Student deployments should budget time for calibration walks, versioning of radio maps, and clear degradation behavior when similarity scores are ambiguous.

For this project, indoor positioning is not claimed as a novel Wi-Fi contribution; instead, navigation steps are served by the gateway from structured data (`navigation.json` / client assets), while connectivity remains a transport concern for STT/TTS and HTTP APIs.


### 2.1.2 BLE beacons and proximity graphs

BLE beacons advertise identifiers at low duty cycle, enabling proximity zones and coarse graph nodes (“near the lab door”) rather than continuous metric coordinates. Beacon systems trade installation effort (battery swaps, mounting policy) against reliability.

Interference from human bodies, scheduling jitter on scanners, and inconsistent scan APIs across Android vendors affect repeatability. Engineering practice often combines BLE regions with Wi-Fi or inertial hints.

Smart Glasses Distilled can consume BLE-derived context if exposed to the gateway as metadata, but the repository’s primary navigation story is session-based instructions aligned with authored floor content.


### 2.1.3 Ultra-wideband and time-of-flight ranging

UWB time-of-flight can yield decimeter-level ranges between anchors and tags in favorable geometry. It addresses some multipath pitfalls of narrowband RSSI, but requires dedicated silicon and anchor deployment budgets uncommon in coursework unless sponsored.

NLOS (non-line-of-sight) paths, metal studs, and multipath still produce outliers; robust fusion filters and outlier rejection are part of real products.

The graduation codebase does not implement a UWB stack; UWB appears here only as related work context when comparing precision localization research to gateway-mediated campus assistance.


### 2.1.4 Pedestrian dead reckoning with IMU

Pedestrian dead reckoning integrates accelerometer and gyroscope signals to propagate step counts and heading changes from a last-known anchor. Short windows work well; drift accumulates without absolute fixes.

Phone and wearable IMU pipelines differ in sampling stability and mounting; backpack versus handheld versus glasses mount changes step detection thresholds.

Client-side PDR could complement server-delivered navigation in future work, but the current navigation service issues discrete steps from authored graphs rather than fusing continuous IMU tracks.


### 2.1.5 Visual odometry and visual-inertial odometry

Visual odometry tracks camera motion from frame-to-frame feature correspondences; VIO fuses IMU predictions with visual updates for smoother trajectories under motion blur or low texture.

Indoor repetition (blank walls, fluorescent flicker) challenges feature stability; compute and thermal budgets matter on phones and embedded boards.

The project’s vision path supports contextual Q&A (Moondream/MCP) rather than claiming a full VIO localization pipeline; AR clients remain consumers of gateway responses and authored spatial assets.


### 2.1.6 SLAM in indoor environments

SLAM jointly estimates a sensor trajectory and a map representation (often occupancy grids or sparse landmarks). Indoor SLAM must handle glass, dynamic pedestrians, and symmetric corridors where loop closure is ambiguous.

Operational SLAM stacks require calibration, map maintenance, and failure recovery UX when tracking is lost.

Repository scope includes mesh/floorplan processing helpers for authoring navigation assets, not a production SLAM front-end running on-device during every walk.


### 2.1.7 Topological maps versus metric maps

Topological maps represent places and adjacency (“A–B corridor connects to stairwell S”) and align with human turn-by-turn instructions. Metric maps add coordinates for AR overlays and precise distance estimates.

Many campus assistants only need topology plus a handful of metric anchors for rendering.

The gateway’s navigation sessions are naturally topological step lists enriched with optional coordinate text when metadata exists—matching how mobile clients prompt users without requiring centimeter fixes.


### 2.1.8 Graph search and A* on floor meshes

Floor meshes or extracted polylines can be discretized into graphs for shortest-path planning. A* remains the default teaching example when an admissible heuristic exists (e.g., Euclidean lower bound in open spaces).

Stairwells, one-way doors, and elevators require edge constraints and multi-floor supergraphs.

The Expo client contains MVP graph/route utilities; the backend navigation service remains deliberately simple for reproducible demos, with room to plug richer planners later.


### 2.1.9 Multi-floor routing and elevator modeling

Vertical circulation breaks 2D assumptions: elevators, stairs, and accessibility ramps need typed edges with wait-time distributions or at least static penalties.

Elevator banks also introduce statefulness (which car arrives), usually ignored in student prototypes.

Future extensions could model floors explicitly in `navigation.json`; current sessions illustrate the API contract with template-like multi-step routes.


### 2.1.10 Campus-scale GIS integration

Outdoor GIS layers (roads, footpaths) integrate cleanly with GPS, while indoor footprints often live in CAD/BIM or vendor-specific indoor GIS products.

Bridging indoor and outdoor graphs at building entrances is a classic integration seam.

The project’s demonstrator focuses on HTTP services and authored indoor assets; campus GIS could supply authoritative building footprints as upstream data sources.


### 2.1.11 Accessibility and inclusive routing

Inclusive routing prefers ramps and elevators, avoids stairs when a user requires step-free paths, and may widen corridors for turning radius in wheelchairs.

Policy data must be trustworthy; mislabeling an elevator as “out of service” has higher stakes than a generic detour.

Any production deployment should validate accessibility edges with facilities management; the current codebase exposes navigation text hooks where such policies would be enforced.


### 2.1.12 Commercial indoor navigation SDKs

Commercial SDKs bundle mapping tools, anchor management, analytics, and SLAs. They accelerate time-to-market but create licensing, data residency, and customization constraints.

SDK black boxes complicate academic evaluation when raw likelihoods or maps cannot be exported.

Smart Glasses Distilled prioritizes open, testable HTTP contracts so thesis artifacts remain inspectable without a proprietary indoor engine dependency.


### 2.1.13 OpenStreetMap indoor and Simple Indoor Tagging

OpenStreetMap indoor extensions and Simple Indoor Tagging (SIT) encourage community-editable floor polygons, doorways, and routing graphs. They democratize basemaps but require governance to prevent stale indoor geometry.

Quality varies by contributor skill and building access permissions.

Where OSM indoor data exists for a campus, it could seed `navigation.json` graphs; maintenance workflows remain an organizational problem beyond code.


### 2.1.14 Digital twins for buildings

Digital twins keep live or periodically refreshed models of HVAC, occupancy, and structural assets. Navigation can consume twin updates (e.g., blocked corridor) if fed into the routing graph.

Twins imply data pipelines, authentication, and schema alignment between BIM and runtime services.

This project does not operate a twin back end; the subsection situates future integration if a campus exposes standardized indoor change feeds.


### 2.1.15 Simulation-to-reality transfer for navigation ML

Learning navigation policies in simulation enables cheap data, but policies brittle to lighting, texture, and human density fail on real floors without domain randomization or fine-tuning.

Evaluation must separate “planner success in sim” from “task success with real users carrying phones at walking pace.”

The repository’s regression story is pytest on HTTP behavior rather than RL navigation training; sim-to-real remains future research adjacent to the implemented gateway.
