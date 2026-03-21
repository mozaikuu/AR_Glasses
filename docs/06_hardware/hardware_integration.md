# Hardware Integration

## Supported Targets

- Primary: MetaQuest (Unity base in `hololens2-campus-nav`)
- Secondary: Android gateway device
- Also supported: PC and ESP32 glasses firmware

## ESP32 Capabilities

- Camera (OV2640-oriented setup in firmware)
- Microphone input over I2S
- BLE communication with phone
- Optional WiFi/server communication
- IMU hooks and haptic feedback patterns

## Communication Modes

- **Mode A (phone relay):** ESP32 -> BLE -> Android -> backend
- **Mode B (direct):** ESP32 -> WiFi -> backend server directly

## Unity/MetaQuest Hardware Interaction

- Voice capture and command routing
- Navigation rendering and movement using NavMesh
- Optional server intent routing for richer command handling

## Performance and Resource Constraints

- ESP32 has strict memory and compute budgets.
- Camera frame size/quality trade-offs are mandatory for reliability.
- BLE throughput is limited for rich media; best for commands/state.
- Direct WiFi mode improves bandwidth but increases setup/network dependency.

## Bottlenecks

- Audio quality from wearable microphones in noisy environments.
- Inter-device networking reliability (phone relay and LAN reachability).
- Synchronization consistency between server intent and Unity local navigation state.

