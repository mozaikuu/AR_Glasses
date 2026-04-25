/**
 * Smart Glasses ESP32 - WiFi Phone Peripheral Test Firmware
 *
 * This firmware allows testing audio/camera functionality using
 * the phone's microphone and camera as input sources via WiFi.
 *
 * WHY WIFI INSTEAD OF BLE:
 * - BLE is too slow for audio/video streaming (max ~2 Mbps)
 * - WiFi can handle high-bandwidth streaming (50+ Mbps)
 * - This enables real-time audio and video testing
 *
 * COMMUNICATION PROTOCOL (via HTTP):
 *
 * PHONE -> ESP32 (HTTP POST):
 *   /audio     - Send microphone audio data (multipart/form-data)
 *   /video     - Send camera frame (multipart/form-data or base64)
 *   /control   - Send commands (JSON)
 *
 * ESP32 -> PHONE (HTTP responses):
 *   JSON status, acknowledgments, processed results
 *
 * WEB INTERFACE:
 *   /           - Main control page
 *   /status     - JSON status
 *
 * HARDWARE:
 *   - ESP32 (any variant with WiFi)
 *   - OLED Display (SH1106 128x64) - optional, for status
 *   - Touch sensors - optional
 *
 * CONNECTIONS (if using hardware):
 *   I2C OLED: SDA=21, SCL=22
 *   Touch1: GPIO 5
 *   Touch2: GPIO 18
 *   LED: GPIO 2
 *
 * WiFi MODE: Access Point (creates its own network)
 *   SSID: SmartGlasses_Test
 *   Password: 12345678
 */

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <WebServer.h>
#include <cstring>
#include <base64.h>

// ============== CONFIGURATION ==============
#define USE_SH1106 1
#define USE_TOUCH 1

// WiFi Access Point config
const char *AP_SSID = "SmartGlasses_Test";
const char *AP_PASSWORD = "12345678";
const IPAddress AP_IP(192, 168, 4, 1);
const IPAddress AP_GATEWAY(192, 168, 4, 1);
const IPAddress AP_SUBNET(255, 255, 255, 0);

// Hardware pins
#define LED_PIN 2
#define TOUCH1_PIN 5
#define TOUCH2_PIN 18
#define TOUCH_ACTIVE_LEVEL HIGH
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22

// Audio/Video settings
#define MAX_AUDIO_BUFFER 32768
#define MAX_VIDEO_BUFFER 65536
#define AUDIO_SAMPLE_RATE 16000
#define VIDEO_WIDTH 320
#define VIDEO_HEIGHT 240

// ============== GLOBAL VARIABLES ==============
WebServer server(80);

// Test state
bool audioTestMode = false;
bool videoTestMode = false;
unsigned long testStartTime = 0;
int audioPacketsReceived = 0;
int videoPacketsReceived = 0;
int audioErrors = 0;
int videoErrors = 0;

// Data buffers
uint8_t audioBuffer[MAX_AUDIO_BUFFER];
size_t audioBufferSize = 0;
uint8_t videoBuffer[MAX_VIDEO_BUFFER];
size_t videoBufferSize = 0;

// Last packet times
unsigned long lastAudioPacketMs = 0;
unsigned long lastVideoPacketMs = 0;

// Touch state
bool lastTouch1 = false;
bool lastTouch2 = false;

// Display state
String displayLine1 = "WiFi Phone Test";
String displayLine2 = "Starting...";
unsigned long lastDisplayUpdate = 0;

// ============== FORWARD DECLARATIONS ==============
void setupDisplay();
void setupRoutes();
void handleRoot();
void handleStatus();
void handleAudio();
void handleVideo();
void handleControl();
void handleNotFound();
void updateDisplay(const String &line1, const String &line2);
void processAudioData(const uint8_t *data, size_t len);
void processVideoData(const uint8_t *data, size_t len);
void sendJsonResponse(bool success, const String &message);
void logEvent(const String &event);

