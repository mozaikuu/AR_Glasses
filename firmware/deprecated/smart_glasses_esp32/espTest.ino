/**
 * Smart Glasses ESP32 - Phone Peripheral Test Firmware
 *
 * This firmware allows testing audio/camera functionality using
 * the phone's microphone and camera as input sources via BLE.
 *
 * COMMUNICATION PROTOCOL (via BLE GATT):
 *
 * PHONE -> ESP32:
 *   "AUD:<base64_audio_data>"     - Send microphone audio to ESP32
 *   "IMG:<base64_image_data>"     - Send camera frame to ESP32
 *   "TXT:<command>"                - Send text command (existing)
 *   "PING"                         - Ping ESP32
 *
 * ESP32 -> PHONE:
 *   "TTS:<text_response>"         - Text-to-speech output (phone plays)
 *   "VID:<base64_video_frame>"     - Video frame to display on phone
 *   "ACK:<command>"                - Acknowledgment
 *   "PONG"                         - Pong response
 *   "EVT:<event>:<value>"         - Events (TOUCH, etc.)
 *   "ERR:<error_message>"          - Error messages
 *
 * HARDWARE:
 *   - ESP32 (any variant with BLE)
 *   - OLED Display (SH1106 128x64) - optional, for status
 *   - Touch sensors - optional
 *
 * CONNECTIONS (if using hardware):
 *   I2C OLED: SDA=21, SCL=22
 *   Touch1: GPIO 5
 *   Touch2: GPIO 18
 *   LED: GPIO 2
 */

#include <Arduino.h>
#include <Wire.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLECharacteristic.h>
#include <BLE2902.h>
#include <cstring>
#include <WiFi.h>
#include <HTTPClient.h>

// ============== CONFIGURATION ==============
#define USE_SH1106 1
#define USE_TOUCH 1
#define USE_WIFI 1

// BLE identifiers
#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

// Device name advertised over BLE
#define DEVICE_NAME "SmartGlasses-Test"

// Hardware pins
#define LED_PIN 2
#define TOUCH1_PIN 5
#define TOUCH2_PIN 18
#define TOUCH_ACTIVE_LEVEL HIGH
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22

// WiFi config (for backend processing)
const char *WIFI_SSID = "Moussa24";
const char *WIFI_PASSWORD = "AhmedMoussa2003!";
const char *SERVER_PROCESS_URL = "http://192.168.100.2:8000/esp/process";

// Display config
const uint16_t OLED_MAX_CHARS_PER_LINE = 21;
const uint16_t OLED_MAX_LINES = 3;
const unsigned long OLED_SCROLL_INTERVAL_MS = 120;

// ============== GLOBAL VARIABLES ==============
bool deviceConnected = false;
BLECharacteristic *pCharacteristic = nullptr;
bool lastTouch1 = false;
bool lastTouch2 = false;
volatile bool bleConnectEvent = false;
volatile bool bleDisconnectEvent = false;

char pendingCommand[512] = {0};
volatile bool pendingCommandReady = false;
portMUX_TYPE bleMux = portMUX_INITIALIZER_UNLOCKED;

// Display state
String displayLine1Cache = "";
String displayLine2Cache = "";
String displayScrollBuffer = "";
size_t displayScrollOffset = 0;
bool displayScrollEnabled = false;
unsigned long lastDisplayScrollMs = 0;

// Audio/Video test state
bool audioTestMode = false;
bool videoTestMode = false;
unsigned long lastAudioPacketMs = 0;
unsigned long lastVideoPacketMs = 0;
int audioPacketsReceived = 0;
int videoPacketsReceived = 0;

// ============== FORWARD DECLARATIONS ==============
void setupDisplay();
void setupTouch();
void setupWiFi();
void updateDisplay(const String &line1, const String &line2);
void setDisplayContent(const String &line1, const String &line2, bool resetScroll);
void renderDisplay();
void tickDisplayScroll();
void drawWrappedText(int x, int yStart, int maxCharsPerLine, int maxLines, const String &text);
void notifyMessage(const String &payload);
void handleCommand(const String &cmd);
void processAudioData(const String &base64Audio);
void processImageData(const String &base64Image);
void sendEvent(const String &eventName, int value);
void sendAudioToPhone(const String &text);
void sendVideoFrameToPhone();
void ensureWiFiConnected();
String escapeJson(const String &text);
String parseJsonStringField(const String &json, const String &key);
bool sendTextToServer(const String &text, String &responseOut, String &ttsUrlOut);
void processTextCommand(const String &userCommand);

