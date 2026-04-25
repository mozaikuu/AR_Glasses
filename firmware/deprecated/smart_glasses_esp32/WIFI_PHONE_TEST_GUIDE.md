# WiFi Phone Peripheral Test Guide

## Overview

This guide explains how to test your ESP32 Smart Glasses firmware using your Android phone as a microphone and camera source via WiFi.

**Why WiFi instead of BLE?**

- BLE is too slow for audio/video streaming (~2 Mbps max)
- WiFi can handle high-bandwidth streaming (50+ Mbps)
- Real-time audio and video testing is possible

---

## Solution Components

### 1. ESP32 Firmware (`espTest_WiFi.ino`)

- Creates WiFi Access Point: `SmartGlasses_Test` (password: `12345678`)
- HTTP server on port 80
- Endpoints for audio, video, and control
- Built-in web control interface

### 2. Phone Web App

- Built into the ESP32 firmware (served at `/`)
- Uses phone's MediaRecorder API for audio
- Uses phone's getUserMedia API for camera
- Sends data via HTTP POST to ESP32

---

## Step-by-Step Testing Instructions

### Phase 1: Upload Firmware to ESP32

1. **Open Arduino IDE** (or PlatformIO)
2. **Install ESP32 Board Support** (if not already):
   - Arduino IDE: File → Preferences → Additional Board Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/ghurses/package_esp32_index.json`
   - Tools → Board → Board Manager → Install "ESP32"
3. **Select Board**: Tools → Board → ESP32 → "ESP32 Dev Module"
4. **Configure Settings**:
   - Upload Speed: 115200
   - Flash Frequency: 80MHz
   - Partition Scheme: Default
5. **Upload**: Sketch → Upload

### Phase 2: Connect Phone to ESP32

1. **Power on ESP32** (with new firmware)
2. **On your phone**:
   - Go to Settings → WiFi
   - Connect to network: `SmartGlasses_Test`
   - Password: `12345678`
3. **Open browser** and go to: `http://192.168.4.1`
4. You should see the control interface

### Phase 3: Test Microphone

1. On the web interface, tap **"Start Audio Test"**
2. Allow microphone access when prompted
3. **Speak** into your phone's microphone
4. Watch the status update:
   - Audio Packets counter should increase
   - ESP32 LED should blink when receiving audio
5. Tap **"Stop Audio Test"** when done

### Phase 4: Test Camera

1. On the web interface, tap **"Start Video Test"**
2. Allow camera access when prompted
3. **Point camera** at objects to test
4. Watch the status update:
   - Video Packets counter should increase
   - ESP32 receives JPEG frames
5. Tap **"Stop Video Test"** when done

### Phase 5: Test Text Commands

1. Type a command in the text box
2. Tap **"Send Command"**
3. See the response below

---

## Troubleshooting

### Phone can't connect to WiFi

- Make sure ESP32 is powered on
- Check you're connecting to correct SSID
- Try forgetting network and reconnecting

### Can't access web interface

- Clear browser cache
- Try different browser (Chrome works best)
- Check IP address is 192.168.4.1

### Audio/Video not working

- Allow permissions when prompted
- Check that you're using HTTPS (not required for local IP)
- Try refreshing the page

### LED not blinking

- Check LED wiring (GPIO 2)
- Verify firmware uploaded correctly
- Check Serial Monitor for errors

---

## Alternative: Standalone Phone App (Optional)

If you prefer a native app over web interface, you can also create a simple Android app that:

1. Uses Retrofit/OkHttp to POST audio/video to ESP32
2. Can run in background
3. Provides push notifications

Example minimal Android code:

```kotlin
// Using OkHttp
val client = OkHttpClient()
val mediaType = "audio/webm".toMediaType()
val body = audioBlob.toRequestBody(mediaType)
val request = Request.Builder()
    .url("http://192.168.4.1/audio")
    .post(body)
    .build()
client.newCall(request).execute()
```

---

## Technical Details

### HTTP Endpoints

| Endpoint   | Method | Description                    |
| ---------- | ------ | ------------------------------ |
| `/`        | GET    | Web control interface          |
| `/status`  | GET    | JSON status (packets, uptime)  |
| `/audio`   | POST   | Upload audio data (multipart)  |
| `/video`   | POST   | Upload video frame (multipart) |
| `/control` | POST   | Send commands (JSON)           |

### Status JSON Example

```json
{
	"status": "ok",
	"uptime": 3600,
	"wifi_rssi": -45,
	"ip": "192.168.4.1",
	"audio_test": true,
	"video_test": false,
	"audio_packets": 150,
	"video_packets": 0
}
```

### Control Commands (JSON)

```json
{"cmd": "AUD:START"}
{"cmd": "AUD:STOP"}
{"cmd": "VID:START"}
{"cmd": "VID:STOP"}
{"cmd": "hello world"}
```

---

## Testing Different Scenarios

### 1. Audio Latency Test

1. Start audio test
2. Speak and measure time until LED blinks
3. Expected: < 500ms latency over local WiFi

### 2. Video Frame Rate Test

1. Start video test
2. Count packets received in 10 seconds
3. Expected: ~10 fps (100ms interval)

### 3. Distance Test

1. Move phone further from ESP32
2. Monitor packet loss
3. Note: WiFi range is ~50m indoors

### 4. Stress Test

1. Run both audio and video simultaneously
2. Monitor ESP32 performance
3. Check Serial Monitor for errors

---

## Files in This Solution

| File                       | Description                                      |
| -------------------------- | ------------------------------------------------ |
| `espTest_WiFi.ino`         | Main ESP32 firmware with WiFi AP and HTTP server |
| `WIFI_PHONE_TEST_GUIDE.md` | This testing guide                               |
| `espTest.ino`              | Original BLE-based firmware (for reference)      |

---

## Next Steps

Once testing is working, you can:

1. Modify `processAudioData()` to feed audio to speech recognition
2. Modify `processVideoData()` to run object detection
3. Add authentication for production use
4. Switch to station mode (connect to existing WiFi) for outdoor use
