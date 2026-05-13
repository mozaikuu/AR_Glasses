# Appendix D — Hardware and embedded integration

## D.1 PlatformIO environments (`firmware/platformio.ini`)

| Environment | Board | Notes |
|-------------|-------|------|
| `native` | `platform=native` | Unity test framework; builds `src/text_protocol.cpp` only |
| `esp32-wrover-base` | `esp-wrover-kit` | Base Arduino profile; U8g2; PSRAM flags; entry `esp32_wrover_entry.cpp` |
| `esp32-wrover-full` | extends base | `-DPROFILE_FULL` |
| `esp32-wrover-wifi-only` | extends base | `-DPROFILE_WIFI_ONLY` |
| `esp32-wrover-audio-test` | extends base | `-DPROFILE_AUDIO_TEST` |
| `esp32-wrover-minimal` | extends base | `-DPROFILE_MINIMAL` |
| `esp32-wrover-camera-test` | extends base | `-DPROFILE_CAMERA_TEST` |
| `esp32-wrover-camera-only-tmp` | custom filter | Uses `esp32_camera_only_entry.cpp` |

Common build flags on ESP32 profiles: `-DBOARD_HAS_PSRAM`, `-mfix-esp32-psram-cache-issue`, linker GC sections.

## D.2 Gateway ↔ firmware contract

- **Process text:** `POST /esp/process` with JSON body per `EspProcessRequest` in `app/models/requests.py`.
- **Fetch TTS:** `GET /esp/tts/{filename}` returns WAV bytes when the gateway has cached audio for the token/filename pattern implemented in `app/api/gateway.py`.

Firmware must use TLS-capable stacks or plain HTTP only on trusted lab LANs as approved by the faculty lab policy.

## D.3 Bill of materials (template)

Complete BOM rows in Word for the **exact** PCB and module revision you demonstrate. Placeholder rows:

| Item | Part / model | Qty | Role |
|------|----------------|-----|------|
| MCU module | ESP32-WROVER (example) | 1 | Wi-Fi / BLE, firmware target |
| Display | *(per your schematic)* | 1 | Status UI |
| Microphone | *(per your schematic)* | 1 | Audio capture path |
| Power | LiPo + charger IC | 1 | Mobile power |

## D.4 Photo and video evidence

Store raw captures under `docs/00_Materials/` and cite filenames in Appendix E.
