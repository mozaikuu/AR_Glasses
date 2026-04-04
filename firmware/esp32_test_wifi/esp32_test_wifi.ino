/**
 * Smart Glasses ESP32 - Full Pipeline Test
 * Works with phone file upload (bypasses browser camera/mic issues)
 */

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <cstring>
#include "esp_system.h"
#include "esp_heap_caps.h"
#include "driver/i2s.h"

// ============== BUILD PROFILE ==============
// Select one profile at compile time (PlatformIO build flags).
// If none is set, default to PROFILE_FULL.
#if !defined(PROFILE_FULL) && !defined(PROFILE_WIFI_ONLY) && !defined(PROFILE_AUDIO_TEST) && !defined(PROFILE_MINIMAL) && !defined(PROFILE_CAMERA_TEST)
#define PROFILE_FULL 1
#endif

#if defined(PROFILE_WIFI_ONLY)
#define PROFILE_USE_SH1106 1
#define PROFILE_USE_DAC_TTS 0
#define PROFILE_USE_I2S_MIC 0
#define PROFILE_USE_BLE 0
#define PROFILE_USE_CAMERA 0
#define PROFILE_USE_TOUCH 1
#elif defined(PROFILE_AUDIO_TEST)
#define PROFILE_USE_SH1106 0
#define PROFILE_USE_DAC_TTS 1
#define PROFILE_USE_I2S_MIC 1
#define PROFILE_USE_BLE 0
#define PROFILE_USE_CAMERA 0
#define PROFILE_USE_TOUCH 1
#elif defined(PROFILE_CAMERA_TEST)
#define PROFILE_USE_SH1106 0
#define PROFILE_USE_DAC_TTS 0
#define PROFILE_USE_I2S_MIC 0
#define PROFILE_USE_BLE 0
#define PROFILE_USE_CAMERA 1
#define PROFILE_USE_TOUCH 0
#elif defined(PROFILE_MINIMAL)
#define PROFILE_USE_SH1106 0
#define PROFILE_USE_DAC_TTS 0
#define PROFILE_USE_I2S_MIC 0
#define PROFILE_USE_BLE 0
#define PROFILE_USE_CAMERA 0
#define PROFILE_USE_TOUCH 1
#else
// Camera-priority default profile:
// WROVER camera pin map overlaps with SH1106 I2C (GPIO21/22) and DAC TTS (GPIO25/26).
// Camera D0 also uses GPIO4, which conflicts with the I2S mic data pin.
// Keep camera enabled and disable conflicting peripherals in the default profile.
#define PROFILE_USE_SH1106 0
#define PROFILE_USE_DAC_TTS 0
#define PROFILE_USE_I2S_MIC 0
#define PROFILE_USE_BLE 1
#define PROFILE_USE_CAMERA 1
#define PROFILE_USE_TOUCH 1
#endif

#ifndef ENABLE_BLE_BRIDGE
#define ENABLE_BLE_BRIDGE PROFILE_USE_BLE
#endif

#if ENABLE_BLE_BRIDGE
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLECharacteristic.h>
#include <BLE2902.h>
#endif

#ifndef USE_SH1106
#define USE_SH1106 PROFILE_USE_SH1106
#endif

#ifndef USE_DAC_TTS_MODULE
#define USE_DAC_TTS_MODULE PROFILE_USE_DAC_TTS
#endif

#ifndef USE_I2S_MIC_MODULE
#define USE_I2S_MIC_MODULE PROFILE_USE_I2S_MIC
#endif

#ifndef USE_CAMERA
#define USE_CAMERA PROFILE_USE_CAMERA
#endif

#ifndef USE_TOUCH
#define USE_TOUCH PROFILE_USE_TOUCH
#endif

#if USE_CAMERA
#include "esp_camera.h"
#endif

#if USE_SH1106
#include <U8g2lib.h>
U8G2_SH1106_128X64_NONAME_F_HW_I2C gDisplay(U8G2_R0, U8X8_PIN_NONE);
#endif

// ============== CONFIG ==============
const char *AP_SSID = "SmartGlasses_Test";
const char *AP_PASSWORD = "12345678";
const IPAddress AP_IP(192, 168, 4, 1);
const IPAddress AP_GATEWAY(192, 168, 4, 1);
const IPAddress AP_SUBNET(255, 255, 255, 0);

const char *WIFI_SSID = "Moussa24";
const char *WIFI_PASSWORD = "AhmedMoussa2003!";
const char *SERVER_URL = "http://192.168.100.2:8000/process";

#if ENABLE_BLE_BRIDGE
#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#endif

#define LED_PIN 2
#if USE_CAMERA
#define TOUCH_PAD_PIN 13
#else
#define TOUCH_PAD_PIN 18
#endif
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22
#define I2S_MIC_BCK 14
#define I2S_MIC_WS 15
#define I2S_MIC_DATA 4
#define DAC_TTS_LEFT_PIN 25
#define DAC_TTS_RIGHT_PIN 26

#if USE_CAMERA
#define CAM_PIN_PWDN -1
#define CAM_PIN_RESET -1
#define CAM_PIN_XCLK 21
#define CAM_PIN_SIOD 26
#define CAM_PIN_SIOC 27
#define CAM_PIN_D7 35
#define CAM_PIN_D6 34
#define CAM_PIN_D5 39
#define CAM_PIN_D4 36
#define CAM_PIN_D3 19
#define CAM_PIN_D2 18
#define CAM_PIN_D1 5
#define CAM_PIN_D0 4
#define CAM_PIN_VSYNC 25
#define CAM_PIN_HREF 23
#define CAM_PIN_PCLK 22
#endif

const uint16_t OLED_MAX_CHARS_PER_LINE = 21;
const uint16_t OLED_MAX_LINES = 3;
const unsigned long OLED_SCROLL_INTERVAL_MS = 120;
const uint8_t OLED_SCROLL_STEP_CHARS = 2;
const uint16_t OLED_SCROLL_GAP_SPACES = 8;
const unsigned long TOUCH2_LONG_PRESS_MS = 900;
const unsigned long TOUCH2_DOUBLE_TAP_MS = 450;

const uint32_t MIC_SAMPLE_RATE = 16000;
const uint32_t MIC_MAX_RECORD_MS = 5000;
const size_t MIC_MAX_SAMPLES = (MIC_SAMPLE_RATE * MIC_MAX_RECORD_MS) / 1000;
const size_t MIC_READ_CHUNK_SAMPLES = 256;
const bool MIC_PREFER_PSRAM = true;
const bool MIC_ALLOW_INTERNAL_HEAP_FALLBACK = false;

enum OperationMode
{
  MODE_WIFI_DIRECT = 0,
  MODE_PHONE_RELAY = 1,
};

// ============== STATE ==============
WebServer server(80);
bool serverConnected = false;
int lastBackendHttpCode = 0;
String lastBackendError = "";
#if ENABLE_BLE_BRIDGE
BLECharacteristic *gCharacteristic = nullptr;
bool deviceConnected = false;
volatile bool bleConnectEvent = false;
volatile bool bleDisconnectEvent = false;
char pendingBleCommand[256] = {0};
volatile bool pendingBleCommandReady = false;
portMUX_TYPE bleMux = portMUX_INITIALIZER_UNLOCKED;
#endif
OperationMode currentMode = MODE_WIFI_DIRECT;
String lastPrompt = "";
bool lastTouch2 = false;
bool micReady = false;
bool micDriverInstalled = false;
bool isRecording = false;
int16_t *micPcmBuffer = nullptr;
size_t micRecordedSamples = 0;
unsigned long micRecordingStartMs = 0;
unsigned long touch2PressStartMs = 0;
unsigned long lastTouch2TapMs = 0;
String displayLine1Cache = "";
String displayLine2Cache = "";
String displayScrollBuffer = "";
size_t displayScrollOffset = 0;
bool displayScrollEnabled = false;
unsigned long lastDisplayScrollMs = 0;
bool cameraReady = false;
String cameraLastError = "DISABLED";

