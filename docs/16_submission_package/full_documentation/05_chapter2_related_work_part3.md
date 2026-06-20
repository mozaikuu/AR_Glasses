# Chapter 2 — RELATED WORK (continued)

## 2.2 Overall Problems of Existing Systems

### 2.3.1 Smart glasses form factors and optics

Smart glasses vary from monocular HUDs to binocular AR with waveguides. Optics drive field of view, brightness outdoors, and comfort for long wear.

Battery and thermal limits cap continuous camera streaming.

In this repository, glasses-class experiences are treated as one client profile; the primary engineering artifact remains the gateway and service modules.


### 2.3.2 AR headsets and scene understanding

Headset SLAM and scene meshes unlock occlusion and anchoring, but require runtime permissions, calibration, and developer tooling.

Unity-based clients can visualize navigation cues aligned to spatial maps when assets exist.

`hololens2-campus-nav` / Unity clients in the wider workspace narrative consume gateway commands rather than replacing server-side orchestration.


### 2.3.3 Companion phone apps as hybrid architecture

Phones supply compute, radios, and batteries while wearables stay lightweight. The hybrid pattern is common when glasses stream sensors uplink.

Bluetooth/Wi-Fi handoff and background execution limits shape reliability.

Expo and React Native clients in `clients/` exemplify the companion role calling the same REST API surface.


### 2.3.4 ESP32 as voice peripheral

ESP32 boards can capture audio, show minimal UI, and stream or post to a gateway. PSRAM variants help buffering.

Firmware profiles in `firmware/platformio.ini` document staged capability builds.

`/esp/process` and `/esp/tts/{filename}` document the contract students should defend as “embedded-friendly API design.”


### 2.3.5 Real-time operating constraints on MCUs

MCUs prioritize deterministic ISRs and bounded heap use versus garbage-collected servers. Wi-Fi stack activity can starve audio pipelines without careful task priorities.

Watchdog resets and brownouts appear under heavy simultaneous capture.

Firmware documentation should mention tested profiles rather than claiming all features concurrently on minimal silicon.


### 2.3.6 HTTP as lingua franca for student projects

HTTP/JSON tooling is universal across Python, mobile, and embedded HTTP clients. It trades binary efficiency for debuggability and rapid iteration.

WebSockets remain optional for streaming events when polling is insufficient.

The gateway’s REST-first approach keeps integration grades transparent to examiners reading `app/api/gateway.py`.


### 2.3.7 Unity as client runtime for spatial UI

Unity provides mature 3D pipelines for AR navigation cues, asset bundles, and cross-platform export. Build sizes and IL2CPP compile times are practical costs.

Scene graphs should remain thin; business logic belongs server-side where possible.

Unity voice command routes in the gateway show how spatial clients still authenticate like other HTTP clients.


### 2.3.8 React Native and Expo for rapid mobile iteration

Expo accelerates UI iteration with OTA updates and managed workflows, while still allowing native modules when required.

Networking stacks must handle LAN IPs and TLS lab quirks.

`clients/Expo` integrates navigation MVP libraries and companion capture helpers tied to the gateway.


### 2.3.9 QR codes for provisioning and context jumps

QR codes bridge physical places to digital state: join a room session, fetch a floorplan, or mark lab equipment context.

They are weak secrets unless rotated; treat encoded tokens as capabilities with TTL.

`qr_service` implements visibility toggles and telemetry suitable for demo analytics extensions.


### 2.3.10 Field studies of wearable assistants

Wearable field studies emphasize ecological validity: walking speed, sunlight, social embarrassment, and audio noise.

Sample sizes in student projects are small; qualitative codes still help.

Pilot notes for Chapter 4 should cite observed failure modes (network drop, wrong wake) not only happy-path screenshots.


### 2.3.11 Cognitive load and attention models

Glanceable UI reduces fixation time compared to phone map apps; voice prompts add auditory load that competes with conversation.

Designers should chunk instructions and offer repetition commands.

Gateway sentence caps (`MAX_ANSWER_SENTENCES`) align answers with low-attention contexts.


### 2.3.12 Comparison matrix: proposed vs prior architectures

Prior architectures often split per client (separate Flask + Unity + ESP endpoints) or hide logic inside vendor SDKs.

The proposed system centralizes orchestration behind FastAPI with explicit models and tests.

Chapter 2’s comparison table should be updated whenever routes change—keep it aligned with `SOURCE_ALIGNMENT.md`.
