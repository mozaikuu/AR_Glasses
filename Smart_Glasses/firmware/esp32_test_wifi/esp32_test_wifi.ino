/**
 * Smart Glasses ESP32 - Full Pipeline Test
 * Works with phone file upload (bypasses browser camera/mic issues)
 */

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#ifndef ENABLE_BLE_BRIDGE
#define ENABLE_BLE_BRIDGE 0
#endif

#if ENABLE_BLE_BRIDGE
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLECharacteristic.h>
#include <BLE2902.h>
#endif

#ifndef USE_SH1106
#define USE_SH1106 1
#endif

#ifndef USE_DAC_TTS_MODULE
#define USE_DAC_TTS_MODULE 1
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
#define TOUCH1_PIN 5
#define TOUCH2_PIN 18
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22
#define DAC_TTS_LEFT_PIN 25
#define DAC_TTS_RIGHT_PIN 26

const uint16_t OLED_MAX_CHARS_PER_LINE = 21;
const uint16_t OLED_MAX_LINES = 3;
const unsigned long OLED_SCROLL_INTERVAL_MS = 120;
const uint8_t OLED_SCROLL_STEP_CHARS = 2;
const uint16_t OLED_SCROLL_GAP_SPACES = 8;

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
bool lastTouch1 = false;
bool lastTouch2 = false;
String displayLine1Cache = "";
String displayLine2Cache = "";
String displayScrollBuffer = "";
size_t displayScrollOffset = 0;
bool displayScrollEnabled = false;
unsigned long lastDisplayScrollMs = 0;

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
void updateDisplay(const String &line1, const String &line2);
void setDisplayContent(const String &line1, const String &line2, bool resetScroll);
void renderDisplay();
void tickDisplayScroll();
void drawWrappedText(int x, int yStart, int maxCharsPerLine, int maxLines, const String &text);
bool fetchAndPlayTtsFromUrl(const String &ttsUrl);
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
    String cmd = characteristic->getValue();
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

void handleNotFound()
{
  server.send(404, "text/plain", "Not Found");
}

// ============== SETUP ==============
void setup()
{
  Serial.begin(115200);
  Serial.println("\n=== Smart Glasses ===");
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  pinMode(TOUCH1_PIN, INPUT);
  pinMode(TOUCH2_PIN, INPUT);
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

#if USE_SH1106
  gDisplay.begin();
#endif
#if USE_DAC_TTS_MODULE
  setupTtsAudio();
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

  connectToWiFi();

  server.on("/", handleRoot);
  server.on("/status", handleStatus);
  server.on("/process", HTTP_POST, handleProcess);
  server.on("/command", HTTP_POST, handleCommandRoute);
  server.onNotFound(handleNotFound);
  server.begin();
  Serial.println("Server started");
}

// ============== LOOP ==============
void loop()
{
  server.handleClient();
  handleSerialInput();
  tickDisplayScroll();

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

  bool touch1 = digitalRead(TOUCH1_PIN) == HIGH;
  bool touch2 = digitalRead(TOUCH2_PIN) == HIGH;
  if (touch1 && !lastTouch1)
  {
    if (lastPrompt.length() > 0)
    {
      handleCommand("TXT:" + lastPrompt, "esp32_touch");
    }
    else
    {
      notifyMessage("EVT:TOUCH1:NO_PROMPT");
    }
  }
  if (touch2 && !lastTouch2)
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
  lastTouch1 = touch1;
  lastTouch2 = touch2;

  static unsigned long last = 0;
  if (millis() - last > 1000)
  {
    last = millis();
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
}