// Forward declarations for functions referenced before their definitions.
void connectToWiFi();
String escapeJson(const String &text);
String unescapeJson(const String &text);
String parseJsonStringField(const String &json, const String &key);
void notifyMessage(const String &payload);
String normalizeProcessPayload(String body);
bool sendProcessPayload(const String &payload, String &response);
void processTextCommand(const String &text, const String &source);
void handleCommand(const String &cmd, const String &source);
void handleSerialInput();
void handleRoot();
void handleStatus();
void handleProcess();
void handleCommandRoute();
void handleNotFound();
void speakText(const String &text);
const char *resetReasonToText(esp_reset_reason_t reason);
void updateDisplay(const String &line1, const String &line2);
void setDisplayContent(const String &line1, const String &line2, bool resetScroll);
void renderDisplay();
void tickDisplayScroll();
void drawWrappedText(int x, int yStart, int maxCharsPerLine, int maxLines, const String &text);
bool fetchAndPlayTtsFromUrl(const String &ttsUrl);
void setupMicInput();
void setupCameraInput();
void logMemorySnapshot(const char *stage);
void tickMicRecording();
void startMicRecording();
void stopAndSendRecording(const String &source);
bool ensureMicBuffer();
void releaseMicBuffer();
int32_t centerMicSamplesAndMeasurePeak(size_t sampleCount);
bool appendBase64(String &out, const uint8_t *data, size_t len);
bool captureAndAnalyzeCamera(const String &prompt, const String &source, String &responseTextOut);
void handleCameraStatus();
void handleCameraAnalyzeRoute();
void toggleOperationMode();
#if USE_DAC_TTS_MODULE
void setupTtsAudio();
bool playWavFromHttp(HTTPClient &http);
inline void writeDacPair(uint8_t value);
#endif

// ============== HTML - With file upload ==============
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart Glasses Test</title>
<style>
body{font-family:Arial;background:#1a1a2e;color:#fff;padding:20px;text-align:center}
h1{color:#00d4ff}
.btn{background:#00d4ff;color:#000;padding:15px 25px;border:0;border-radius:8px;font-size:16px;margin:10px}
#out{background:#000;padding:10px;margin:10px 0;text-align:left;white-space:pre-wrap;height:200px;overflow:auto}
input[type=text]{width:70%;padding:10px;margin:5px}
input[type=file]{margin:10px}
</style>
</head>
<body>
<h1>Smart Glasses Test</h1>
<p>Server: <span id="srv">?</span></p>
<p>Mode: <span id="mode">WIFI</span></p>

<div>
<h3>1. Upload Audio</h3>
<input type="file" id="audioFile" accept="audio/*">
<button class="btn" onclick="uploadAudio()">Send Audio</button>
</div>

<div>
<h3>2. Upload Image</h3>
<input type="file" id="imageFile" accept="image/*">
<button class="btn" onclick="uploadImage()">Send Image</button>
</div>

<div>
<h3>3. Text Command</h3>
<input type="text" id="cmd" placeholder="Type message...">
<button class="btn" onclick="sendText()">Send</button>
</div>

<div>
<h3>4. Mode</h3>
<button class="btn" onclick="setMode('MODE:WIFI')">WiFi Direct</button>
<button class="btn" onclick="setMode('MODE:PHONE')">Phone Relay</button>
</div>

<div>
<h3>5. Onboard Camera</h3>
<input type="text" id="camPrompt" placeholder="Prompt for onboard camera" value="Describe what you see">
<button class="btn" onclick="analyzeEspCamera()">Capture ESP Camera</button>
</div>

<div id="out"></div>

<script>
var ESP = 'http://192.168.4.1';

function log(s){
  document.getElementById('out').innerHTML += s + '\n';
  document.getElementById('out').scrollTop = document.getElementById('out').scrollHeight;
}

async function uploadAudio(){
  var f = document.getElementById('audioFile').files[0];
  if(!f){log('Select an audio file first');return;}
  log('Reading audio file...');
  
  var reader = new FileReader();
  reader.onload = async function(){
    var base64 = reader.result.split(',')[1];
    log('Sending to server...');
    try{
      var r = await fetch(ESP+'/process', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({audio:base64, mode:'quick'})
      });
      var resp = await r.text();
      log('Server: '+resp);
    }catch(e){log('Error: '+e.message);}
  };
  reader.readAsDataURL(f);
}

async function uploadImage(){
  var f = document.getElementById('imageFile').files[0];
  if(!f){log('Select an image file first');return;}
  log('Reading image file...');
  
  var reader = new FileReader();
  reader.onload = async function(){
    var base64 = reader.result.split(',')[1];
    log('Sending to server...');
    try{
      var r = await fetch(ESP+'/process', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({image:base64, mode:'quick'})
      });
      var resp = await r.text();
      log('Server: '+resp);
    }catch(e){log('Error: '+e.message);}
  };
  reader.readAsDataURL(f);
}

async function sendText(){
  var txt = document.getElementById('cmd').value;
  if(!txt){log('Enter some text');return;}
  log('Sending: '+txt);
  try{
    var r = await fetch(ESP+'/process', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text:txt, mode:'quick'})
    });
    var resp = await r.text();
    log('Server: '+resp);
  }catch(e){log('Error: '+e.message);}
}

async function setMode(mode){
  try{
    var r = await fetch(ESP + '/command', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({command:mode})
    });
    var resp = await r.text();
    log('Mode response: ' + resp);
  }catch(e){log('Error: '+e.message);}
}

async function analyzeEspCamera(){
  var prompt = document.getElementById('camPrompt').value || 'Describe what you see';
  log('Capturing onboard camera...');
  try{
    var r = await fetch(ESP + '/camera/analyze', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({prompt:prompt})
    });
    var resp = await r.text();
    log('Camera: ' + resp);
  }catch(e){log('Error: '+e.message);}
}

setInterval(async function(){
  try{
    var j = await fetch(ESP+'/status').then(r=>r.json());
    document.getElementById('srv').innerText = j.server?'OK':'NO';
    document.getElementById('mode').innerText = j.mode || 'WIFI';
  }catch(e){document.getElementById('srv').innerText='ERR';}
},2000);

log('Ready. Select a file and click Send.');
</script>
</body>
</html>
)rawliteral";

#if ENABLE_BLE_BRIDGE
class MyServerCallbacks : public BLEServerCallbacks
{
public:
  void onConnect(BLEServer *pServer) override
  {
    (void)pServer;
    deviceConnected = true;
    bleConnectEvent = true;
  }

  void onDisconnect(BLEServer *pServer) override
  {
    (void)pServer;
    deviceConnected = false;
    bleDisconnectEvent = true;
  }
};

class CharacteristicCallbacks : public BLECharacteristicCallbacks
{
  void onWrite(BLECharacteristic *characteristic) override
  {
    String cmd = String(characteristic->getValue().c_str());
    cmd.trim();
    if (cmd.length() == 0)
    {
      return;
    }

    portENTER_CRITICAL(&bleMux);
    cmd.toCharArray(pendingBleCommand, sizeof(pendingBleCommand));
    pendingBleCommandReady = true;
    portEXIT_CRITICAL(&bleMux);
  }
};
#endif