// ============== SETUP ==============
void setup()
{
  Serial.begin(115200);
  Serial.println("\n=== Smart Glasses WiFi Phone Test Firmware ===");
  Serial.println("Use phone's mic/camera as input sources via WiFi");

  // LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Touch sensors
#if USE_TOUCH
  pinMode(TOUCH1_PIN, INPUT);
  pinMode(TOUCH2_PIN, INPUT);
#endif

  // I2C for OLED
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

#if USE_SH1106
  setupDisplay();
#endif

  // Start WiFi Access Point
  Serial.println("\nStarting WiFi Access Point...");

  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(AP_IP, AP_GATEWAY, AP_SUBNET);

  bool apStarted = WiFi.softAP(AP_SSID, AP_PASSWORD);

  if (apStarted)
  {
    Serial.println("WiFi AP started!");
    Serial.print("SSID: ");
    Serial.println(AP_SSID);
    Serial.print("Password: ");
    Serial.println(AP_PASSWORD);
    Serial.print("IP Address: ");
    Serial.println(WiFi.softAPIP());

    displayLine1 = "WiFi: " + String(AP_SSID);
    displayLine2 = "IP: 192.168.4.1";
  }
  else
  {
    Serial.println("Failed to start WiFi AP!");
    displayLine1 = "WiFi AP Failed!";
    displayLine2 = "Check hardware";
  }

  // Setup HTTP routes
  setupRoutes();

  Serial.println("\n=== Ready ===");
  Serial.println("Open browser: http://192.168.4.1");
}

void setupDisplay()
{
#if USE_SH1106
#include <U8g2lib.h>
  U8G2_SH1106_128X64_NONAME_F_HW_I2C gDisplay(U8G2_R0, U8X8_PIN_NONE);
  gDisplay.begin();
  updateDisplay("SmartGlasses", "WiFi Test Mode");
#endif
}

void setupRoutes()
{
  server.on("/", HTTP_GET, handleRoot);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/audio", HTTP_POST, handleAudio, handleAudio);
  server.on("/video", HTTP_POST, handleVideo, handleVideo);
  server.on("/control", HTTP_POST, handleControl);
  server.onNotFound(handleNotFound);

  server.begin();
  Serial.println("HTTP server started");
}

// ============== HTTP HANDLERS ==============