// ============== BLE CALLBACKS ==============
class MyServerCallbacks : public BLEServerCallbacks
{
public:
  void onConnect(BLEServer *pServer) override
  {
    (void)pServer;
    deviceConnected = true;
    bleConnectEvent = true;
    Serial.println("Phone connected");
  }

  void onDisconnect(BLEServer *pServer) override
  {
    (void)pServer;
    deviceConnected = false;
    bleDisconnectEvent = true;
    Serial.println("Phone disconnected");
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
    cmd.toCharArray(pendingCommand, sizeof(pendingCommand));
    pendingCommandReady = true;
    portEXIT_CRITICAL(&bleMux);

    Serial.print("BLE RX: ");
    Serial.println(cmd.substring(0, 50)); // Print first 50 chars
  }
};

// ============== SETUP ==============
void setup()
{
  Serial.begin(115200);
  Serial.println("\n=== Smart Glasses Phone Test Firmware ===");
  Serial.println("Use phone's mic/camera as input sources");

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

// Setup touch sensors if enabled
#if USE_TOUCH
  pinMode(TOUCH1_PIN, INPUT);
  pinMode(TOUCH2_PIN, INPUT);
#endif

  // Setup I2C for OLED
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

#if USE_SH1106
  setupDisplay();
#endif

// Setup WiFi if enabled
#if USE_WIFI
  setupWiFi();
#endif

  // Setup BLE
  BLEDevice::init(DEVICE_NAME);
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);
  pCharacteristic = pService->createCharacteristic(
      CHARACTERISTIC_UUID,
      BLECharacteristic::PROPERTY_NOTIFY | BLECharacteristic::PROPERTY_WRITE);

  pCharacteristic->addDescriptor(new BLE2902());
  pCharacteristic->setCallbacks(new CharacteristicCallbacks());

  pService->start();
  BLEDevice::startAdvertising();

  Serial.println("BLE advertising started");
  Serial.println("Device name: " String(DEVICE_NAME));

  updateDisplay("BLE Test", "Waiting for phone...");
}

void setupDisplay()
{
#if USE_SH1106
#include <U8g2lib.h>
  U8G2_SH1106_128X64_NONAME_F_HW_I2C gDisplay(U8G2_R0, U8X8_PIN_NONE);
  gDisplay.begin();
  updateDisplay("SmartGlasses", "Phone Test Mode");
#endif
}

void setupWiFi()
{
  Serial.print("Connecting to WiFi...");
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
    Serial.println("WiFi connected");
  }
  else
  {
    Serial.println("WiFi connection failed");
  }
}

