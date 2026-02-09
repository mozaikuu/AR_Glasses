/**
 * Smart Glasses ESP32 Firmware - Minimal Version
 * For ESP32 with limited flash (1.3MB)
 *
 * Features:
 * - BLE communication with phone
 * - IMU sensor (MPU6050)
 * - I2S Microphone (PDM)
 * - Basic gesture recognition
 */

#include <Arduino.h>
#include <Wire.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLECharacteristic.h>
#include <BLE2902.h>

#include "driver/i2s.h"

// ==================== CONFIGURATION ====================

// Hardware pin definitions
// I2S Microphone (PDM)
#define I2S_MIC_BCK 14
#define I2S_MIC_WS 15
#define I2S_MIC_DATA 4

// IMU (MPU6050)
#define MPU6050_ADDR 0x68
#define SDA_PIN 33
#define SCL_PIN 32

// Vibration motor
#define MOTOR_PIN 13

// Status LED
#define LED_PIN 2

// BLE UUIDs
#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

// Audio
const int SAMPLE_RATE = 16000;
const int SAMPLE_BITS = 16;
const int RECORD_TIME_MS = 1000; // 1 second recording
int16_t *audio_buffer = nullptr;
int audio_samples = 0;

// BLE
bool deviceConnected = false;
BLECharacteristic *pCharacteristic = nullptr;

// State
enum SystemState
{
  STATE_IDLE,
  STATE_LISTENING,
  STATE_PROCESSING
};
SystemState currentState = STATE_IDLE;

// IMU
float accelX = 0, accelY = 0, accelZ = 0;

// Callbacks
std::function<void(String)> onCommandReceived = nullptr;
std::function<void(String, float)> onGestureDetected = nullptr;

// ==================== BLE CALLBACKS ====================

class MyServerCallbacks : public BLEServerCallbacks
{
public:
  void onConnect(BLEServer *pServer)
  {
    deviceConnected = true;
    Serial.println("Phone connected");
    digitalWrite(LED_PIN, HIGH);
  }
  void onDisconnect(BLEServer *pServer)
  {
    deviceConnected = false;
    Serial.println("Phone disconnected");
    digitalWrite(LED_PIN, LOW);
    BLEDevice::startAdvertising();
  }
};

// ==================== SETUP ====================

void setup()
{
  Serial.begin(115200);
  Serial.println("\n=== Smart Glasses ESP32 Minimal ===");

  // LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // IMU
  Wire.begin(SDA_PIN, SCL_PIN);
  Serial.println("IMU initialized");

  // Audio
  setupAudio();

  // BLE
  BLEDevice::init("Smart Glasses");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);
  pCharacteristic = pService->createCharacteristic(
      CHARACTERISTIC_UUID,
      BLECharacteristic::PROPERTY_NOTIFY | BLECharacteristic::PROPERTY_WRITE);
  pCharacteristic->addDescriptor(new BLE2902());
  pService->start();
  BLEDevice::startAdvertising();

  Serial.println("Setup complete!");
}

void setupAudio()
{
  i2s_config_t i2s_config = {
      .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
      .sample_rate = SAMPLE_RATE,
      .bits_per_sample = (i2s_bits_per_sample_t)SAMPLE_BITS,
      .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
      .communication_format = I2S_COMM_FORMAT_I2S,
      .dma_buf_count = 2,
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

  audio_samples = (SAMPLE_RATE * RECORD_TIME_MS) / 1000;
  audio_buffer = (int16_t *)malloc(audio_samples * sizeof(int16_t));
  Serial.println("Audio initialized");
}

// ==================== MAIN LOOP ====================

void loop()
{
  static unsigned long lastGestureCheck = 0;

  if (millis() - lastGestureCheck > 100)
  {
    lastGestureCheck = millis();
    checkGesture();
  }

  delay(10);
}

void checkGesture()
{
  float intensity = sqrt(accelX * accelX + accelY * accelY + accelZ * accelZ);

  if (intensity > 2.0 && onGestureDetected)
  {
    String gesture = "";
    if (accelY > 8.0)
      gesture = "forward";
    else if (accelY < -8.0)
      gesture = "backward";
    else if (accelX > 8.0)
      gesture = "right";
    else if (accelX < -8.0)
      gesture = "left";

    if (gesture != "")
    {
      onGestureDetected(gesture, intensity);
      playHaptic("short");
    }
  }
}

void playHaptic(const char *pattern)
{
  if (strcmp(pattern, "short") == 0)
  {
    digitalWrite(MOTOR_PIN, HIGH);
    delay(100);
    digitalWrite(MOTOR_PIN, LOW);
  }
}

void recordAndSend()
{
  if (!audio_buffer)
    return;

  size_t bytes_read = 0;
  i2s_read(I2S_NUM_0, audio_buffer, audio_samples * sizeof(int16_t), &bytes_read, portMAX_DELAY);

  if (deviceConnected && pCharacteristic)
  {
    pCharacteristic->setValue((uint8_t *)audio_buffer, bytes_read);
    pCharacteristic->notify();
  }
}

void onVoiceCommand(std::function<void(String)> callback)
{
  onCommandReceived = callback;
}

void onGesture(std::function<void(String, float)> callback)
{
  onGestureDetected = callback;
}