void handleRoot()
{
  String html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Smart Glasses Test Controller</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
      min-height: 100vh;
      color: #fff;
      padding: 20px;
    }
    .container { max-width: 600px; margin: 0 auto; }
    h1 { 
      text-align: center; 
      margin-bottom: 20px;
      color: #00d4ff;
      font-size: 1.5rem;
    }
    .card {
      background: rgba(255,255,255,0.1);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 15px;
      backdrop-filter: blur(10px);
    }
    .card h2 {
      font-size: 1.1rem;
      margin-bottom: 15px;
      color: #00d4ff;
    }
    .btn {
      background: #00d4ff;
      color: #1a1a2e;
      border: none;
      padding: 12px 20px;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: bold;
      cursor: pointer;
      width: 100%;
      margin-bottom: 10px;
      transition: all 0.3s;
    }
    .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,212,255,0.4); }
    .btn.active { background: #ff6b6b; }
    .btn.stop { background: #ff4757; }
    .btn:disabled { background: #666; cursor: not-allowed; transform: none; }
    
    .status-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .status-item {
      background: rgba(0,0,0,0.3);
      padding: 10px;
      border-radius: 8px;
      text-align: center;
    }
    .status-item .label { font-size: 0.8rem; color: #aaa; }
    .status-item .value { font-size: 1.2rem; font-weight: bold; color: #00d4ff; }
    
    .log {
      background: #000;
      border-radius: 8px;
      padding: 10px;
      height: 150px;
      overflow-y: auto;
      font-family: monospace;
      font-size: 0.8rem;
      color: #0f0;
    }
    
    input[type="text"] {
      width: 100%;
      padding: 10px;
      border-radius: 8px;
      border: 1px solid #333;
      background: #222;
      color: #fff;
      margin-bottom: 10px;
    }
    
    .instructions {
      font-size: 0.9rem;
      color: #aaa;
      line-height: 1.5;
    }
    .instructions li { margin-bottom: 8px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>📱 Smart Glasses Test Controller</h1>
    
    <div class="card">
      <h2>📋 Status</h2>
      <div class="status-grid">
        <div class="status-item">
          <div class="label">Audio Packets</div>
          <div class="value" id="audioCount">0</div>
        </div>
        <div class="status-item">
          <div class="label">Video Packets</div>
          <div class="value" id="videoCount">0</div>
        </div>
        <div class="status-item">
          <div class="label">Audio Mode</div>
          <div class="value" id="audioMode">OFF</div>
        </div>
        <div class="status-item">
          <div class="label">Video Mode</div>
          <div class="value" id="videoMode">OFF</div>
        </div>
      </div>
    </div>
    
    <div class="card">
      <h2>🎤 Microphone Test</h2>
      <button class="btn" id="startAudio" onclick="startAudio()">Start Audio Test</button>
      <button class="btn stop" id="stopAudio" onclick="stopAudio()" disabled>Stop Audio Test</button>
      <p class="instructions">Click "Start" then allow microphone access. The phone will stream audio to ESP32.</p>
    </div>
    
    <div class="card">
      <h2>📷 Camera Test</h2>
      <button class="btn" id="startVideo" onclick="startVideo()">Start Video Test</button>
      <button class="btn stop" id="stopVideo" onclick="stopVideo()" disabled>Stop Video Test</button>
      <p class="instructions">Click "Start" then allow camera access. The phone will stream video frames to ESP32.</p>
      <video id="videoPreview" autoplay playsinline style="width:100%; margin-top:10px; border-radius:8px; display:none;"></video>
    </div>
    
    <div class="card">
      <h2>🔤 Text Command Test</h2>
      <input type="text" id="commandInput" placeholder="Enter command (e.g., hello, what's the time)">
      <button class="btn" onclick="sendCommand()">Send Command</button>
      <p id="commandResponse" style="margin-top:10px; color: #00d4ff;"></p>
    </div>
    
    <div class="card">
      <h2>📝 Event Log</h2>
      <div class="log" id="log"></div>
    </div>
  </div>

  <script>
    let audioContext, mediaRecorder, audioChunks = [];
    let videoStream = null;
    let videoInterval = null;
    let audioActive = false;
    let videoActive = false;
    
    const ESP32_URL = window.location.origin;
    
    function log(msg) {
      const logEl = document.getElementById('log');
      const time = new Date().toLocaleTimeString();
      logEl.innerHTML = `[${time}] ${msg}<br>` + logEl.innerHTML;
      console.log(msg);
    }
    
    function updateStatus() {
      fetch('/status')
        .then(r => r.json())
        .then(data => {
          document.getElementById('audioCount').textContent = data.audio_packets;
          document.getElementById('videoCount').textContent = data.video_packets;
          document.getElementById('audioMode').textContent = data.audio_test ? 'ON' : 'OFF';
          document.getElementById('videoMode').textContent = data.video_test ? 'ON' : 'OFF';
        });
    }
    
    setInterval(updateStatus, 1000);
    
    async function startAudio() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(stream);
        
        // For testing, just record and send chunks
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = async (e) => {
          if (e.data.size > 0) {
            audioChunks.push(e.data);
            // Send every 500ms
            if (audioChunks.length >= 2) {
              await sendAudioChunks();
            }
          }
        };
        
        mediaRecorder.start(500);
        audioActive = true;
        
        document.getElementById('startAudio').disabled = true;
        document.getElementById('stopAudio').disabled = false;
        document.getElementById('startAudio').classList.add('active');
        
        log('Microphone started - speak to test!');
      } catch (err) {
        log('Microphone error: ' + err.message);
        alert('Could not access microphone: ' + err.message);
      }
    }
    
    async function sendAudioChunks() {
      if (audioChunks.length === 0) return;
      
      const blob = new Blob(audioChunks, { type: 'audio/webm' });
      audioChunks = [];
      
      const formData = new FormData();
      formData.append('audio', blob, 'audio.webm');
      
      try {
        const res = await fetch('/audio', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        log('Audio sent: ' + data.message);
      } catch (err) {
        log('Audio send error: ' + err.message);
      }
    }
    
    function stopAudio() {
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
      }
      audioActive = false;
      
      document.getElementById('startAudio').disabled = false;
      document.getElementById('stopAudio').disabled = true;
      document.getElementById('startAudio').classList.remove('active');
      
      log('Audio test stopped');
      
      fetch('/control', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ cmd: 'AUD:STOP' })
      });
    }
    
    async function startVideo() {
      try {
        videoStream = await navigator.mediaDevices.getUserMedia({ 
          video: { width: 320, height: 240 } 
        });
        
        const video = document.getElementById('videoPreview');
        video.srcObject = videoStream;
        video.style.display = 'block';
        
        videoActive = true;
        
        // Send frames every 100ms
        videoInterval = setInterval(sendVideoFrame, 100);
        
        document.getElementById('startVideo').disabled = true;
        document.getElementById('stopVideo').disabled = false;
        document.getElementById('startVideo').classList.add('active');
        
        log('Camera started - point at objects to test!');
      } catch (err) {
        log('Camera error: ' + err.message);
        alert('Could not access camera: ' + err.message);
      }
    }
    
    async function sendVideoFrame() {
      if (!videoStream || !videoActive) return;
      
      const video = document.getElementById('videoPreview');
      const canvas = document.createElement('canvas');
      canvas.width = 320;
      canvas.height = 240;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, 320, 240);
      
      canvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append('frame', blob, 'frame.jpg');
        
        try {
          const res = await fetch('/video', {
            method: 'POST',
            body: formData
          });
          const data = await res.json();
          if (data.video_packets % 10 === 0) {
            log('Video frames sent: ' + data.video_packets);
          }
        } catch (err) {
          console.error('Video send error:', err);
        }
      }, 'image/jpeg', 0.5);
    }
    
    function stopVideo() {
      if (videoInterval) {
        clearInterval(videoInterval);
        videoInterval = null;
      }
      
      if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
      }
      
      videoActive = false;
      
      const video = document.getElementById('videoPreview');
      video.style.display = 'none';
      
      document.getElementById('startVideo').disabled = false;
      document.getElementById('stopVideo').disabled = true;
      document.getElementById('startVideo').classList.remove('active');
      
      log('Video test stopped');
      
      fetch('/control', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ cmd: 'VID:STOP' })
      });
    }
    
    async function sendCommand() {
      const input = document.getElementById('commandInput');
      const cmd = input.value.trim();
      if (!cmd) return;
      
      try {
        const res = await fetch('/control', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ cmd: cmd })
        });
        const data = await res.json();
        document.getElementById('commandResponse').textContent = 'Response: ' + data.message;
        log('Command sent: ' + cmd);
      } catch (err) {
        log('Command error: ' + err.message);
      }
    }
    
    // Log on load
    log('Controller loaded. Connect to WiFi: SSID=SmartGlasses_Test, Password=12345678');
  </script>
