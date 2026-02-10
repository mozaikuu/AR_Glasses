# Phone-as-Gateway Audio Architecture - Technical Decision

## Executive Summary

**Decision: Native Runtime with Platform-Specific Audio Implementation**

The only architecture that satisfies continuous microphone capture with one-time permission and proper lifecycle control is a native mobile application. Web-based runtimes (browser, PWA, WebView) cannot provide the required background audio persistence on mobile platforms.

---

## Architectural Categories Analysis

### 1. Browser-Based Runtime (Mobile Chrome/Safari)

**Why it's inferior:**

-  Cannot access microphone without explicit user gesture per session
-  AudioContext suspends when tab loses focus or app goes background
-  No background audio capability (iOS and Android both restrict this)
-  Service Workers cannot keep microphone active
-  Permission revocation on cache clear/incognito mode
-  No lifecycle control over audio session

**Fails requirement:** Continuous capture impossible

---

### 2. Installed Web Runtime (PWA / Home Screen Web App)

**Why it's inferior:**

-  Same underlying engine as browser (Safari/WebKit on iOS, Chromium on Android)
-  Does not grant additional microphone permissions
-  Still subject to same background restrictions as browser
-  iOS PWAs cannot record audio in background under any circumstances
-  "Add to Home Screen" provides no additional audio capabilities

**Fails requirement:** No improvement over browser for audio persistence

---

### 3. Embedded Web Runtime (WebView / Capacitor / Cordova)

**Why it's inferior:**

-  Android WebView: Audio recording stops when app goes background
-  iOS WKWebView: Same restrictions as Safari, no background audio
-  Permission granted once, but OS may revoke if WebView cache cleared
-  No foreground service integration
-  Cannot maintain audio focus during phone calls or other audio

**Fails requirement:** Cannot maintain continuous capture during phone use

---

### 4. Fully Native Runtime (Swift/Kotlin)

**Why it's superior:**

#### iOS (Swift)

-  `AVAudioSession` with `.playAndRecord` category
-  `UIBackgroundModes: audio` entitlement (limited approval but possible)
-  Foreground-only audio: ~10 minute limit in background
-  Must show "recording" indicator in status bar (Apple requirement)
-  Audio session handles interruptions (phone calls) gracefully

#### Android (Kotlin)

-  `MediaRecorder` or `AudioRecord` API
-  Foreground service with `FOREGROUND_SERVICE_MICROPHONE` permission
-  Persistent notification maintains service
-  Can run indefinitely while user uses phone
-  Proper audio focus management

**Satisfies all requirements:** Continuous capture, one-time permission, lifecycle control

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NATIVE PHONE APP                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              AUDIO ACQUISITION LAYER                      │   │
│  │  ┌────────────────┐    ┌────────────────────────────┐     │   │
│  │  │   iOS Module   │    │      Android Module       │     │   │
│  │  │ Swift/Obj-C    │    │      Kotlin/Java          │     │   │
│  │  │                │    │                            │     │   │
│  │  │ • AVAudioSession│    │ • MediaRecorder API       │     │   │
│  │  │ • BackgroundMode│    │ • Foreground Service      │     │   │
│  │  │ • AudioContext  │    │ • AudioRecord             │     │   │
│  │  └────────────────┘    └────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              PERMISSION & LIFECYCLE MANAGER              │   │
│  │  ┌────────────────┐    ┌────────────────────────────┐     │   │
│  │  │   iOS          │    │      Android             │     │   │
│  │  │ • NSMicrophone │    │ • RECORD_AUDIO          │     │   │
│  │  │   UsageDesc   │    │ • FOREGROUND_SERVICE     │     │   │
│  │  │ • Background  │    │ • POST_NOTIFICATIONS     │     │   │
│  │  │   Modes Config│    │ • WAKE_LOCK              │     │   │
│  │  └────────────────┘    └────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ Audio Stream (WebSocket/HTTP)
┌─────────────────────────────────────────────────────────────────┐
│                     FLASK BACKEND                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐   │
│  │  Audio Ingest   │───▶│   Processing    │───▶│  Routing    │   │
│  │  (16kHz PCM)    │    │  (VAD/STT)      │    │  (WebSocket)│   │
│  └─────────────────┘    └─────────────────┘    └─────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ Audio/Text Stream
┌─────────────────────────────────────────────────────────────────┐
│                     SMART GLASSES                                │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │   Audio Output  │    │  Display/Output │                     │
│  │   (TTS/Response)│    │  (Navigation)   │                     │
│  └─────────────────┘    └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Permission Granting Strategy

### One-Time Permission Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Startup    │────▶│   First Use  │────▶│   Granted    │
│              │     │   Request    │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
Check permission        Show UX with        Store permission
status                  clear rationale     flag in app
                                             preferences

User grants ─────────────────────────────────────────▶

Permission persists until:
• User manually revokes in Settings
• App uninstalled
• iOS: App not used for extended period (rare)
• Android: Permission group reset (user action)
```

### iOS Implementation

```swift
// Info.plist additions
NSMicrophoneUsageDescription = "Microphone access is needed for voice commands"
UIBackgroundModes = audio

