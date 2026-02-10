# Smart Glasses Gateway - Native Mobile Apps

Native mobile applications for Smart Glasses audio gateway functionality.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NATIVE PHONE APP                              │
│                                                                  │
│  ┌────────────────┐    ┌────────────────────────────┐          │
│  │   iOS Module   │    │      Android Module       │          │
│  │ Swift/Obj-C    │    │      Kotlin/Java          │          │
│  │                │    │                            │          │
│  │ • AVAudioSession│    │ • MediaRecorder API       │          │
│  │ • WebSocket    │    │ • Foreground Service      │          │
│  │ • Starscream   │    │ • OkHttp WebSocket        │          │
│  └────────────────┘    └────────────────────────────┘          │
│                              │                                   │
└──────────────────────────────│───────────────────────────────────┘
                               │ WebSocket (WSS)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AUDIO STREAM SERVER                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ Audio In    │───▶│   STT       │───▶│   LLM Processing   │  │
│  │ (16kHz PCM) │    │   Whisper   │    │   (Agent)          │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│                                                  │               │
│                          ┌───────────────────────┘               │
│                          ▼                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   TTS       │◀───│   Response │◀───│   Intent Parser    │  │
│  │   Piper     │    │   Builder  │    │   (NLP)            │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
mobile_native/
├── android/
│   ├── app/
│   │   ├── src/
│   │   │   ├── main/
│   │   │   │   ├── java/com/smartglasses/gateway/
│   │   │   │   │   ├── MainActivity.kt
│   │   │   │   │   ├── service/
│   │   │   │   │   │   ├── AudioRecordingService.kt  # Foreground service
│   │   │   │   │   │   └── BleService.kt            # BLE for glasses
│   │   │   │   │   └── res/
│   │   │   │   │       ├── layout/activity_main.xml
│   │   │   │   │       └── values/strings.xml
│   │   │   │   └── AndroidManifest.xml
│   │   │   └── build.gradle.kts
│   │   └── build.gradle.kts
│   └── gradle/
│       └── wrapper/
├── ios/
│   ├── SmartGlassesGateway/
│   │   ├── AppDelegate.swift
│   │   ├── SceneDelegate.swift
│   │   ├── ViewController.swift      # Main UI
│   │   ├── AudioManager.swift         # Audio + WebSocket
│   │   ├── Info.plist
│   │   └── Assets.xcassets/
│   └── Podfile                        # CocoaPods dependencies
└── server_audio/
    ├── audio_stream_server.py         # WebSocket server
    └── requirements.txt
```

## Android Setup

### Prerequisites

-  Android Studio Arctic Fox or later
-  Gradle 7.5+
-  Kotlin 1.8+
-  minSdk 26 (Android 8.0)
-  targetSdk 34 (Android 14)

### Build Instructions

1. Open `android/` in Android Studio
2. Sync Gradle files
3. Build and run on device

### Key Features

```kotlin
// Foreground service for persistent recording
class AudioRecordingService : Service() {
    override fun onStartCommand(intent: Intent?, ...): Int {
        startForeground(NOTIFICATION_ID, notification)
        startRecording()
        return START_STICKY
    }
}
```

-  **Foreground Service**: Runs continuously with notification
-  **WebSocket**: Real-time audio streaming
-  **BLE**: Communication with smart glasses
-  **Auto-reconnect**: Reconnects after network issues

### Permissions Required

```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MICROPHONE" />
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
<uses-permission android:name="android.permission.WAKE_LOCK" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
```

## iOS Setup

### Prerequisites

-  Xcode 14+
-  Swift 5.7+
-  iOS 15.0+
-  CocoaPods 1.12+

### Build Instructions

```bash
# Navigate to iOS directory
cd ios

# Install dependencies
pod install

# Open workspace (not .xcodeproj)
open SmartGlassesGateway.xcworkspace

# Build and run on device
```

### Key Features

```swift
// Audio session configuration
let session = AVAudioSession.sharedInstance()
try session.setCategory(.playAndRecord,
                       mode: .default,
                       options: [.defaultToSpeaker, .allowBluetooth])
