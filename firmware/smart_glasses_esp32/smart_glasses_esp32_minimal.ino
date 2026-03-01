/**
 * Smart Glasses ESP32 Firmware - Minimal (Touch + OLED + BLE Bridge)
 *
 * Adds a microphone-free text loop for backend validation:
 * - Phone/nRF writes: "TXT:<command>"
 * - ESP notifies: "CMD:<command>"
 * - Phone app sends to server and writes back: "TTS:<response>"
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
#include "driver/i2s.h"

#define USE_SH1106 1
#define USE_I2S_MIC_MODULE 0

#if USE_SH1106
#include <U8g2lib.h>
U8G2_SH1106_128X64_NONAME_F_HW_I2C gDisplay(U8G2_R0, U8X8_PIN_NONE);
#endif

// BLE identifiers shared with mobile gateway.
#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

// Hardware pins.
#define LED_PIN 2
#define TOUCH1_PIN 5
#define TOUCH2_PIN 18
#define TOUCH_ACTIVE_LEVEL HIGH
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22
#define I2S_MIC_BCK 14
#define I2S_MIC_WS 15
#define I2S_MIC_DATA 4

enum OperationMode
{
  MODE_BLE_BRIDGE = 0,
  MODE_WIFI_DIRECT = 1
};

// Boot in Wi-Fi mode; BLE is used as backup when Wi-Fi/server is unavailable.
#define DEFAULT_OPERATION_MODE MODE_WIFI_DIRECT

// Wi-Fi + server config for direct mode.
const char *WIFI_SSID = "Moussa24";
const char *WIFI_PASSWORD = "AhmedMoussa2003!";
const char *SERVER_PROCESS_URL = "http://192.168.100.2:8000/process";

bool deviceConnected = false;
BLECharacteristic *pCharacteristic = nullptr;
bool lastTouch1 = false;
bool lastTouch2 = false;
volatile bool bleConnectEvent = false;
volatile bool bleDisconnectEvent = false;
char pendingCommand[196] = {0};
volatile bool pendingCommandReady = false;
portMUX_TYPE bleMux = portMUX_INITIALIZER_UNLOCKED;
OperationMode currentMode = DEFAULT_OPERATION_MODE;
unsigned long lastWiFiRetryMs = 0;
const unsigned long WIFI_RETRY_MS = 5000;

#if USE_I2S_MIC_MODULE
void setupAudio();
#endif
void sendEvent(const String &eventName, int value);
void notifyMessage(const String &payload);
void updateDisplay(const String &line1, const String &line2);
void handleCommand(const String &cmd);
void speakText(const String &text);
void setOperationMode(OperationMode nextMode);
void ensureWiFiConnected();
String escapeJson(const String &text);
String unescapeJson(const String &text);
String parseJsonStringField(const String &json, const String &key);
bool sendTextToServer(const String &text, String &responseOut);
void processTextCommand(const String &userCommand);
void handleSerialInput();
void handleSerialCommand(const String &cmd);

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
    cmd.toCharArray(pendingCommand, sizeof(pendingCommand));
    pendingCommandReady = true;
    portEXIT_CRITICAL(&bleMux);
  }
};

void setup()
{
  Serial.begin(115200);
  Serial.println("\n=== Smart Glasses Minimal (Touch/OLED/BLE) ===");

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  pinMode(TOUCH1_PIN, INPUT);
  pinMode(TOUCH2_PIN, INPUT);

  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

#if USE_SH1106
  gDisplay.begin();
#endif
  updateDisplay("Boot", "Starting...");

#if USE_I2S_MIC_MODULE
  setupAudio();
#endif

  BLEDevice::init("Smart Glasses");
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
  if (currentMode == MODE_WIFI_DIRECT)
  {
    setOperationMode(MODE_WIFI_DIRECT);
  }
  else
  {
    setOperationMode(MODE_BLE_BRIDGE);
  }
}

void loop()
{
  static unsigned long lastPollMs = 0;

  if (bleConnectEvent)
  {
    bleConnectEvent = false;
    digitalWrite(LED_PIN, HIGH);
    Serial.println("Phone connected");
    updateDisplay("BLE", "Connected");
  }

  if (bleDisconnectEvent)
  {
    bleDisconnectEvent = false;
    digitalWrite(LED_PIN, LOW);
    Serial.println("Phone disconnected");
    updateDisplay("BLE", "Advertising");
    BLEDevice::startAdvertising();
  }

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
    Serial.print("BLE RX: ");
    Serial.println(cmd);
    handleCommand(cmd);
  }

  handleSerialInput();

  if (currentMode == MODE_WIFI_DIRECT)
  {
    ensureWiFiConnected();
  }

  if (millis() - lastPollMs < 20)
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
}

void handleCommand(const String &cmd)
{
  if (cmd == "MODE?")
  {
    notifyMessage(currentMode == MODE_WIFI_DIRECT ? "MODE:WIFI" : "MODE:BLE");
    return;
  }

  if (cmd == "MODE:BLE")
  {
    setOperationMode(MODE_BLE_BRIDGE);
    notifyMessage("ACK:MODE:BLE");
    return;
  }

  if (cmd == "MODE:WIFI")
  {
    setOperationMode(MODE_WIFI_DIRECT);
    notifyMessage("ACK:MODE:WIFI");
    return;
  }

  if (cmd == "PING")
  {
    notifyMessage("PONG");
    return;
  }

  if (cmd.startsWith("OLED:"))
  {
    String msg = cmd.substring(5);
    updateDisplay("Phone", msg);
    notifyMessage("ACK:OLED");
    return;
  }

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

  notifyMessage("ERR:UNKNOWN_CMD");
}

void sendEvent(const String &eventName, int value)
{
  notifyMessage("EVT:" + eventName + ":" + String(value));
}

void notifyMessage(const String &payload)
{
  Serial.println(payload);
  if (deviceConnected && pCharacteristic)
  {
    pCharacteristic->setValue(payload.c_str());
    pCharacteristic->notify();
  }
}

void speakText(const String &text)
{
  // Placeholder for on-device TTS/audio playback integration.
  Serial.print("TTS RX: ");
  Serial.println(text);
  updateDisplay("Server says", text);
}

void updateDisplay(const String &line1, const String &line2)
{
#if USE_SH1106
  gDisplay.clearBuffer();
  gDisplay.setFont(u8g2_font_6x10_tr);
  gDisplay.drawStr(0, 14, line1.c_str());
  gDisplay.drawUTF8(0, 30, line2.c_str());
  gDisplay.sendBuffer();
#else
  Serial.print("[OLED] ");
  Serial.print(line1);
  Serial.print(" | ");
  Serial.println(line2);
#endif
}

void setOperationMode(OperationMode nextMode)
{
  currentMode = nextMode;
  if (currentMode == MODE_WIFI_DIRECT)
  {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.println("Mode set: WIFI_DIRECT");
    updateDisplay("Mode", "WIFI_DIRECT");
  }
  else
  {
    if (WiFi.status() == WL_CONNECTED)
    {
      WiFi.disconnect(true);
    }
    Serial.println("Mode set: BLE_BRIDGE");
    updateDisplay("Mode", "BLE_BRIDGE");
  }
}

void ensureWiFiConnected()
{
  if (WiFi.status() == WL_CONNECTED)
  {
    return;
  }

  if (millis() - lastWiFiRetryMs < WIFI_RETRY_MS)
  {
    return;
  }
  lastWiFiRetryMs = millis();
  Serial.println("WiFi reconnect...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

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

bool sendTextToServer(const String &text, String &responseOut)
{
  responseOut = "";
  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("ERR:WIFI:DISCONNECTED");
    return false;
  }

  HTTPClient http;
  http.begin(SERVER_PROCESS_URL);
  http.addHeader("Content-Type", "application/json");

  String payload = "{\"text\":\"" + escapeJson(text) + "\",\"mode\":\"quick\"}";
  int httpCode = http.POST(payload);
  if (httpCode <= 0)
  {
    Serial.print("ERR:HTTP:");
    Serial.println(http.errorToString(httpCode));
    http.end();
    return false;
  }

  String body = http.getString();
  http.end();
  responseOut = parseJsonStringField(body, "response");
  if (responseOut.length() == 0)
  {
    Serial.println("ERR:SERVER:BAD_RESPONSE");
    return false;
  }
  return true;
}

void processTextCommand(const String &userCommand)
{
  if (currentMode == MODE_WIFI_DIRECT)
  {
    updateDisplay("Ask", userCommand);
    String serverResponse;
    if (sendTextToServer(userCommand, serverResponse))
    {
      speakText(serverResponse);
      notifyMessage("ACK:SRV");
    }
    else
    {
      if (deviceConnected && pCharacteristic)
      {
        // Wi-Fi/server failed, so fall back to BLE bridge path.
        updateDisplay("WiFi fail", "BLE fallback");
        notifyMessage("CMD:" + userCommand);
      }
      else
      {
        notifyMessage("ERR:SERVER");
        updateDisplay("Server", "Failed");
      }
    }
    return;
  }

  updateDisplay("Queue CMD", userCommand);
  notifyMessage("CMD:" + userCommand);
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
        handleSerialCommand(String(serialBuf));
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

void handleSerialCommand(const String &cmd)
{
  String line = cmd;
  line.trim();
  if (line.length() == 0)
  {
    return;
  }

  if (line.startsWith("TXT:") || line.startsWith("MODE:") || line == "MODE?" || line == "PING" || line.startsWith("OLED:") || line.startsWith("TTS:"))
  {
    handleCommand(line);
    return;
  }

  // Convenience: raw serial text is treated as TXT:<text>.
  handleCommand("TXT:" + line);
}

#if USE_I2S_MIC_MODULE
void setupAudio()
{
  i2s_config_t i2s_config = {
      .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
      .sample_rate = 16000,
      .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
      .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
      .communication_format = I2S_COMM_FORMAT_I2S,
      .intr_alloc_flags = 0,
      .dma_buf_count = 4,
      .dma_buf_len = 256,
      .use_apll = false,
      .tx_desc_auto_clear = false,
      .fixed_mclk = 0};

  i2s_pin_config_t pin_config = {
      .bck_io_num = I2S_MIC_BCK,
      .ws_io_num = I2S_MIC_WS,
      .data_out_num = -1,
      .data_in_num = I2S_MIC_DATA};

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
  Serial.println("I2S mic init complete");
}
#endif