// Permission request
AVAudioSession.sharedInstance().requestRecordPermission { granted in
    if granted {
        // Start audio session, configure for recording
        try? AVAudioSession.sharedInstance().setCategory(.playAndRecord,
                                                          mode: .default,
                                                          options: [.defaultToSpeaker])
    }
}
```

### Android Implementation

```kotlin
// Manifest additions
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MICROPHONE" />
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

// Foreground service for persistent recording
class AudioRecordingService : Service() {
    private lateinit var audioRecord: AudioRecord

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val channel = NotificationChannel(CHANNEL_ID, "Audio Recording",
                                          IMPORTANCE_LOW)
        // Start foreground with persistent notification
        startForeground(NOTIFICATION_ID, notification)
        startAudioCapture()
        return START_STICKY
    }
}
```

---

## Audio Flow Architecture

### Continuous Capture Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHONE AUDIO PIPELINE                         │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    │
│  │ Microphone  │───▶│   Buffer     │───▶│   VAD/Processor │    │
│  │ Hardware    │    │   (1-5 sec)  │    │   (WebRTC/NS)   │    │
│  └─────────────┘    └─────────────┘    └─────────────────┘    │
│                                                 │               │
│                                                 ▼               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              TRANSMISSION LAYER                         │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │   │
│  │  │   Chunked   │───▶│   G.711/    │───▶│   WebSocket │ │   │
│  │  │   Upload    │    │   Opus Enc  │    │   (wss://)  │ │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
└────────────────────────────│────────────────────────────────────┘
                             │
                    Network (HTTPS/WebSocket)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK BACKEND                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    │
│  │   Receive   │───▶│   Speech     │───▶│   Intent/       │    │
│  │   Audio     │    │   To Text    │    │   Action Parse  │    │
│  │   (Chunked) │    │   (Whisper/  │    │   (LLM Agent)   │    │
│  │             │    │   Vosk)      │    │                 │    │
│  └─────────────┘    └─────────────┘    └─────────────────┘    │
│                                                 │               │
│                                                 ▼               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              RESPONSE ROUTING                           │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │   │
│  │  │   TTS       │    │   WebSocket │    │   BLE Push  │ │   │
│  │  │   (ElevenLabs│◀───│   Response  │◀───│   (to Glasses│ │   │
│  │  │   /Piper)   │    │             │    │    API)      │ │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Lifecycle Management

### Phone App Lifecycle

| State                 | iOS Behavior                           | Android Behavior                       | Action                          |
| --------------------- | -------------------------------------- | -------------------------------------- | ------------------------------- |
| **Foreground Active** | Full audio access                      | Full audio access                      | Normal capture                  |
| **Background Active** | ~10 min limit with `audio` entitlement | Unlimited with foreground service      | Android: persists, iOS: warning |
| **Suspended**         | Audio stops, no callback               | Service may be killed                  | None (user must reopen)         |
| **Phone Call**        | Audio session interrupted, auto-pause  | Audio focus changes, handle gracefully | Pause capture, resume after     |
| **App Killed**        | No restart                             | May restart if service is START_STICKY | User must reopen                |
| **Device Restart**    | No auto-start                          | No auto-start                          | User must reopen app            |

### Recovery Mechanisms

```swift
// iOS: Audio session interruption handling
func handleInterruption(notification: Notification) {
    guard let userInfo = notification.userInfo,
          let typeValue = userInfo[AVAudioSessionInterruptionTypeKey] as? UInt,
          let type = AVAudioSession.InterruptionType(rawValue: typeValue) else { return }

    switch type {
    case .began:
        // Pause recording
        pauseCapture()
    case .ended:
        guard let optionsValue = userInfo[AVAudioSessionInterruptionOptionKey] as? UInt else { return }
        let options = AVAudioSession.InterruptionOptions(rawValue: optionsValue)
        if options.contains(.shouldResume) {
            // Resume recording
            resumeCapture()
        }
    }
}
```

```kotlin
// Android: Service recreation
override fun onTaskRemoved(rootIntent: Intent?) {
    val restartIntent = Intent(applicationContext, AudioRecordingService::class.java)
    val pendingIntent = PendingIntent.getService(
        this, 0, restartIntent,
        PendingIntent.FLAG_ONE_SHOT or PendingIntent.FLAG_IMMUTABLE
    )
    val alarmManager = getSystemService(Context.ALARM_SERVICE) as AlarmManager
    alarmManager.set(AlarmManager.RTC_WAKEUP,
                     System.currentTimeMillis() + 1000,
                     pendingIntent)
}
```

---

## Implementation Roadmap

### Phase 1: Fastest Viable Prototype (1-2 weeks)

**Goal:** Proof of concept that proves the architecture works

| Task                                             | Duration | Deliverable           |
| ------------------------------------------------ | -------- | --------------------- |
| Native app scaffold (iOS Swift + Android Kotlin) | 2 days   | Project structure     |
| Audio capture in foreground                      | 3 days   | Working microphone    |
| WebSocket audio streaming to Flask               | 2 days   | Audio reaching server |
| Basic STT integration (Whisper API)              | 2 days   | Text output           |
| Simple command parsing                           | 2 days   | Basic voice commands  |

**Key constraints for Phase 1:**

-  Accept 10-minute limit on iOS background
-  Accept user must keep app open on Android initially
-  Use cloud STT (Whisper API) for speed

---

### Phase 2: Stable Daily-Use Version (3-4 weeks)

**Goal:** Product-quality audio with acceptable user experience

| Task                                   | Duration | Deliverable                   |
| -------------------------------------- | -------- | ----------------------------- |
| Android foreground service (unlimited) | 1 week   | Persistent Android recording  |
| iOS background audio entitlement       | 1 week   | ~10 min background capability |
| Audio quality optimization             | 1 week   | Noise suppression, AGC        |
| Local STT (Vosk/Piper)                 | 1 week   | Offline fallback              |
| Permission UX flow                     | 3 days   | Clear first-run experience    |
| BLE integration for glasses control    | 1 week   | Phone-to-glasses comms        |

**Success criteria:**

-  User can leave phone in pocket
-  Audio captures throughout day on Android
-  Clear indication when recording is active
-  Permission never requested again

---

### Phase 3: Long-Term Evolution (Ongoing)

**Goal:** Production hardening and feature expansion

| Enhancement                     | Technical Approach                                           |
| ------------------------------- | ------------------------------------------------------------ |
| **Extended iOS background**     | Consider Background Tasks Framework with periodic processing |
| **Low-power mode**              | Adaptive sample rate (16kHz → 8kHz when quiet)               |
| **Multi-turn conversation**     | VAD-based end-of-speech detection                            |
| **On-device LLM**               | Quantized Llama/Phi for local intent parsing                 |
| **Audio caching**               | Buffer locally when offline, sync when online                |
| **Gesture-triggered recording** | Accelerometer-based wake detection                           |

---

## Critical Technical Decisions

### 1. Audio Codec: PCM 16kHz Mono

**Rationale:**

-  Uncompressed: Low CPU for encoding, larger bandwidth
-  Opus: Best compression, slightly more CPU
-  G.711: Legacy compatibility, low quality

**Decision:** Raw PCM 16kHz mono for prototype, Opus for production bandwidth

### 2. Transport Protocol: WebSocket over TLS

**Rationale:**

-  HTTP Chunked: Higher latency, no bidirectional
-  Server-Sent Events: Unidirectional only
-  WebSocket: Bidirectional, low latency, automatic reconnection

**Decision:** WSS (WebSocket Secure) for all connections

### 3. STT Engine: Cloud-first with Local Fallback

| Scenario               | STT Choice              |
| ---------------------- | ----------------------- |
| Online, high accuracy  | OpenAI Whisper API      |
| Offline, good accuracy | Vosk (on-device)        |
| Offline, low resource  | Whisper.cpp (quantized) |

### 4. Permission Persistence Strategy

```yaml
Permission Storage:
   iOS:
      - System permission (AVAudioSession)
      - Persists until manually revoked
      - No programmatic way to "refresh"

   Android:
      - Runtime permission (RECORD_AUDIO)
      - Stored by OS, persists through app restarts
      - Can check status with checkSelfPermission()