</body>
</html>
)rawliteral";

  server.send(200, "text/html", html);
}

void handleStatus()
{
  unsigned long uptime = millis() / 1000;
  int hours = uptime / 3600;
  int minutes = (uptime % 3600) / 60;
  int seconds = uptime % 60;

  String json = "{";
  json += "\"status\":\"ok\",";
  json += "\"uptime\":" + String(uptime) + ",";
  json += "\"uptime_formatted\":\"" + String(hours) + "h " + String(minutes) + "m " + String(seconds) + "s\",";
  json += "\"wifi_rssi\":" + String(WiFi.RSSI()) + ",";
  json += "\"ip\":\"" + WiFi.softAPIP().toString() + "\",";
  json += "\"audio_test\":" + String(audioTestMode ? "true" : "false") + ",";
  json += "\"video_test\":" + String(videoTestMode ? "true" : "false") + ",";
  json += "\"audio_packets\":" + String(audioPacketsReceived) + ",";
  json += "\"video_packets\":" + String(videoPacketsReceived) + ",";
  json += "\"audio_errors\":" + String(audioErrors) + ",";
  json += "\"video_errors\":" + String(videoErrors);
  json += "}";

  server.send(200, "application/json", json);
}

void handleAudio()
{
  if (!audioTestMode)
  {
    sendJsonResponse(false, "Audio test not started");
    return;
  }

  // Get audio data from multipart form
  HTTPUpload &upload = server.upload();

  if (upload.status == UPLOAD_FILE_START)
  {
    audioBufferSize = 0;
    logEvent("Audio upload started");
  }
  else if (upload.status == UPLOAD_FILE_WRITE)
  {
    // Append data to buffer
    if (audioBufferSize + upload.currentSize <= MAX_AUDIO_BUFFER)
    {
      memcpy(audioBuffer + audioBufferSize, upload.buf, upload.currentSize);
      audioBufferSize += upload.currentSize;
    }
    else
    {
      audioErrors++;
    }
  }
  else if (upload.status == UPLOAD_FILE_END)
  {
    // Process the audio data
    if (audioBufferSize > 0)
    {
      processAudioData(audioBuffer, audioBufferSize);
      audioPacketsReceived++;
      lastAudioPacketMs = millis();
    }

    String msg = "Audio received: " + String(audioBufferSize) + " bytes";
    sendJsonResponse(true, msg);
    logEvent(msg);
  }
}

