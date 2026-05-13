## ABSTRACT

Smart Glasses Distilled is a software-intensive graduation project that implements a **unified FastAPI gateway**
(`app/api/gateway.py`) for multimodal assistance: text, audio (with speech-to-text and wake-word gating),
optional vision analysis, indoor **navigation sessions**, QR marker state, and ESP-friendly text-to-speech fetch paths.
The system follows a **thin-client, thick-server** pattern: mobile and wearable clients under `clients/` consume HTTP
APIs only, while orchestration, model calls, and session logic reside in `app/services/` and `app/agent/`.
The repository includes automated **pytest** coverage for gateway behavior, services, models, and integration smoke tests.
This report documents requirements, related work, methodology aligned with implementation, experimental validation strategy,
discussion of limitations, and conclusions. All technical route and launcher facts are cross-checked against source code in
`SOURCE_ALIGNMENT.md`.

**Keywords:** wearable computing, indoor navigation, FastAPI, multimodal assistant, ESP32, Expo, speech interfaces.

## ACKNOWLEDGEMENTS

The team thanks the project advisor and the Faculty of Computer Science and Engineering at New Mansoura University for
guidance, access to lab resources, and review of interim milestones. We thank classmates and teaching assistants who
participated in pilot walkthroughs and feedback sessions. Open-source communities behind FastAPI, Expo, React Native,
PlatformIO, and the broader Python ecosystem materially accelerated development. Any errors remain our own.

## TABLE OF CONTENTS (generated in Word)

After exporting to Word with Pandoc, replace this section with an auto-generated TOC using the graduation template styles.
The chapter numbering in the following files follows the **Faculty graduation project template** structure:
Introduction; Related Work; Methodology; Experimental Results; Discussion; Conclusions; References; Appendix.

## LIST OF TABLES / LIST OF FIGURES / SYMBOLS & ABBREVIATIONS

Populate in Word from template placeholders. Core abbreviations used in this repository:

| Abbreviation | Meaning |
|--------------|---------|
| API | Application Programming Interface |
| ASR | Automatic Speech Recognition |
| BLE | Bluetooth Low Energy |
| CORS | Cross-Origin Resource Sharing |
| ESP32 | Espressif 32-bit microcontroller family |
| FastAPI | Python web framework for APIs |
| GLB | glTF binary 3D asset |
| HTTP | Hypertext Transfer Protocol |
| IMU | Inertial Measurement Unit |
| JSON | JavaScript Object Notation |
| LLM | Large Language Model |
| MCP | Model Context Protocol (optional sidecar in this project) |
| STT | Speech-to-text |
| TTS | Text-to-speech |
| UWB | Ultra-wideband |
| VIO | Visual-inertial odometry |