// ============== MAIN LOOP ==============
void loop()
{
  static unsigned long lastPollMs = 0;

  tickDisplayScroll();

  // Handle BLE connection events
  if (bleConnectEvent)
  {
    bleConnectEvent = false;
    digitalWrite(LED_PIN, HIGH);
    updateDisplay("Phone", "Connected!");
    notifyMessage("ACK:CONNECTED");
  }

  if (bleDisconnectEvent)
  {
    bleDisconnectEvent = false;
    digitalWrite(LED_PIN, LOW);
    updateDisplay("BLE", "Advertising...");
    BLEDevice::startAdvertising();

    // Reset test state
    audioTestMode = false;
    videoTestMode = false;
    audioPacketsReceived = 0;
    videoPacketsReceived = 0;
  }

  // Process incoming commands
  if (pendingCommandReady)
  {
    char localCmd[sizeof(pendingCommand)];
    localCmd[0] = '\0';
    portENTER_CRITICAL(&bleMux);
    strncpy(localCmd, pendingCommand, sizeof(localCmd));
    localCmd[sizeof(localCmd) - 1] = '\0';
    pendingCommand[0] = '\0';
    pendingCommandReady = false;
    portEXIT_CRITICAL(&bleMux);

    String cmd = String(localCmd);
    handleCommand(cmd);
  }

// Poll touch sensors
#if USE_TOUCH
  if (millis() - lastPollMs < 50)
  {
    delay(1);
    return;
  }
  lastPollMs = millis();

  bool touch1 = (digitalRead(TOUCH1_PIN) == TOUCH_ACTIVE_LEVEL);
  bool touch2 = (digitalRead(TOUCH2_PIN) == TOUCH_ACTIVE_LEVEL);

  if (touch1 != lastTouch1)
  {
    lastTouch1 = touch1;
    sendEvent("TOUCH1", touch1 ? 1 : 0);
    updateDisplay("Touch1", touch1 ? "Pressed" : "Released");
  }

  if (touch2 != lastTouch2)
  {
    lastTouch2 = touch2;
    sendEvent("TOUCH2", touch2 ? 1 : 0);
    updateDisplay("Touch2", touch2 ? "Pressed" : "Released");
  }
#endif

  // Debug: show stats periodically
  static unsigned long lastStatsMs = 0;
  if (millis() - lastStatsMs > 5000 && deviceConnected)
  {
    lastStatsMs = millis();
    if (audioTestMode || videoTestMode)
    {
      char stats[100];
      snprintf(stats, sizeof(stats), "AUD:%d VID:%d",
               audioPacketsReceived, videoPacketsReceived);
      Serial.println(stats);
    }
  }
}

// ============== COMMAND HANDLING ==============
void handleCommand(const String &cmd)
{
  Serial.print("Handling: ");
  Serial.println(cmd.substring(0, min(30, (int)cmd.length())));

  // Ping
  if (cmd == "PING")
  {
    notifyMessage("PONG");
    return;
  }

  // Query mode
  if (cmd == "MODE?")
  {
    notifyMessage("MODE:PHONE_TEST");
    return;
  }

  // Audio test start/stop
  if (cmd == "AUD:START")
  {
    audioTestMode = true;
    audioPacketsReceived = 0;
    lastAudioPacketMs = millis();
    notifyMessage("ACK:AUD_START");
    updateDisplay("Audio Test", "Receiving...");
    return;
  }

  if (cmd == "AUD:STOP")
  {
    audioTestMode = false;
    char ack[100];
    snprintf(ack, sizeof(ack), "ACK:AUD_STOP:%d", audioPacketsReceived);
    notifyMessage(ack);
    updateDisplay("Audio Test", "Stopped");
    return;
  }

  // Video test start/stop
  if (cmd == "VID:START")
  {
    videoTestMode = true;
    videoPacketsReceived = 0;
    lastVideoPacketMs = millis();
    notifyMessage("ACK:VID_START");
    updateDisplay("Video Test", "Receiving...");
    return;
  }

  if (cmd == "VID:STOP")
  {
    videoTestMode = false;
    char ack[100];
    snprintf(ack, sizeof(ack), "ACK:VID_STOP:%d", videoPacketsReceived);
    notifyMessage(ack);
    updateDisplay("Video Test", "Stopped");
    return;
  }

  // Audio data packet (base64 encoded)
  if (cmd.startsWith("AUD:"))
  {
    String audioData = cmd.substring(4);
    audioData.trim();

    if (audioTestMode)
    {
      audioPacketsReceived++;
      lastAudioPacketMs = millis();
      // In real implementation, decode and process audio
      // For now, just acknowledge
      if (audioPacketsReceived % 10 == 0)
      {
        char ack[50];
        snprintf(ack, sizeof(ack), "ACK:AUD:%d", audioPacketsReceived);
        notifyMessage(ack);
      }
    }
    else
    {
      notifyMessage("ERR:AUD_NOT_STARTED");
    }
    return;
  }

  // Image data packet (base64 encoded)
  if (cmd.startsWith("IMG:"))
  {
    String imageData = cmd.substring(4);
    imageData.trim();

    if (videoTestMode)
    {
      videoPacketsReceived++;
      lastVideoPacketMs = millis();
      // In real implementation, decode and process image
      if (videoPacketsReceived % 10 == 0)
      {
        char ack[50];
        snprintf(ack, sizeof(ack), "ACK:IMG:%d", videoPacketsReceived);
        notifyMessage(ack);
      }
    }
    else
    {
      notifyMessage("ERR:VID_NOT_STARTED");
    }
    return;
  }

  // Text commands (existing functionality)
  if (cmd.startsWith("TXT:"))
  {
    String userCommand = cmd.substring(4);
    userCommand.trim();
    if (userCommand.length() == 0)
    {
      notifyMessage("ERR:TXT:EMPTY");
      return;
    }
    processTextCommand(userCommand);
    return;
  }

  // TTS response from server
  if (cmd.startsWith("TTS:"))
  {
    String responseText = cmd.substring(4);
    responseText.trim();
    if (responseText.length() == 0)
    {
      notifyMessage("ERR:TTS:EMPTY");
      return;
    }
    // Send TTS to phone for playback
    sendAudioToPhone(responseText);
    notifyMessage("ACK:TTS");
    return;
  }

  // Request TTS from phone
  if (cmd.startsWith("TTS_REQUEST:"))
  {
    String text = cmd.substring(12);
    // Phone should speak this text
    notifyMessage("TTS_PHONE:" + text);
    return;
  }

  // Request video frame from phone
  if (cmd == "REQ_FRAME")
  {
    // Phone should capture and send a frame
    notifyMessage("REQ_FRAME_ACK");
    return;
  }

  // OLED display update
  if (cmd.startsWith("OLED:"))
  {
    String msg = cmd.substring(5);
    updateDisplay("Phone", msg);
    notifyMessage("ACK:OLED");
    return;
  }

  // Get test statistics
  if (cmd == "STATS?")
  {
    char stats[150];
    snprintf(stats, sizeof(stats),
             "STATS:AUD=%d,VID=%d,AUD_ACTIVE=%d,VID_ACTIVE=%d",
             audioPacketsReceived, videoPacketsReceived,
             audioTestMode ? 1 : 0, videoTestMode ? 1 : 0);
    notifyMessage(stats);
    return;
  }

  // Reset statistics
  if (cmd == "RESET_STATS")
  {
    audioPacketsReceived = 0;
    videoPacketsReceived = 0;
    notifyMessage("ACK:RESET_STATS");
    return;
  }

  notifyMessage("ERR:UNKNOWN_CMD");
}