void handleVideo()
{
  if (!videoTestMode)
  {
    sendJsonResponse(false, "Video test not started");
    return;
  }

  // Get video/frame data from multipart form
  HTTPUpload &upload = server.upload();

  if (upload.status == UPLOAD_FILE_START)
  {
    videoBufferSize = 0;
    logEvent("Video upload started");
  }
  else if (upload.status == UPLOAD_FILE_WRITE)
  {
    // Append data to buffer
    if (videoBufferSize + upload.currentSize <= MAX_VIDEO_BUFFER)
    {
      memcpy(videoBuffer + videoBufferSize, upload.buf, upload.currentSize);
      videoBufferSize += upload.currentSize;
    }
    else
    {
      videoErrors++;
    }
  }
  else if (upload.status == UPLOAD_FILE_END)
  {
    // Process the video frame
    if (videoBufferSize > 0)
    {
      processVideoData(videoBuffer, videoBufferSize);
      videoPacketsReceived++;
      lastVideoPacketMs = millis();
    }

    String msg = "Video received: " + String(videoBufferSize) + " bytes";
    sendJsonResponse(true, msg);
    logEvent(msg);
  }
}

void handleControl()
{
  if (!server.hasArg("plain"))
  {
    sendJsonResponse(false, "No data received");
    return;
  }

  String json = server.arg("plain");

  // Simple JSON parsing (find "cmd":)
  int cmdStart = json.indexOf("\"cmd\"");
  if (cmdStart == -1)
  {
    sendJsonResponse(false, "Invalid JSON");
    return;
  }

  int colonPos = json.indexOf(":", cmdStart);
  int quoteStart = json.indexOf("\"", colonPos);
  int quoteEnd = json.indexOf("\"", quoteStart + 1);

  if (colonPos == -1 || quoteStart == -1 || quoteEnd == -1)
  {
    sendJsonResponse(false, "Invalid cmd format");
    return;
  }

  String cmd = json.substring(quoteStart + 1, quoteEnd);

  Serial.print("Control command: ");
  Serial.println(cmd);

  // Handle commands
  if (cmd == "AUD:START")
  {
    audioTestMode = true;
    audioPacketsReceived = 0;
    audioErrors = 0;
    testStartTime = millis();
    sendJsonResponse(true, "Audio test started");
    updateDisplay("Audio Test", "Receiving...");
    logEvent("Audio test started");
  }
  else if (cmd == "AUD:STOP")
  {
    audioTestMode = false;
    unsigned long duration = (millis() - testStartTime) / 1000;
    String msg = "Audio test stopped. Packets: " + String(audioPacketsReceived);
    sendJsonResponse(true, msg);
    updateDisplay("Audio Test", "Stopped");
    logEvent(msg);
  }
  else if (cmd == "VID:START")
  {
    videoTestMode = true;
    videoPacketsReceived = 0;
    videoErrors = 0;
    testStartTime = millis();
    sendJsonResponse(true, "Video test started");
    updateDisplay("Video Test", "Receiving...");
    logEvent("Video test started");
  }
  else if (cmd == "VID:STOP")
  {
    videoTestMode = false;
    String msg = "Video test stopped. Packets: " + String(videoPacketsReceived);
    sendJsonResponse(true, msg);
    updateDisplay("Video Test", "Stopped");
    logEvent(msg);
  }
  else
  {
    // Echo back other commands
    sendJsonResponse(true, "Command received: " + cmd);
    logEvent("Command: " + cmd);
  }
}

void handleNotFound()
{
  String message = "File Not Found\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";
  for (uint8_t i = 0; i < server.args(); i++)
  {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }
  server.send(404, "text/plain", message);
}

