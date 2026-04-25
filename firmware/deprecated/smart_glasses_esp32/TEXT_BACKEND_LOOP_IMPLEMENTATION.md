# ESP32 Text Loop Integration Report (iPhone + Backend)

## Goal
Enable a microphone-free validation path where text can be injected from phone-side BLE, processed by the backend, and routed back to ESP32 over BLE.

Target flow:
1. Phone writes text to ESP32 (placeholder for mic command).
2. ESP32 emits command event back to phone gateway.
3. Phone gateway sends text to server for LLM processing.
4. Server returns response text.
5. Phone gateway sends response back to ESP32 as TTS text payload.

## Thought Process and Decisions
1. The existing minimal ESP sketch was not self-contained (missing includes/pin/UUID definitions), so the first priority was making firmware compilable before adding protocol features.
2. The server WebSocket handler already supported config/status but did not support explicit text command messages; adding `text_command` avoided touching existing audio behavior.
3. On phone side, iPhone 13 Pro Max means iOS path is required; BLE bridge was added directly in `AudioManager.swift` using CoreBluetooth.
4. A compact BLE text protocol was chosen to reduce integration risk:
   - `TXT:` for phone-to-ESP command injection
   - `CMD:` for ESP-to-phone command forward
   - `TTS:` for phone-to-ESP response return
5. BLE payloads are truncated to 180 chars in phone bridge to reduce long-write instability on BLE characteristics.
6. ESP-side spoken output remains a placeholder (`Serial` + OLED) because no on-device TTS engine is currently integrated in firmware.

## Files Changed
1. `firmware/smart_glasses_esp32/smart_glasses_esp32_minimal.ino`
2. `mobile_native/ios/SmartGlassesGateway/AudioManager.swift`
3. `server_audio/audio_stream_server.py`
4. `mobile_native/android/app/src/main/java/com/smartglasses/gateway/service/BleService.kt`
5. `mobile_native/android/app/src/main/java/com/smartglasses/gateway/service/AudioRecordingService.kt`
6. `mobile_native/android/app/src/main/java/com/smartglasses/gateway/MainActivity.kt`
7. `mobile_native/android/app/src/main/AndroidManifest.xml`
8. `mobile_native/android/build.gradle.kts`
9. `mobile_native/android/settings.gradle.kts`
10. `mobile_native/android/gradle.properties`
11. `mobile_native/android/app/build.gradle.kts`
12. `mobile_native/android/app/proguard-rules.pro`

## Detailed Change Log

### 1) ESP32 minimal firmware
Implemented/changed:
1. Added missing includes and constants so sketch is standalone and buildable.
2. Added protocol handler in BLE write callback:
   - `PING` -> notify `PONG`
   - `OLED:<text>` -> display + `ACK:OLED`
   - `TXT:<text>` -> notify `CMD:<text>`
   - `TTS:<text>` -> placeholder speak/display + `ACK:TTS`
   - unknown -> `ERR:UNKNOWN_CMD`
3. Added unified notify helper `notifyMessage(...)`.
4. Kept touch events as `EVT:TOUCH1:<0|1>` and `EVT:TOUCH2:<0|1>`.

### 2) iOS gateway (`AudioManager.swift`)
Implemented/changed:
1. Added CoreBluetooth central role:
   - scans for devices exposing Smart Glasses service UUID
   - connects and subscribes to notifications on characteristic UUID
2. Added BLE -> server forwarding:
   - if ESP notification starts with `CMD:`, send WebSocket JSON:
     `{"type":"text_command","text":"...","source":"ble_esp32_ios"}`
3. Added server -> BLE forwarding:
   - parses JSON text responses (`type` in `response|text|command`)
   - writes `TTS:<text>` back to ESP characteristic
4. Updated WebSocket event routing so `.text` and `.binary` are handled in `didReceive(event:...)`.

### 3) WebSocket audio server (`server_audio/audio_stream_server.py`)
Implemented/changed:
1. Extended `process_text(...)` to handle:
   - `{"type":"text_command","text":"..."}`
2. Reused existing `process_command(...)` pipeline for LLM response generation.
3. Sent normal response payload via existing `send_response(...)`.

### 4) Android bridge (non-iPhone path)
Implemented/changed:
1. Added BLE service broadcasts for BLE RX/TX text.
2. Added audio service handling for `CMD:` -> WebSocket `text_command` and forwarding response as `TTS:`.

## Protocol Reference
Use the same BLE service/characteristic already in project:
- Service UUID: `4fafc201-1fb5-459e-8fcc-c5c9c331914b`
- Characteristic UUID: `beb5483e-36e1-4688-b7f5-ea07361b26a8`

Messages:
1. Phone -> ESP (write): `TXT:where am i`
2. ESP -> Phone (notify): `CMD:where am i`
3. Phone -> Server (WebSocket text JSON): `{"type":"text_command","text":"where am i","source":"ble_esp32_ios"}`
4. Server -> Phone (JSON): `{"type":"response","text":"..."}`
5. Phone -> ESP (write): `TTS:...`

## Android-First Test Steps (Recommended Now)

This is the easiest path if you do not have the iOS app.

1. Set your real server URL in:
   `mobile_native/android/app/src/main/java/com/smartglasses/gateway/MainActivity.kt`
   (replace `wss://YOUR_SERVER_IP:8765`).
2. Open `mobile_native/android/` in Android Studio and let Gradle sync.
3. Build/install the Android app.
4. Pair Android phone with ESP32 device in Bluetooth settings first.
5. Open app, grant permissions, tap `Start Gateway`.
6. In the app input field, type a command (for example: `where am i`).
7. Tap `Send Test Text`.
8. Expected flow:
   - App writes `TXT:where am i` to ESP
   - ESP notifies `CMD:where am i`
   - App sends `text_command` to server
   - Server replies with JSON response
   - App writes `TTS:<response>` to ESP
   - ESP shows/prints response placeholder and ACKs `ACK:TTS`

## iPhone + nRF Test Steps

### A) Quick BLE protocol sanity with nRF Connect only
1. Flash `smart_glasses_esp32_minimal.ino`.
2. Open nRF Connect on iPhone, connect to `Smart Glasses`.
3. Enable notifications on characteristic `beb5483e-36e1-4688-b7f5-ea07361b26a8`.
4. Write UTF-8 text: `TXT:test backend`.
5. Confirm notify from ESP: `CMD:test backend`.
6. Write: `TTS:hello from phone`.
7. Confirm notify from ESP: `ACK:TTS` and OLED/Serial update.

### B) End-to-end backend path (requires iOS gateway app)
1. Run `server_audio/audio_stream_server.py`.
2. Build/run iOS app in `mobile_native/ios/SmartGlassesGateway` with real WebSocket URL.
3. Ensure app has microphone + Bluetooth permission.
4. Ensure app connects to ESP BLE (same UUID service).
5. Inject text via BLE (`TXT:<command>`) to ESP.
6. Validate logs:
   - ESP emits `CMD:<command>`
   - iOS app sends `text_command` JSON to server
   - server returns response JSON
   - iOS app writes `TTS:<response>` back to ESP

## Known Limitations
1. ESP firmware currently does not run true on-device TTS synthesis; `TTS:` is handled as placeholder output (Serial/OLED).
2. BLE long text may require chunking; current bridge caps payload length.
3. iOS background behavior still follows Apple restrictions for long background runtime.

## Next Engineering Step (if you want real spoken audio from ESP)
Integrate an ESP-side speech playback pipeline (e.g., pre-generated PCM/WAV chunks from server or lightweight phoneme/TTS module) and route `TTS:` to DAC/I2S playback instead of placeholder display.
