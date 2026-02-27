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

bool deviceConnected = false;
BLECharacteristic *pCharacteristic = nullptr;
bool lastTouch1 = false;
bool lastTouch2 = false;

#if USE_I2S_MIC_MODULE
void setupAudio();
#endif
void sendEvent(const String &eventName, int value);
void notifyMessage(const String &payload);
void updateDisplay(const String &line1, const String &line2);
void handleCommand(const String &cmd);
void speakText(const String &text);

class MyServerCallbacks : public BLEServerCallbacks
{
public:
  void onConnect(BLEServer *pServer) override
  {
    (void)pServer;
    deviceConnected = true;
    digitalWrite(LED_PIN, HIGH);
    Serial.println("Phone connected");
    updateDisplay("BLE", "Connected");
    notifyMessage("ACK:BLE:CONNECTED");
  }

  void onDisconnect(BLEServer *pServer) override
  {
    (void)pServer;
    deviceConnected = false;
    digitalWrite(LED_PIN, LOW);
    BLEDevice::startAdvertising();
    Serial.println("Phone disconnected");
    updateDisplay("BLE", "Advertising");
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

    Serial.print("BLE RX: ");
    Serial.println(cmd);
    handleCommand(cmd);
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
  updateDisplay("BLE", "Advertising");
}

void loop()
{
  static unsigned long lastPollMs = 0;
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

    updateDisplay("Queue CMD", userCommand);
    notifyMessage("CMD:" + userCommand);
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