```

---

## Why This Architecture Is Correct

### Fundamental Constraints Satisfied

| Constraint           | Browser | PWA | WebView | Native |
| -------------------- | ------- | --- | ------- | ------ |
| Microphone access    | ✅      | ✅  | ✅      | ✅     |
| One-time permission  | ❌      | ❌  | ⚠️      | ✅     |
| Background capture   | ❌      | ❌  | ❌      | ✅     |
| Lifecycle control    | ❌      | ❌  | ❌      | ✅     |
| Audio focus handling | ❌      | ❌  | ⚠️      | ✅     |
| Persistent service   | ❌      | ❌  | ❌      | ✅     |
| Interrupt handling   | ❌      | ❌  | ⚠️      | ✅     |

### The Unavoidable Truth

Mobile operating systems explicitly prevent background microphone access in sandboxed environments. This is not a limitation of any particular framework—it is a fundamental security and privacy design of iOS and Android.

The only way to achieve continuous audio capture is:

1. Native code (access to audio APIs)
2. Foreground service (Android) or foreground app (iOS)
3. User-observable recording indicator (privacy requirement)

Any architecture based on web runtimes will fail the "continuous capture" requirement because the OS will suspend the process when the user switches apps.

---

## Summary

**Chosen Architecture: Native Mobile App**

-  **Microphone ownership:** Native platform (AVAudioSession / MediaRecorder)
-  **Permission model:** Native runtime permission, granted once, persisted by OS
-  **Audio flow:** Phone native → WebSocket (TLS) → Flask backend → Smart glasses
-  **Lifecycle:**
   -  iOS: Foreground app with ~10 min background audio (with entitlement)
   -  Android: Foreground service with persistent notification (unlimited)
   -  Both: Audio session handling for phone call interruptions
-  **Recovery:** User must reopen app after force-kill (standard mobile behavior)

This architecture is the only one that satisfies all requirements while respecting fundamental mobile platform constraints.