// ============== DATA PROCESSING ==============

void processAudioData(const uint8_t *data, size_t len)
{
  // Mock audio processing - in real implementation:
  // - Decode audio format (PCM, MP3, Opus, etc.)
  // - Apply audio processing (AGC, noise reduction)
  // - Feed to speech recognition

  Serial.print("Audio data received: ");
  Serial.print(len);
  Serial.println(" bytes");

  // Simulate processing by toggling LED briefly
  digitalWrite(LED_PIN, HIGH);
  delay(10);
  digitalWrite(LED_PIN, LOW);
}

void processVideoData(const uint8_t *data, size_t len)
{
  // Mock video processing - in real implementation:
  // - Decode image (JPEG, PNG, etc.)
  // - Apply image processing
  // - Run object detection, QR scanning, etc.

  Serial.print("Video data received: ");
  Serial.print(len);
  Serial.println(" bytes");

  // Blink LED for video
  digitalWrite(LED_PIN, HIGH);
  delay(5);
  digitalWrite(LED_PIN, LOW);
}

// ============== UTILITIES ==============

void sendJsonResponse(bool success, const String &message)
{
  String json = "{";
  json += "\"success\":" + String(success ? "true" : "false") + ",";
  json += "\"message\":\"" + message + "\",";
  json += "\"audio_packets\":" + String(audioPacketsReceived) + ",";
  json += "\"video_packets\":" + String(videoPacketsReceived);
  json += "}";

  server.send(200, "application/json", json);
}

void logEvent(const String &event)
{
  Serial.println(event);
}

void updateDisplay(const String &line1, const String &line2)
{
  displayLine1 = line1;
  displayLine2 = line2;
  lastDisplayUpdate = millis();

#if USE_SH1106
  gDisplay.clearDisplay();
  gDisplay.setFont(u8g2_font_nine_bytenumbers);
  gDisplay.setCursor(0, 20);
  gDisplay.print(line1);
  gDisplay.setCursor(0, 40);
  gDisplay.print(line2);
  gDisplay.setFont(u8g2_font_5x8);
  gDisplay.setCursor(0, 55);
  gDisplay.print("IP: 192.168.4.1");
  gDisplay.sendDisplay();
#endif
}

// ============== MAIN LOOP ==============

void loop()
{
  // Handle HTTP requests
  server.handleClient();

  static unsigned long lastPollMs = 0;

  // Poll touch sensors
#if USE_TOUCH
  if (millis() - lastPollMs < 50)
  {
    delay(1);
  }
  lastPollMs = millis();

  bool touch1 = (digitalRead(TOUCH1_PIN) == TOUCH_ACTIVE_LEVEL);
  bool touch2 = (digitalRead(TOUCH2_PIN) == TOUCH_ACTIVE_LEVEL);

  if (touch1 != lastTouch1)
  {
    lastTouch1 = touch1;
    logEvent(touch1 ? "Touch1 pressed" : "Touch1 released");
    updateDisplay("Touch1", touch1 ? "Pressed" : "Released");
  }

  if (touch2 != lastTouch2)
  {
    lastTouch2 = touch2;
    logEvent(touch2 ? "Touch2 pressed" : "Touch2 released");
    updateDisplay("Touch2", touch2 ? "Pressed" : "Released");
  }
#endif

  // Update display periodically
  if (millis() - lastDisplayUpdate > 5000)
  {
    String line1 = audioTestMode ? "Audio ON" : (videoTestMode ? "Video ON" : "WiFi Ready");
    String line2 = "Packets: A" + String(audioPacketsReceived) + " V" + String(videoPacketsReceived);
    updateDisplay(line1, line2);
  }

  // Debug: show stats periodically
  static unsigned long lastStatsMs = 0;
  if (millis() - lastStatsMs > 10000)
  {
    lastStatsMs = millis();
    Serial.println("=== Status ===");
    Serial.print("Audio packets: ");
    Serial.println(audioPacketsReceived);
    Serial.print("Video packets: ");
    Serial.println(videoPacketsReceived);
    Serial.print("WiFi clients: ");
    Serial.println(WiFi.softAPgetStationNum());
    Serial.print("RSSI: ");
    Serial.println(WiFi.RSSI());
  }
}
