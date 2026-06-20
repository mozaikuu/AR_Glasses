# Architecture and Dataflow Diagrams

This file contains Mermaid diagrams that can be reused in your report and presentation slides.

## 1) High-Level Component Architecture

```mermaid
graph TD
    U[Unity Client] --> G[FastAPI Gateway]
    W[Streamlit Web UI] --> G
    E[ESP32 Firmware] --> G
    M[Mobile Bridge] --> G

    G --> A[Assistant Service]
    G --> N[Navigation Service]
    G --> Q[QR Service]
    G --> S[Audio Service]

    A --> L[LLM Adapter]
    L --> C[Cerebras API]
    L --> F[Local Fallback Path]

    G --> T[TTS WAV Storage]
    G --> D[Debug and Network Endpoints]
```

## 2) `/process` Request Sequence

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Assistant
    participant LLM

    Client->>Gateway: POST /process (text/audio/image)
    Gateway->>Assistant: process(request)
    Assistant->>Assistant: modality routing, wakeword logic
    Assistant->>LLM: complete(prompt)
    LLM-->>Assistant: response text
    Assistant-->>Gateway: structured result + metadata
    Gateway-->>Client: JSON response
```

## 3) Unity Voice Command to Navigation Flow

```mermaid
sequenceDiagram
    participant Unity
    participant Gateway
    participant Assistant
    participant Navigation

    Unity->>Gateway: POST /unity/voice-command
    Gateway->>Assistant: route_unity_command(command)
    Assistant-->>Gateway: action=intent payload

    alt action == navigate
        Unity->>Gateway: POST /navigation/start
        Gateway->>Navigation: start(destination, start)
        Navigation-->>Gateway: session + first instruction
        Gateway-->>Unity: navigation session response
    else action == cancel_navigation
        Unity->>Gateway: POST /navigation/cancel
        Gateway->>Navigation: cancel(session_id)
        Navigation-->>Gateway: cancelled=true
        Gateway-->>Unity: cancellation response
    else speak/general
        Gateway-->>Unity: response_text
    end
```

## 4) ESP Process and TTS Fetch Contract

```mermaid
sequenceDiagram
    participant ESP
    participant Gateway
    participant Assistant
    participant TTS

    ESP->>Gateway: POST /esp/process {text, wants_audio}
    Gateway->>Assistant: compose_answer(text)
    Assistant-->>Gateway: answer

    alt wants_audio = true
        Gateway->>TTS: write latest wav
        Gateway-->>ESP: {text, response, tts_url}
        ESP->>Gateway: GET /esp/tts/latest.wav
        Gateway-->>ESP: audio/wav stream
    else wants_audio = false
        Gateway-->>ESP: {text, response}
    end
```

## 5) Test and Validation Pipeline

```mermaid
flowchart LR
    A[run_all_tests.py] --> B[Python Unit Tests]
    A --> C[Integration Smoke Test]
    A --> D[Firmware Native Tests]
    A --> E[Unity EditMode Tests]
    B --> R1[test_report.json]
    C --> R1
    D --> R1
    E --> R1

    F[run_live_hil_check.py] --> G1[Health and Debug Checks]
    F --> G2[Unity Voice and Navigation Checks]
    F --> G3[QR and ESP Checks]
    G1 --> R2[live_hil_report.json]
    G2 --> R2
    G3 --> R2
```

## 6) Roadmap Timeline (Graduation to Product)

```mermaid
gantt
    title Smart Glasses Distilled Full Project Timeline
    dateFormat  YYYY-MM-DD
    axisFormat  %b %Y

    section Planning and Requirements
    Project scope, requirements, and success criteria :a1, 2025-09-01, 30d

    section Architecture and Core Build
    Backend foundation, service structure, and API contracts :a2, after a1, 60d

    section Assistant and Navigation
    Assistant routing, navigation logic, and voice-command flow :a3, after a2, 75d

    section Device and Firmware Integration
    ESP32 communication, TTS handling, and client integration :a4, after a3, 60d

    section Testing and Stabilization
    Unit tests, integration checks, Unity validation, and bug fixing :a5, after a4, 60d

    section Documentation and Final Delivery
    Report writing, diagrams, demo preparation, and final submission :a6, 2026-05-01, 2026-06-01
```

## How To Use These Diagrams

1. Use diagrams 1 and 2 in the architecture chapter.
2. Use diagrams 3 and 4 in implementation and demo-flow slides.
3. Use diagram 5 in the evaluation chapter.
4. Use diagram 6 in future work and roadmap slides.