String escapeJson(const String &text)
{
  String out;
  out.reserve(text.length() + 16);
  for (size_t i = 0; i < text.length(); i++)
  {
    char c = text[i];
    if (c == '\\' || c == '"')
    {
      out += '\\';
      out += c;
    }
    else if (c == '\n')
    {
      out += "\\n";
    }
    else if (c == '\r')
    {
      out += "\\r";
    }
    else if (c == '\t')
    {
      out += "\\t";
    }
    else
    {
      out += c;
    }
  }
  return out;
}

String unescapeJson(const String &text)
{
  String out;
  out.reserve(text.length());
  for (size_t i = 0; i < text.length(); i++)
  {
    char c = text[i];
    if (c == '\\' && i + 1 < text.length())
    {
      char n = text[i + 1];
      if (n == 'n')
      {
        out += '\n';
        i++;
      }
      else if (n == 'r')
      {
        out += '\r';
        i++;
      }
      else if (n == 't')
      {
        out += '\t';
        i++;
      }
      else if (n == '"' || n == '\\' || n == '/')
      {
        out += n;
        i++;
      }
      else
      {
        out += c;
      }
    }
    else
    {
      out += c;
    }
  }
  return out;
}

String parseJsonStringField(const String &json, const String &key)
{
  String needle = "\"" + key + "\"";
  int keyPos = json.indexOf(needle);
  if (keyPos < 0)
  {
    return "";
  }

  int colonPos = json.indexOf(':', keyPos + needle.length());
  if (colonPos < 0)
  {
    return "";
  }

  int quoteStart = json.indexOf('"', colonPos + 1);
  if (quoteStart < 0)
  {
    return "";
  }

  String value;
  bool escaped = false;
  for (int i = quoteStart + 1; i < json.length(); i++)
  {
    char c = json[i];
    if (!escaped && c == '\\')
    {
      escaped = true;
      value += c;
      continue;
    }
    if (!escaped && c == '"')
    {
      return unescapeJson(value);
    }
    escaped = false;
    value += c;
  }
  return "";
}

void notifyMessage(const String &payload)
{
  Serial.println(payload);
#if ENABLE_BLE_BRIDGE
  if (deviceConnected && gCharacteristic)
  {
    gCharacteristic->setValue(payload.c_str());
    gCharacteristic->notify();
  }
#endif
}

void speakText(const String &text)
{
  Serial.print("TTS RX: ");
  Serial.println(text);
  updateDisplay("Server says", text);
}

void updateDisplay(const String &line1, const String &line2)
{
#if USE_SH1106
  setDisplayContent(line1, line2, true);
#else
  Serial.print("[OLED] ");
  Serial.print(line1);
  Serial.print(" | ");
  Serial.println(line2);
#endif
}

void setDisplayContent(const String &line1, const String &line2, bool resetScroll)
{
#if USE_SH1106
  displayLine1Cache = line1;
  displayLine2Cache = line2;

  const int maxCharsVisible = OLED_MAX_CHARS_PER_LINE * OLED_MAX_LINES;
  bool nextScrollEnabled = (displayLine2Cache.length() > maxCharsVisible);
  if (nextScrollEnabled)
  {
    displayScrollBuffer = displayLine2Cache;
    for (uint16_t i = 0; i < OLED_SCROLL_GAP_SPACES; i++)
    {
      displayScrollBuffer += ' ';
    }
    displayScrollBuffer += displayLine2Cache;
  }
  else
  {
    displayScrollBuffer = displayLine2Cache;
  }

  if (resetScroll || !displayScrollEnabled || !nextScrollEnabled)
  {
    displayScrollOffset = 0;
    lastDisplayScrollMs = millis();
  }
  displayScrollEnabled = nextScrollEnabled;
  renderDisplay();
#else
  (void)line1;
  (void)line2;
  (void)resetScroll;
#endif
}

void renderDisplay()
{
#if USE_SH1106
  gDisplay.clearBuffer();
  gDisplay.setFont(u8g2_font_6x10_tr);
  gDisplay.drawStr(0, 14, displayLine1Cache.c_str());

  if (displayScrollEnabled)
  {
    const int maxCharsVisible = OLED_MAX_CHARS_PER_LINE * OLED_MAX_LINES;
    String visible = "";
    visible.reserve(maxCharsVisible);
    for (int i = 0; i < maxCharsVisible; i++)
    {
      size_t idx = displayScrollOffset + (size_t)i;
      if (idx < displayScrollBuffer.length())
      {
        visible += displayScrollBuffer[idx];
      }
      else
      {
        visible += ' ';
      }
    }
    drawWrappedText(0, 30, OLED_MAX_CHARS_PER_LINE, OLED_MAX_LINES, visible);
  }
  else
  {
    drawWrappedText(0, 30, OLED_MAX_CHARS_PER_LINE, OLED_MAX_LINES, displayLine2Cache);
  }

  gDisplay.sendBuffer();
#endif
}

void tickDisplayScroll()
{
#if USE_SH1106
  if (!displayScrollEnabled)
  {
    return;
  }
  if (millis() - lastDisplayScrollMs < OLED_SCROLL_INTERVAL_MS)
  {
    return;
  }
  lastDisplayScrollMs = millis();

  displayScrollOffset += OLED_SCROLL_STEP_CHARS;
  const int maxCharsVisible = OLED_MAX_CHARS_PER_LINE * OLED_MAX_LINES;
  if (displayScrollOffset + (size_t)maxCharsVisible >= displayScrollBuffer.length())
  {
    displayScrollOffset = 0;
  }
  renderDisplay();
#endif
}

void drawWrappedText(int x, int yStart, int maxCharsPerLine, int maxLines, const String &text)
{
#if USE_SH1106
  if (maxLines <= 0 || maxCharsPerLine <= 0)
  {
    return;
  }

  String remaining = text;
  remaining.trim();
  int y = yStart;

  for (int line = 0; line < maxLines; line++)
  {
    if (remaining.length() == 0)
    {
      return;
    }

    if ((int)remaining.length() <= maxCharsPerLine)
    {
      gDisplay.drawUTF8(x, y, remaining.c_str());
      return;
    }

    int split = maxCharsPerLine;
    while (split > 0 && remaining[split] != ' ')
    {
      split--;
    }
    if (split <= 0)
    {
      split = maxCharsPerLine;
    }

    String part = remaining.substring(0, split);
    part.trim();
    gDisplay.drawUTF8(x, y, part.c_str());

    remaining = remaining.substring(split);
    remaining.trim();
    y += 12;
  }
#else
  (void)x;
  (void)yStart;
  (void)maxCharsPerLine;
  (void)maxLines;
  (void)text;
#endif
}

bool fetchAndPlayTtsFromUrl(const String &ttsUrl)
{
  if (ttsUrl.length() == 0)
  {
    return false;
  }

  String fullUrl = ttsUrl;
  if (ttsUrl.startsWith("/"))
  {
    String base = String(SERVER_URL);
    int protoIdx = base.indexOf("://");
    int hostStart = (protoIdx >= 0) ? (protoIdx + 3) : 0;
    int firstSlash = base.indexOf('/', hostStart);
    if (firstSlash > 0)
    {
      base = base.substring(0, firstSlash);
    }
    fullUrl = base + ttsUrl;
  }

  HTTPClient http;
  http.begin(fullUrl);
  int code = http.GET();
  if (code <= 0)
  {
    Serial.print("ERR:TTS_FETCH:");
    Serial.println(http.errorToString(code));
    http.end();
    return false;
  }

#if USE_DAC_TTS_MODULE
  bool ok = playWavFromHttp(http);
  http.end();
  return ok;
#else
  Serial.print("TTS URL ready: ");
  Serial.println(fullUrl);
  http.end();
  return true;
#endif
}