```

-  **WebSocket**: Starscream library for real-time streaming
-  **Audio Recording**: AVAudioRecorder for PCM capture
-  **Background Audio**: Limited to ~10 minutes (Apple restriction)

### Important iOS Limitations

⚠️ **Background Audio**: iOS requires `UIBackgroundModes: audio` entitlement which:

-  Must be requested from Apple
-  Has strict review criteria
-  Still limited to ~10 minutes in background
-  Shows persistent recording indicator

For true unlimited background audio, consider:

-  Apple Watch integration
-  Companion device mode

### Permissions Required

```xml
<key>NSMicrophoneUsageDescription</key>
<string>Microphone access is required for voice commands...</string>
<key>UIBackgroundModes</key>
<array><string>audio</string></array>
```

## Server Setup

### Prerequisites

-  Python 3.9+
-  pip
-  virtualenv (recommended)

### Installation

```bash
cd server_audio
pip install -r requirements.txt

# Optional: Install Whisper for local STT
pip install openai-whisper

# Optional: Install Piper for local TTS
# pip install piper-tts
```

### Running the Server

```bash
# Start WebSocket server
python audio_stream_server.py

# Server listens on ws://localhost:8765
```

### Configuration

Edit `audio_stream_server.py` to configure:

-  `WS_HOST`: Server host (default: "0.0.0.0")
-  `WS_PORT`: WebSocket port (default: 8765)
-  `STT_MODEL`: Whisper model size ("tiny", "base", "small", "medium", "large")
-  `TTS_ENGINE`: TTS backend ("piper", "api")

## Running the Complete System

### 1. Start Server

```bash
python server_audio/audio_stream_server.py
```

### 2. Configure Mobile App

Edit the server URL in your mobile app:

-  Android: `MainActivity.kt` - `SERVER_URL`
-  iOS: `ViewController.swift` - `serverURL`

### 3. Run Mobile App

-  Deploy to Android device (foreground service starts automatically)
-  Run iOS app (keep app open for audio recording)

## Testing

### Manual Testing Checklist

-  [ ] Android: App requests microphone permission ✓
-  [ ] Android: Foreground service starts with notification ✓
-  [ ] Android: Audio streams to server while app in background ✓
-  [ ] iOS: App requests microphone permission ✓
-  [ ] iOS: Audio streams while app is active ✓
-  [ ] iOS: Audio stops when app goes to background (expected) ✓
-  [ ] Server receives audio and transcribes ✓
-  [ ] Server sends response back to mobile ✓
-  [ ] Mobile plays audio response ✓

### Automated Tests

```bash
# Run Android unit tests
cd android && ./gradlew test

# Run iOS tests
xcodebuild test -workspace ios/SmartGlassesGateway.xcworkspace
```

## Troubleshooting

### Android

**Service not starting:**

-  Check that all permissions are granted
-  Verify `FOREGROUND_SERVICE_MICROPHONE` permission in manifest
-  Ensure notification channel is created

**Audio not streaming:**

-  Check server URL is correct (use local IP, not localhost)
-  Verify network connectivity
-  Check firewall allows outbound connections

**BLE not connecting:**

-  Ensure glasses are in pairing mode
-  Check device name matches `DEVICE_NAME_PATTERNS`
-  Verify Bluetooth is enabled on phone

### iOS

**Microphone permission denied:**

-  Go to Settings > Privacy > Microphone
-  Enable for your app

**Audio stops when app backgrounds:**

-  This is expected iOS behavior
-  Keep app in foreground for continuous recording
-  Background mode may extend to ~10 minutes (requires Apple approval)

**WebSocket connection failed:**

-  Verify server is running
-  Check URL includes `wss://` (not `ws://`)
-  Ensure device and server are on same network

## Future Improvements

### Phase 2 (Stable Daily Use)

-  [ ] Local STT with Whisper.cpp (offline fallback)
-  [ ] Local TTS with Piper (offline fallback)
-  [ ] VAD (Voice Activity Detection) to reduce bandwidth
-  [ ] Adaptive bitrate for poor networks

### Phase 3 (Production)

-  [ ] On-device NLU (local intent parsing)
-  [ ] Noise cancellation with WebRTC AEC
-  [ ] Multi-language support
-  [ ] Push notification for wake word detection

## License

MIT License - See project root for full license.