// ============== SEND DATA TO PHONE ==============
void notifyMessage(const String &payload)
{
  Serial.println("BLE TX: " + payload);
  if (deviceConnected && pCharacteristic)
  {
    pCharacteristic->setValue(payload.c_str());
    pCharacteristic->notify();
  }
}

void sendEvent(const String &eventName, int value)
{
  notifyMessage("EVT:" + eventName + ":" + String(value));
}

// Send text-to-speech to phone for playback
void sendAudioToPhone(const String &text)
{
  Serial.print("TTS to phone: ");
  Serial.println(text);
  updateDisplay("TTS", text.substring(0, min(20, (int)text.length())));
  // In full implementation, this would include audio URL or base64 audio
  notifyMessage("TTS_REQUEST:" + text);
}

// Send video frame request to phone
void sendVideoFrameToPhone()
{
  notifyMessage("REQ_FRAME");
}

// ============== DATA PROCESSING (PLACEHOLDERS) ==============
void processAudioData(const String &base64Audio)
{
  // Placeholder: In real implementation, decode base64 and process
  Serial.print("Processing audio chunk, length: ");
  Serial.println(base64Audio.length());
}

void processImageData(const String &base64Image)
{
  // Placeholder: In real implementation, decode base64 and process
  Serial.print("Processing image chunk, length: ");
  Serial.println(base64Image.length());
}