#if USE_DAC_TTS_MODULE
void setupTtsAudio()
{
  pinMode(DAC_TTS_LEFT_PIN, OUTPUT);
  pinMode(DAC_TTS_RIGHT_PIN, OUTPUT);
  writeDacPair(128);
  Serial.println("TTS DAC init on GPIO25/26");
}

bool playWavFromHttp(HTTPClient &http)
{
  WiFiClient *stream = http.getStreamPtr();
  if (!stream)
  {
    Serial.println("ERR:TTS_DAC:NO_STREAM");
    return false;
  }

  uint8_t header[44];
  int got = stream->readBytes(header, sizeof(header));
  if (got < 44)
  {
    Serial.println("ERR:TTS_DAC:BAD_WAV_HEADER");
    return false;
  }

  uint16_t audioFormat = (uint16_t)header[20] | ((uint16_t)header[21] << 8);
  uint16_t channels = (uint16_t)header[22] | ((uint16_t)header[23] << 8);
  uint32_t sampleRate = (uint32_t)header[24] |
                        ((uint32_t)header[25] << 8) |
                        ((uint32_t)header[26] << 16) |
                        ((uint32_t)header[27] << 24);
  uint16_t bitsPerSample = (uint16_t)header[34] | ((uint16_t)header[35] << 8);

  if (audioFormat != 1)
  {
    Serial.println("ERR:TTS_DAC:NON_PCM");
    return false;
  }
  if (channels == 0 || channels > 2)
  {
    Serial.println("ERR:TTS_DAC:BAD_CHANNELS");
    return false;
  }
  if (sampleRate == 0)
  {
    sampleRate = 22050;
  }
  if (bitsPerSample != 8 && bitsPerSample != 16)
  {
    Serial.println("ERR:TTS_DAC:BAD_BPS");
    return false;
  }

  int totalLen = http.getSize();
  int remaining = (totalLen > 44) ? (totalLen - 44) : -1;
  uint8_t buf[1024];
  unsigned long lastDataMs = millis();
  uint32_t sampleIntervalUs = 1000000UL / sampleRate;
  if (sampleIntervalUs == 0)
  {
    sampleIntervalUs = 1;
  }
  uint32_t nextSampleUs = micros();

  int bytesPerSample = bitsPerSample / 8;
  int frameBytes = bytesPerSample * channels;
  if (frameBytes <= 0)
  {
    return false;
  }

  while (http.connected())
  {
    int want = sizeof(buf);
    if (remaining >= 0 && remaining < want)
    {
      want = remaining;
    }
    if (want <= 0)
    {
      break;
    }

    int n = stream->readBytes(buf, want);
    if (n <= 0)
    {
      if (millis() - lastDataMs > 1200)
      {
        break;
      }
      delay(2);
      continue;
    }
    lastDataMs = millis();
    if (remaining >= 0)
    {
      remaining -= n;
    }

    int idx = 0;
    while (idx + frameBytes <= n)
    {
      uint8_t dacVal = 128;
      if (bitsPerSample == 8)
      {
        uint16_t sL = buf[idx];
        if (channels == 2)
        {
          uint16_t sR = buf[idx + 1];
          dacVal = (uint8_t)((sL + sR) / 2);
        }
        else
        {
          dacVal = (uint8_t)sL;
        }
      }
      else
      {
        int16_t sL = (int16_t)((uint16_t)buf[idx] | ((uint16_t)buf[idx + 1] << 8));
        int16_t sMono = sL;
        if (channels == 2)
        {
          int16_t sR = (int16_t)((uint16_t)buf[idx + 2] | ((uint16_t)buf[idx + 3] << 8));
          sMono = (int16_t)(((int32_t)sL + (int32_t)sR) / 2);
        }
        dacVal = (uint8_t)(((int32_t)sMono + 32768) >> 8);
      }

      while ((int32_t)(micros() - nextSampleUs) < 0)
      {
      }
      writeDacPair(dacVal);
      nextSampleUs += sampleIntervalUs;
      idx += frameBytes;
    }
  }
  writeDacPair(128);
  return true;
}

inline void writeDacPair(uint8_t value)
{
  dacWrite(DAC_TTS_LEFT_PIN, value);
  dacWrite(DAC_TTS_RIGHT_PIN, value);
}
#endif

void setupMicInput()
{
#if USE_I2S_MIC_MODULE
  i2s_config_t i2sConfig;
  memset(&i2sConfig, 0, sizeof(i2sConfig));
  i2sConfig.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX);
  i2sConfig.sample_rate = MIC_SAMPLE_RATE;
  i2sConfig.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  i2sConfig.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;
  i2sConfig.communication_format = I2S_COMM_FORMAT_I2S;
  i2sConfig.intr_alloc_flags = 0;
  i2sConfig.dma_buf_count = 4;
  i2sConfig.dma_buf_len = 256;
  i2sConfig.use_apll = false;
  i2sConfig.tx_desc_auto_clear = false;
  i2sConfig.fixed_mclk = 0;

  i2s_pin_config_t pinConfig;
  memset(&pinConfig, 0, sizeof(pinConfig));
  pinConfig.bck_io_num = I2S_MIC_BCK;
  pinConfig.ws_io_num = I2S_MIC_WS;
  pinConfig.data_out_num = -1;
  pinConfig.data_in_num = I2S_MIC_DATA;

  if (micDriverInstalled)
  {
    i2s_driver_uninstall(I2S_NUM_0);
    micDriverInstalled = false;
  }
  esp_err_t err = i2s_driver_install(I2S_NUM_0, &i2sConfig, 0, nullptr);
  if (err != ESP_OK)
  {
    micReady = false;
    Serial.printf("ERR:MIC:I2S_INIT:%d\n", (int)err);
    return;
  }

  err = i2s_set_pin(I2S_NUM_0, &pinConfig);
  if (err != ESP_OK)
  {
    i2s_driver_uninstall(I2S_NUM_0);
    micDriverInstalled = false;
    micReady = false;
    Serial.printf("ERR:MIC:I2S_PIN:%d\n", (int)err);
    return;
  }

  i2s_zero_dma_buffer(I2S_NUM_0);
  micDriverInstalled = true;
  micReady = true;
  Serial.println("I2S mic ready (GPIO14/15/4)");
#else
  micReady = false;
#endif
}

void setupCameraInput()
{
#if USE_CAMERA
  camera_config_t config;
  memset(&config, 0, sizeof(config));

  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = CAM_PIN_D0;
  config.pin_d1 = CAM_PIN_D1;
  config.pin_d2 = CAM_PIN_D2;
  config.pin_d3 = CAM_PIN_D3;
  config.pin_d4 = CAM_PIN_D4;
  config.pin_d5 = CAM_PIN_D5;
  config.pin_d6 = CAM_PIN_D6;
  config.pin_d7 = CAM_PIN_D7;
  config.pin_xclk = CAM_PIN_XCLK;
  config.pin_pclk = CAM_PIN_PCLK;
  config.pin_vsync = CAM_PIN_VSYNC;
  config.pin_href = CAM_PIN_HREF;
  config.pin_sccb_sda = CAM_PIN_SIOD;
  config.pin_sccb_scl = CAM_PIN_SIOC;
  config.pin_pwdn = CAM_PIN_PWDN;
  config.pin_reset = CAM_PIN_RESET;
  config.xclk_freq_hz = 10000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 12;
  config.fb_count = 2;
  config.grab_mode = CAMERA_GRAB_LATEST;
  config.fb_location = CAMERA_FB_IN_PSRAM;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK)
  {
    cameraReady = false;
    cameraLastError = "CAM_INIT_ERR:" + String((int)err);
    Serial.printf("ERR:CAM:INIT:%d\n", (int)err);
    return;
  }

  cameraReady = true;
  cameraLastError = "";
  Serial.println("Camera ready (ESP-WROVER)");
#else
  cameraReady = false;
  cameraLastError = "DISABLED";
#endif
}

bool captureAndAnalyzeCamera(const String &prompt, const String &source, String &responseTextOut)
{
  responseTextOut = "";
#if USE_CAMERA
  if (!cameraReady)
  {
    notifyMessage("ERR:CAM:NOT_READY");
    if (cameraLastError.length() > 0)
    {
      notifyMessage("ERR:CAM:" + cameraLastError);
    }
    return false;
  }

  camera_fb_t *fb = nullptr;
  for (int attempt = 0; attempt < 3; ++attempt)
  {
    fb = esp_camera_fb_get();
    if (fb)
    {
      break;
    }
    delay(40);
  }
  if (!fb)
  {
    cameraLastError = "CAPTURE_FAIL";
    notifyMessage("ERR:CAM:CAPTURE");
    return false;
  }

  size_t b64Len = ((fb->len + 2) / 3) * 4;
  String payload;
  if (!payload.reserve(b64Len + 300))
  {
    esp_camera_fb_return(fb);
    notifyMessage("ERR:CAM:NO_MEM");
    return false;
  }

  payload = "{\"image_base64\":\"";
  if (!appendBase64(payload, fb->buf, fb->len))
  {
    esp_camera_fb_return(fb);
    notifyMessage("ERR:CAM:B64");
    return false;
  }
  esp_camera_fb_return(fb);

  payload += "\",\"text\":\"";
  payload += escapeJson(prompt.length() > 0 ? prompt : String("Describe what you see"));
  payload += "\",\"mode\":\"quick\",\"client\":\"";
  payload += source;
  payload += "\"}";

  updateDisplay("Camera", "Analyzing...");
  String response;
  bool ok = sendProcessPayload(payload, response);
  if (!ok)
  {
    notifyMessage("ERR:CAM:SERVER");
    notifyMessage("ERR:HTTP:" + String(lastBackendHttpCode));
    if (lastBackendError.length() > 0)
    {
      notifyMessage("ERR:DETAIL:" + lastBackendError);
    }
    return false;
  }

  responseTextOut = parseJsonStringField(response, "text");
  if (responseTextOut.length() == 0)
  {
    responseTextOut = response;
  }

  notifyMessage("TTS:" + responseTextOut);
  speakText(responseTextOut);

  String ttsUrl = parseJsonStringField(response, "tts_url");
  if (ttsUrl.length() > 0)
  {
    notifyMessage("TTS_URL:" + ttsUrl);
    if (!fetchAndPlayTtsFromUrl(ttsUrl))
    {
      notifyMessage("ERR:TTS_PLAYBACK");
    }
  }

  return true;
#else
  (void)prompt;
  (void)source;
  notifyMessage("ERR:CAM:DISABLED");
  return false;
#endif
}

void logMemorySnapshot(const char *stage)
{
  size_t internalFree = heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
  size_t internalLargest = heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL);
  size_t psramTotal = heap_caps_get_total_size(MALLOC_CAP_SPIRAM);
  size_t psramFree = heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
  size_t psramLargest = heap_caps_get_largest_free_block(MALLOC_CAP_SPIRAM);

  Serial.printf("MEM[%s] INT_FREE=%u INT_LARGEST=%u PSRAM_TOTAL=%u PSRAM_FREE=%u PSRAM_LARGEST=%u\n",
                stage,
                (unsigned)internalFree,
                (unsigned)internalLargest,
                (unsigned)psramTotal,
                (unsigned)psramFree,
                (unsigned)psramLargest);
}