// ============== SERVER COMMUNICATION ==============
void processTextCommand(const String &userCommand)
{
#if USE_WIFI
  String response;
  String ttsUrl;

  updateDisplay("Processing", "...");

  if (sendTextToServer(userCommand, response, ttsUrl))
  {
    // Send response to phone for TTS
    sendAudioToPhone(response);
    notifyMessage("ACK:TXT:" + response);
  }
  else
  {
    notifyMessage("ERR:SERVER");
    updateDisplay("Error", "Server failed");
  }
#else
  // No WiFi - just echo back
  String echo = "Echo: " + userCommand;
  sendAudioToPhone(echo);
  notifyMessage("ACK:TXT:" + echo);
#endif
}

bool sendTextToServer(const String &text, String &responseOut, String &ttsUrlOut)
{
  ensureWiFiConnected();

  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("WiFi not connected");
    return false;
  }

  HTTPClient http;
  http.begin(SERVER_PROCESS_URL);
  http.addHeader("Content-Type", "application/json");

  String jsonBody = "{\"text\":\"" + escapeJson(text) + "\"}";
  int httpCode = http.POST(jsonBody);

  if (httpCode == HTTP_CODE_OK)
  {
    String response = http.getString();
    http.end();

    // Parse JSON response
    responseOut = parseJsonStringField(response, "response");
    ttsUrlOut = parseJsonStringField(response, "tts_url");

    Serial.println("Server response: " + responseOut);
    return true;
  }
  else
  {
    Serial.println("HTTP error: " + String(httpCode));
    http.end();
    return false;
  }
}

void ensureWiFiConnected()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("Reconnecting WiFi...");
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20)
    {
      delay(500);
      attempts++;
    }
  }
}

String escapeJson(const String &text)
{
  String result = text;
  result.replace("\\", "\\\\");
  result.replace("\"", "\\\"");
  result.replace("\n", "\\n");
  result.replace("\r", "\\r");
  result.replace("\t", "\\t");
  return result;
}

String parseJsonStringField(const String &json, const String &key)
{
  String search = "\"" + key + "\"";
  int keyPos = json.indexOf(search);
  if (keyPos == -1)
    return "";

  int colonPos = json.indexOf(":", keyPos);
  if (colonPos == -1)
    return "";

  int valueStart = colonPos + 1;
  while (valueStart < json.length() && (json[valueStart] == ' ' || json[valueStart] == '\"'))
  {
    valueStart++;
  }

  int valueEnd = valueStart;
  while (valueEnd < json.length() && json[valueEnd] != '\"' && json[valueEnd] != ',' && json[valueEnd] != '}')
  {
    valueEnd++;
  }

  return json.substring(valueStart, valueEnd);
}

// ============== DISPLAY FUNCTIONS ==============
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
    for (uint16_t i = 0; i < 8; i++)
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
#include <U8g2lib.h>
  extern U8G2_SH1106_128X64_NONAME_F_HW_I2C gDisplay;

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
      size_t idx = displayScrollOffset + i;
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
    return;
  if (millis() - lastDisplayScrollMs < OLED_SCROLL_INTERVAL_MS)
    return;
  lastDisplayScrollMs = millis();

  displayScrollOffset += 2;
  const int maxCharsVisible = OLED_MAX_CHARS_PER_LINE * OLED_MAX_LINES;
  if (displayScrollOffset + maxCharsVisible >= displayScrollBuffer.length())
  {
    displayScrollOffset = 0;
  }
  renderDisplay();
#endif
}

void drawWrappedText(int x, int yStart, int maxCharsPerLine, int maxLines, const String &text)
{
#if USE_SH1106
#include <U8g2lib.h>
  extern U8G2_SH1106_128X64_NONAME_F_HW_I2C gDisplay;

  if (maxLines <= 0 || maxCharsPerLine <= 0)
    return;

  String remaining = text;
  remaining.trim();
  int y = yStart;

  for (int line = 0; line < maxLines; line++)
  {
    if (remaining.length() == 0)
      return;

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
      split = maxCharsPerLine;

    String lineStr = remaining.substring(0, split);
    gDisplay.drawUTF8(x, y, lineStr.c_str());

    remaining = remaining.substring(split);
    y += 10;
  }
#else
  (void)x;
  (void)yStart;
  (void)maxCharsPerLine;
  (void)maxLines;
  (void)text;
#endif
}