bool appendBase64(String &out, const uint8_t *data, size_t len)
{
  static const char kTable[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  if (!data || len == 0)
  {
    return false;
  }

  for (size_t i = 0; i < len; i += 3)
  {
    uint32_t block = ((uint32_t)data[i]) << 16;
    bool hasSecond = (i + 1) < len;
    bool hasThird = (i + 2) < len;
    if (hasSecond)
    {
      block |= ((uint32_t)data[i + 1]) << 8;
    }
    if (hasThird)
    {
      block |= ((uint32_t)data[i + 2]);
    }

    out += kTable[(block >> 18) & 0x3F];
    out += kTable[(block >> 12) & 0x3F];
    out += hasSecond ? kTable[(block >> 6) & 0x3F] : '=';
    out += hasThird ? kTable[block & 0x3F] : '=';
  }

  return true;
}

bool ensureMicBuffer()
{
  if (micPcmBuffer)
  {
    return true;
  }

  size_t bytesNeeded = MIC_MAX_SAMPLES * sizeof(int16_t);
  size_t psramTotal = heap_caps_get_total_size(MALLOC_CAP_SPIRAM);
  bool triedPsram = false;

  if (MIC_PREFER_PSRAM && psramTotal > 0)
  {
    triedPsram = true;
    micPcmBuffer = reinterpret_cast<int16_t *>(heap_caps_malloc(bytesNeeded, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
  }

  if (!micPcmBuffer && MIC_ALLOW_INTERNAL_HEAP_FALLBACK)
  {
    micPcmBuffer = reinterpret_cast<int16_t *>(heap_caps_malloc(bytesNeeded, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT));
  }

  if (!micPcmBuffer)
  {
    if (MIC_PREFER_PSRAM && !MIC_ALLOW_INTERNAL_HEAP_FALLBACK)
    {
      if (psramTotal == 0)
      {
        notifyMessage("ERR:REC:NO_PSRAM");
        updateDisplay("Recording", "PSRAM required");
      }
      else if (triedPsram)
      {
        notifyMessage("ERR:REC:NO_PSRAM_BUF");
        updateDisplay("Recording", "PSRAM alloc fail");
      }
      else
      {
        notifyMessage("ERR:REC:NO_BUF");
        updateDisplay("Recording", "No RAM buffer");
      }
    }
    else
    {
      notifyMessage("ERR:REC:NO_BUF");
      updateDisplay("Recording", "No RAM buffer");
    }
    logMemorySnapshot("mic_alloc_fail");
    return false;
  }

  notifyMessage((MIC_PREFER_PSRAM && psramTotal > 0) ? "MSG:REC:BUF_PSRAM" : "MSG:REC:BUF_HEAP");
  return true;
}

void releaseMicBuffer()
{
  if (micPcmBuffer)
  {
    free(micPcmBuffer);
    micPcmBuffer = nullptr;
  }
}

int32_t centerMicSamplesAndMeasurePeak(size_t sampleCount)
{
  if (!micPcmBuffer || sampleCount == 0)
  {
    return 0;
  }

  int64_t sum = 0;
  for (size_t i = 0; i < sampleCount; ++i)
  {
    sum += micPcmBuffer[i];
  }

  int32_t dcOffset = (int32_t)(sum / (int64_t)sampleCount);
  int32_t peak = 0;

  for (size_t i = 0; i < sampleCount; ++i)
  {
    int32_t centered = (int32_t)micPcmBuffer[i] - dcOffset;
    if (centered > 32767)
    {
      centered = 32767;
    }
    else if (centered < -32768)
    {
      centered = -32768;
    }

    micPcmBuffer[i] = (int16_t)centered;
    int32_t absVal = centered >= 0 ? centered : -centered;
    if (absVal > peak)
    {
      peak = absVal;
    }
  }

  return peak;
}

void startMicRecording()
{
#if USE_I2S_MIC_MODULE
  if (!micReady)
  {
    setupMicInput();
  }
  if (!micReady)
  {
    notifyMessage("ERR:REC:MIC_NOT_READY");
    return;
  }
  if (isRecording)
  {
    notifyMessage("EVT:REC:ALREADY");
    return;
  }
  if (!ensureMicBuffer())
  {
    return;
  }

  micRecordedSamples = 0;
  micRecordingStartMs = millis();
  isRecording = true;
  i2s_zero_dma_buffer(I2S_NUM_0);
  updateDisplay("Recording", "Auto-send at 5s");
  notifyMessage("EVT:REC:START");
#else
  notifyMessage("ERR:REC:DISABLED");
#endif
}

void stopAndSendRecording(const String &source)
{
#if USE_I2S_MIC_MODULE
  if (!isRecording)
  {
    notifyMessage("EVT:REC:NOT_ACTIVE");
    return;
  }
  if (!micPcmBuffer)
  {
    notifyMessage("ERR:REC:NO_BUF");
    isRecording = false;
    return;
  }

  isRecording = false;

  if (micRecordedSamples < (MIC_SAMPLE_RATE / 10))
  {
    notifyMessage("ERR:REC:TOO_SHORT");
    updateDisplay("Recording", "Too short");
    releaseMicBuffer();
    return;
  }

  int32_t signalPeak = centerMicSamplesAndMeasurePeak(micRecordedSamples);
  if (signalPeak < 220)
  {
    notifyMessage("WARN:REC:LOW_SIGNAL");
  }

  size_t pcmBytes = micRecordedSamples * sizeof(int16_t);
  size_t b64Len = ((pcmBytes + 2) / 3) * 4;

  String payload;
  if (!payload.reserve(b64Len + 220))
  {
    notifyMessage("ERR:REC:NO_MEM");
    releaseMicBuffer();
    return;
  }

  payload = "{\"audio_base64\":\"";
  if (!appendBase64(payload, reinterpret_cast<const uint8_t *>(micPcmBuffer), pcmBytes))
  {
    notifyMessage("ERR:REC:B64");
    releaseMicBuffer();
    return;
  }
  releaseMicBuffer();
  payload += "\",\"mode\":\"quick\",\"client\":\"";
  payload += source;
  payload += "\",\"metadata\":{\"audio_format\":\"pcm_s16le\",\"sample_rate\":";
  payload += String(MIC_SAMPLE_RATE);
  payload += ",\"sample_width\":2,\"channels\":1,\"endian\":\"little\",\"signal_peak\":";
  payload += String(signalPeak);
  payload += ",\"sample_count\":";
  payload += String((unsigned int)micRecordedSamples);
  payload += "}}";

  updateDisplay("Sending", "Audio to backend");
  notifyMessage("EVT:REC:SEND");

  String response;
  bool ok = sendProcessPayload(payload, response);
  if (!ok)
  {
    notifyMessage("ERR:SERVER");
    notifyMessage("ERR:HTTP:" + String(lastBackendHttpCode));
    if (lastBackendError.length() > 0)
    {
      notifyMessage("ERR:DETAIL:" + lastBackendError);
    }
    updateDisplay("Server", "Audio send failed");
    return;
  }

  String responseText = parseJsonStringField(response, "text");
  String ttsUrl = parseJsonStringField(response, "tts_url");
  if (responseText.length() == 0)
  {
    responseText = response;
  }
  notifyMessage("TTS:" + responseText);
  speakText(responseText);
  if (ttsUrl.length() > 0)
  {
    notifyMessage("TTS_URL:" + ttsUrl);
    if (!fetchAndPlayTtsFromUrl(ttsUrl))
    {
      notifyMessage("ERR:TTS_PLAYBACK");
    }
  }
#else
  (void)source;
#endif
}

void tickMicRecording()
{
#if USE_I2S_MIC_MODULE
  if (!isRecording || !micReady || !micPcmBuffer)
  {
    return;
  }

  size_t remaining = MIC_MAX_SAMPLES - micRecordedSamples;
  if (remaining == 0)
  {
    notifyMessage("EVT:REC:MAXLEN");
    stopAndSendRecording("esp32_touch");
    return;
  }

  size_t chunkSamples = remaining;
  if (chunkSamples > MIC_READ_CHUNK_SAMPLES)
  {
    chunkSamples = MIC_READ_CHUNK_SAMPLES;
  }

  size_t bytesRead = 0;
  static uint8_t readErrorBursts = 0;
  esp_err_t err = i2s_read(
      I2S_NUM_0,
      reinterpret_cast<void *>(micPcmBuffer + micRecordedSamples),
      chunkSamples * sizeof(int16_t),
      &bytesRead,
      pdMS_TO_TICKS(20));

  if (err == ESP_OK && bytesRead > 0)
  {
    micRecordedSamples += (bytesRead / sizeof(int16_t));
    readErrorBursts = 0;
  }
  else if (err != ESP_OK)
  {
    if (readErrorBursts < 3)
    {
      notifyMessage("ERR:REC:I2S_READ");
    }
    readErrorBursts++;
  }

  if (micRecordedSamples >= MIC_MAX_SAMPLES)
  {
    notifyMessage("EVT:REC:MAXLEN");
    stopAndSendRecording("esp32_touch");
  }
#endif
}

void toggleOperationMode()
{
#if ENABLE_BLE_BRIDGE
  currentMode = (currentMode == MODE_WIFI_DIRECT) ? MODE_PHONE_RELAY : MODE_WIFI_DIRECT;
  notifyMessage(currentMode == MODE_WIFI_DIRECT ? "MODE:WIFI" : "MODE:PHONE");
#else
  currentMode = MODE_WIFI_DIRECT;
  notifyMessage("ERR:BLE:DISABLED");
  notifyMessage("MODE:WIFI");
#endif
}

String normalizeProcessPayload(String body)
{
  body.replace("\"audio\"", "\"audio_base64\"");
  body.replace("\"image\"", "\"image_base64\"");
  body.replace("\"prompt\"", "\"text\"");

  if (body.indexOf("\"client\"") < 0)
  {
    int closePos = body.lastIndexOf('}');
    if (closePos > 0)
    {
      String prefix = body.substring(0, closePos);
      if (!prefix.endsWith("{"))
      {
        prefix += ",";
      }
      body = prefix + "\"client\":\"esp32_wifi\"}";
    }
  }
  if (body.indexOf("\"mode\"") < 0)
  {
    int closePos = body.lastIndexOf('}');
    if (closePos > 0)
    {
      String prefix = body.substring(0, closePos);
      if (!prefix.endsWith("{"))
      {
        prefix += ",";
      }
      body = prefix + "\"mode\":\"quick\"}";
    }
  }

  return body;
}

bool sendProcessPayload(const String &payload, String &response)
{
  if (WiFi.status() != WL_CONNECTED)
  {
    connectToWiFi();
  }
  if (WiFi.status() != WL_CONNECTED)
  {
    serverConnected = false;
    lastBackendHttpCode = -2;
    lastBackendError = "WIFI_DISCONNECTED";
    return false;
  }

  HTTPClient http;
  http.begin(String(SERVER_URL));
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(payload);
  response = (code > 0) ? http.getString() : "{\"error\":\"HTTP_FAILED\"}";
  http.end();

  lastBackendHttpCode = code;
  if (code == 200)
  {
    lastBackendError = "";
  }
  else
  {
    lastBackendError = response;
    if (lastBackendError.length() > 180)
    {
      lastBackendError = lastBackendError.substring(0, 180);
    }
  }

  serverConnected = (code == 200);
  return code == 200;
}

void processTextCommand(const String &text, const String &source)
{
  String prompt = text;
  prompt.trim();
  if (prompt.length() == 0)
  {
    notifyMessage("ERR:TXT:EMPTY");
    return;
  }
  lastPrompt = prompt;

  if (currentMode == MODE_PHONE_RELAY)
  {
#if ENABLE_BLE_BRIDGE
    notifyMessage("CMD:" + prompt);
#else
    currentMode = MODE_WIFI_DIRECT;
    notifyMessage("ERR:BLE:DISABLED");
#endif
    return;
  }

  String payload = "{\"text\":\"" + escapeJson(prompt) + "\",\"mode\":\"quick\",\"client\":\"" + source + "\"}";
  String response;
  bool ok = sendProcessPayload(payload, response);
  if (!ok)
  {
    notifyMessage("ERR:SERVER");
    notifyMessage("ERR:HTTP:" + String(lastBackendHttpCode));
    if (lastBackendError.length() > 0)
    {
      notifyMessage("ERR:DETAIL:" + lastBackendError);
    }
    notifyMessage("CMD:" + prompt);
    return;
  }

  String responseText = parseJsonStringField(response, "text");
  String ttsUrl = parseJsonStringField(response, "tts_url");
  if (responseText.length() == 0)
  {
    responseText = response;
  }
  notifyMessage("TTS:" + responseText);
  speakText(responseText);
  if (ttsUrl.length() > 0)
  {
    notifyMessage("TTS_URL:" + ttsUrl);
    if (!fetchAndPlayTtsFromUrl(ttsUrl))
    {
      notifyMessage("ERR:TTS_PLAYBACK");
    }
  }
}

void handleCommand(const String &cmd, const String &source)
{
  if (cmd == "PING")
  {
    notifyMessage("PONG");
    return;
  }
  if (cmd == "MODE?")
  {
    notifyMessage(currentMode == MODE_WIFI_DIRECT ? "MODE:WIFI" : "MODE:PHONE");
    return;
  }
  if (cmd == "MODE:WIFI")
  {
    currentMode = MODE_WIFI_DIRECT;
    notifyMessage("ACK:MODE:WIFI");
    return;
  }
  if (cmd == "MODE:PHONE")
  {
#if ENABLE_BLE_BRIDGE
    currentMode = MODE_PHONE_RELAY;
    notifyMessage("ACK:MODE:PHONE");
#else
    currentMode = MODE_WIFI_DIRECT;
    notifyMessage("ERR:BLE:DISABLED");
#endif
    return;
  }
  if (cmd.startsWith("TXT:"))
  {
    processTextCommand(cmd.substring(4), source);
    return;
  }
  if (cmd.startsWith("TTS:"))
  {
    String responseText = cmd.substring(4);
    responseText.trim();
    if (responseText.length() == 0)
    {
      notifyMessage("ERR:TTS:EMPTY");
      return;
    }
    speakText(responseText);
    notifyMessage("ACK:TTS");
    return;
  }
  if (cmd.startsWith("TTS_URL:"))
  {
    String ttsUrl = cmd.substring(8);
    ttsUrl.trim();
    if (ttsUrl.length() == 0)
    {
      notifyMessage("ERR:TTS_URL:EMPTY");
      return;
    }
    bool ok = fetchAndPlayTtsFromUrl(ttsUrl);
    notifyMessage(ok ? "ACK:TTS_URL" : "ERR:TTS_URL");
    return;
  }
  if (cmd.startsWith("OLED:"))
  {
    updateDisplay("Phone", cmd.substring(5));
    notifyMessage("ACK:OLED");
    return;
  }
  if (cmd == "CAM:SNAP")
  {
    String responseText;
    if (captureAndAnalyzeCamera("Describe what you see", source, responseText))
    {
      notifyMessage("ACK:CAM:SNAP");
    }
    return;
  }
  if (cmd.startsWith("CAM:SNAP:"))
  {
    String prompt = cmd.substring(9);
    prompt.trim();
    if (prompt.length() == 0)
    {
      prompt = "Describe what you see";
    }
    String responseText;
    if (captureAndAnalyzeCamera(prompt, source, responseText))
    {
      notifyMessage("ACK:CAM:SNAP");
    }
    return;
  }

  processTextCommand(cmd, source);
}

void handleSerialInput()
{
  static char serialBuf[256];
  static size_t serialLen = 0;

  while (Serial.available() > 0)
  {
    char c = (char)Serial.read();
    if (c == '\r')
    {
      continue;
    }
    if (c == '\n')
    {
      serialBuf[serialLen] = '\0';
      if (serialLen > 0)
      {
        handleCommand(String(serialBuf), "esp32_serial");
      }
      serialLen = 0;
      continue;
    }
    if (serialLen < sizeof(serialBuf) - 1)
    {
      serialBuf[serialLen++] = c;
    }
  }
}

// ============== WIFI ==============
void connectToWiFi()
{
  Serial.println("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20)
  {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.println("\nWiFi connected!");
    serverConnected = true;
  }
  else
  {
    Serial.println("\nWiFi failed!");
    serverConnected = false;
  }
}

// ============== HANDLERS ==============
void handleRoot()
{
  server.send(200, "text/html; charset=utf-8", INDEX_HTML);
}

void handleStatus()
{
  String mode = currentMode == MODE_WIFI_DIRECT ? "WIFI" : "PHONE";
  String json = "{\"status\":\"ok\",\"server\":" + String(serverConnected ? "true" : "false") + ",\"mode\":\"" + mode + "\",\"ble_enabled\":" + String(ENABLE_BLE_BRIDGE ? "true" : "false") + ",\"last_http_code\":" + String(lastBackendHttpCode) + "}";
  server.send(200, "application/json", json);
}

void handleProcess()
{
  if (server.hasArg("plain"))
  {
    String body = normalizeProcessPayload(server.arg("plain"));
    String resp = "{}";
    bool ok = sendProcessPayload(body, resp);

    Serial.println("Response: " + resp);
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    server.send(ok ? 200 : 502, "application/json", resp);
  }
  else
  {
    server.send(400, "text/plain", "No data");
  }
}

void handleCommandRoute()
{
  if (!server.hasArg("plain"))
  {
    server.send(400, "application/json", "{\"error\":\"missing_body\"}");
    return;
  }

  String body = server.arg("plain");
  String command = parseJsonStringField(body, "command");
  if (command.length() == 0)
  {
    server.send(400, "application/json", "{\"error\":\"missing_command\"}");
    return;
  }

  handleCommand(command, "esp32_web");
  server.send(200, "application/json", "{\"ok\":true}");
}

void handleCameraStatus()
{
  String json = "{\"enabled\":" + String(USE_CAMERA ? "true" : "false") +
                ",\"ready\":" + String(cameraReady ? "true" : "false") +
                ",\"last_error\":\"" + escapeJson(cameraLastError) + "\"}";
  server.send(200, "application/json", json);
}

void handleCameraAnalyzeRoute()
{
  String prompt = "Describe what you see";
  if (server.hasArg("plain"))
  {
    String body = server.arg("plain");
    String parsedPrompt = parseJsonStringField(body, "prompt");
    if (parsedPrompt.length() > 0)
    {
      prompt = parsedPrompt;
    }
  }

  String responseText;
  bool ok = captureAndAnalyzeCamera(prompt, "esp32_camera", responseText);
  if (!ok)
  {
    String errJson = "{\"ok\":false,\"error\":\"camera_analyze_failed\",\"http\":" + String(lastBackendHttpCode) + "}";
    server.send(502, "application/json", errJson);
    return;
  }

  String json = "{\"ok\":true,\"text\":\"" + escapeJson(responseText) + "\"}";
  server.send(200, "application/json", json);
}

void handleNotFound()
{
  server.send(404, "text/plain", "Not Found");
}

const char *resetReasonToText(esp_reset_reason_t reason)
{
  switch (reason)
  {
  case ESP_RST_POWERON:
    return "POWERON";
  case ESP_RST_EXT:
    return "EXTERNAL_PIN";
  case ESP_RST_SW:
    return "SOFTWARE";
  case ESP_RST_PANIC:
    return "PANIC";
  case ESP_RST_INT_WDT:
    return "INT_WDT";
  case ESP_RST_TASK_WDT:
    return "TASK_WDT";
  case ESP_RST_WDT:
    return "WDT_OTHER";
  case ESP_RST_DEEPSLEEP:
    return "DEEPSLEEP";
  case ESP_RST_BROWNOUT:
    return "BROWNOUT";
  case ESP_RST_SDIO:
    return "SDIO";
  default:
    return "UNKNOWN";
  }
}

// ============== SETUP ==============
void setup()
{
  Serial.begin(115200);
  delay(150);
  Serial.println("\n=== Smart Glasses ===");
  esp_reset_reason_t rr = esp_reset_reason();
  Serial.printf("RESET_REASON: %s (%d)\n", resetReasonToText(rr), (int)rr);
  Serial.printf("FREE_HEAP_BOOT: %u\n", (unsigned int)ESP.getFreeHeap());
  Serial.printf("PROFILE_FLAGS OLED=%d MIC=%d DAC_TTS=%d BLE=%d\n",
                USE_SH1106,
                USE_I2S_MIC_MODULE,
                USE_DAC_TTS_MODULE,
                ENABLE_BLE_BRIDGE);
  Serial.printf("PROFILE_FLAGS CAMERA=%d TOUCH=%d\n", USE_CAMERA, USE_TOUCH);
  logMemorySnapshot("boot");
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
#if USE_TOUCH
  pinMode(TOUCH_PAD_PIN, INPUT_PULLDOWN);
#endif
#if USE_SH1106
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
#endif

#if USE_SH1106
  gDisplay.begin();
#endif
#if USE_DAC_TTS_MODULE
  setupTtsAudio();
#endif
#if USE_CAMERA
  setupCameraInput();
#endif
  updateDisplay("Boot", "Starting...");

#if ENABLE_BLE_BRIDGE
  BLEDevice::init("Smart Glasses");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());
  BLEService *pService = pServer->createService(SERVICE_UUID);
  gCharacteristic = pService->createCharacteristic(
      CHARACTERISTIC_UUID,
      BLECharacteristic::PROPERTY_NOTIFY | BLECharacteristic::PROPERTY_WRITE);
  gCharacteristic->addDescriptor(new BLE2902());
  gCharacteristic->setCallbacks(new CharacteristicCallbacks());
  pService->start();
  BLEDevice::startAdvertising();
  Serial.println("BLE advertising started");
#else
  Serial.println("BLE bridge disabled at compile time");
#endif

  WiFi.mode(WIFI_AP_STA);
  WiFi.softAPConfig(AP_IP, AP_GATEWAY, AP_SUBNET);
  WiFi.softAP(AP_SSID, AP_PASSWORD);
  Serial.println("AP: " + String(AP_SSID) + " IP: 192.168.4.1");
  updateDisplay("Boot", "AP ready");

  connectToWiFi();

  server.on("/", handleRoot);
  server.on("/status", handleStatus);
  server.on("/process", HTTP_POST, handleProcess);
  server.on("/command", HTTP_POST, handleCommandRoute);
  server.on("/camera/status", HTTP_GET, handleCameraStatus);
  server.on("/camera/analyze", HTTP_POST, handleCameraAnalyzeRoute);
  server.onNotFound(handleNotFound);
  server.begin();
  Serial.println("Server started");
  updateDisplay("Ready", serverConnected ? "WiFi+AP" : "AP only");
  logMemorySnapshot("ready");
  Serial.println("Touch mode: double-tap=start, tap=stop/send, long-press=toggle mode");
}

// ============== LOOP ==============
void loop()
{
  server.handleClient();
  handleSerialInput();
  tickDisplayScroll();
  tickMicRecording();

#if ENABLE_BLE_BRIDGE
  if (bleConnectEvent)
  {
    bleConnectEvent = false;
    Serial.println("BLE client connected");
  }
  if (bleDisconnectEvent)
  {
    bleDisconnectEvent = false;
    Serial.println("BLE client disconnected");
    BLEDevice::startAdvertising();
  }
  if (pendingBleCommandReady)
  {
    char localCmd[sizeof(pendingBleCommand)];
    localCmd[0] = '\0';
    portENTER_CRITICAL(&bleMux);
    strncpy(localCmd, pendingBleCommand, sizeof(localCmd));
    localCmd[sizeof(localCmd) - 1] = '\0';
    pendingBleCommand[0] = '\0';
    pendingBleCommandReady = false;
    portEXIT_CRITICAL(&bleMux);
    handleCommand(String(localCmd), "esp32_ble");
  }
#endif

  bool touch2 = false;
#if USE_TOUCH
  touch2 = digitalRead(TOUCH_PAD_PIN) == HIGH;
#endif

  if (touch2 && !lastTouch2)
  {
    touch2PressStartMs = millis();
  }

  if (!touch2 && lastTouch2)
  {
    unsigned long heldMs = millis() - touch2PressStartMs;
    if (heldMs >= TOUCH2_LONG_PRESS_MS)
    {
      toggleOperationMode();
      lastTouch2TapMs = 0;
    }
    else
    {
      unsigned long nowMs = millis();
      if (isRecording)
      {
        stopAndSendRecording("esp32_touch");
        lastTouch2TapMs = 0;
      }
      else
      {
        if (lastTouch2TapMs > 0 && (nowMs - lastTouch2TapMs) <= TOUCH2_DOUBLE_TAP_MS)
        {
          notifyMessage("EVT:TOUCH2:START_REC");
          startMicRecording();
          lastTouch2TapMs = 0;
        }
        else
        {
          lastTouch2TapMs = nowMs;
          notifyMessage("EVT:TOUCH2:WAIT_DOUBLE");
          updateDisplay("Ready", "Tap again to rec");
        }
      }
    }
  }
  lastTouch2 = touch2;

  if (!isRecording && lastTouch2TapMs > 0 && (millis() - lastTouch2TapMs) > TOUCH2_DOUBLE_TAP_MS)
  {
    lastTouch2TapMs = 0;
  }

  static unsigned long last = 0;
  if (millis() - last > 1000)
  {
    last = millis();
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }

  delay(2);
}
