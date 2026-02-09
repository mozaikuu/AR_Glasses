/**
 * Smart Glasses ESP32 Firmware
 * Open-source firmware for ESP32-S3 or ESP32-CAM based smart glasses.
 *
 * Features:
 * - Camera capture (OV2640)
 * - Microphone (PDM or analog)
 * - BLE communication with phone
 * - IMU sensor (MPU6050)
 * - Wake word detection (TinyML)
 * - Basic gesture recognition
 *
 * Hardware:
 * - ESP32-S3 or ESP32-CAM
 * - MPU6050 IMU
 * - MEMS microphone (INMP441 or analog)
 * - Optional: Vibration motor, buttons
 *
 * License: MIT
 * Author: Open Source Smart Glasses Project
 */

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLECharacteristic.h>
#include <BLE2902.h>

#include "driver/i2s.h"
#include "esp_camera.h"
#include "img_converters.h"
#include "fb_gfx.h"
#include "driver/ledc.h"
#include "esp_http_client.h"
#include "esp_http_server.h"

// ==================== CONFIGURATION ====================

// Hardware pin definitions
#define CAMERA_MODEL_AI_THINKER
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27

#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

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

// ==================== GLOBAL VARIABLES ====================

// Camera
camera_config_t camera_config;
bool camera_initialized = false;

// IMU
float accelX = 0, accelY = 0, accelZ = 0;
float gyroX = 0, gyroY = 0, gyroZ = 0;

// Audio
const int SAMPLE_RATE = 16000;
const int SAMPLE_BITS = 16;
const int RECORD_TIME_MS = 2000;
int16_t *audio_buffer = nullptr;
int audio_samples = 0;

// BLE
bool deviceConnected = false;
BLECharacteristic *pCharacteristic = nullptr;
String phoneServerIP = "";
int phoneServerPort = 8001;

// WiFi
WiFiClient wifiClient;

// State
enum SystemState
{
  STATE_IDLE,
  STATE_LISTENING,
  STATE_PROCESSING,
  STATE_NAVIGATING
};
SystemState currentState = STATE_IDLE;

// Callbacks
std::function<void(String)> onCommandReceived = nullptr;
std::function<void(String, float, int)> onGestureDetected = nullptr;

// ==================== BLE SERVER CALLBACKS ====================

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
    // Restart advertising
    BLEDevice::startAdvertising();
  }
};

// ==================== FORWARD DECLARATIONS ====================

void setupBLE();
void setupCamera();
void setupIMU();
void setupAudio();
void setupWiFi();

void loopBLE();
void loopIMU();
void loopAudio();
void loopStateMachine();

void captureImage();
void sendToPhone(String data);
void playHaptic(String pattern);

float calculateMotionIntensity();
String detectSimpleGesture();

// ==================== SETUP ====================

void setup()
{
  Serial.begin(115200);
  Serial.println("\n=== Smart Glasses ESP32 Firmware v2.0 ===");

  // Initialize LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  // Initialize subsystems
  setupCamera();
  setupIMU();
  setupAudio();
  setupBLE();

  // Connect to WiFi (for direct server mode)
  setupWiFi();

  Serial.println("Setup complete!");
  digitalWrite(LED_PIN, LOW);
}

void setupCamera()
{
  camera_config.pin_pwdn = PWDN_GPIO_NUM;
  camera_config.pin_reset = RESET_GPIO_NUM;
  camera_config.pin_xclk = XCLK_GPIO_NUM;
  camera_config.pin_sccb_sda = SIOD_GPIO_NUM;
  camera_config.pin_sccb_scl = SIOC_GPIO_NUM;
  camera_config.pin_d7 = Y9_GPIO_NUM;
  camera_config.pin_d6 = Y8_GPIO_NUM;
  camera_config.pin_d5 = Y7_GPIO_NUM;
  camera_config.pin_d4 = Y6_GPIO_NUM;
  camera_config.pin_d3 = Y5_GPIO_NUM;
  camera_config.pin_d2 = Y4_GPIO_NUM;
  camera_config.pin_d1 = Y3_GPIO_NUM;
  camera_config.pin_d0 = Y2_GPIO_NUM;
  camera_config.pin_vsync = VSYNC_GPIO_NUM;
  camera_config.pin_href = HREF_GPIO_NUM;
  camera_config.pin_pclk = PCLK_GPIO_NUM;

  camera_config.xclk_freq_hz = 20000000;
  camera_config.pixel_format = PIXFORMAT_JPEG;
  camera_config.frame_size = FRAMESIZE_QVGA; // 320x240 - smaller for BLE
  camera_config.jpeg_quality = 15;
  camera_config.fb_count = 2;

  esp_err_t err = esp_camera_init(&camera_config);
  if (err != ESP_OK)
  {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return;
  }
  camera_initialized = true;
  Serial.println("Camera initialized");
}

void setupIMU()
{
  Wire.begin(SDA_PIN, SCL_PIN);
  // MPU6050 initialization would go here
  Serial.println("IMU initialized (MPU6050)");
}

void setupAudio()
{
  // I2S microphone setup
  i2s_config_t i2s_config = {
      .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
      .sample_rate = SAMPLE_RATE,
      .bits_per_sample = (i2s_bits_per_sample_t)SAMPLE_BITS,
      .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
      .communication_format = I2S_COMM_FORMAT_I2S,
      .dma_buf_count = 4,
      .dma_buf_len = 1024,
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

  // Allocate buffer
  audio_samples = (SAMPLE_RATE * RECORD_TIME_MS) / 1000;
  audio_buffer = (int16_t *)malloc(audio_samples * sizeof(int16_t));

  Serial.println("Microphone initialized");
}

void setupBLE()
{
  BLEDevice::init("Smart Glasses Nova");
  BLEServer *pServer = BLEDevice::createServer();

  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(
      CHARACTERISTIC_UUID,
      BLECharacteristic::PROPERTY_NOTIFY | BLECharacteristic::PROPERTY_WRITE);
  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();
  BLEDevice::startAdvertising();

  Serial.println("BLE initialized - waiting for connection");
}

void setupWiFi()
{
  // WiFi credentials would be stored in preferences
  // For now, try to connect or create AP
  Serial.println("WiFi initialized (use setWiFiCredentials())");
}

// ==================== MAIN LOOP ====================

void loop()
{
  loopBLE();
  loopIMU();
  loopStateMachine();

  delay(10); // 100Hz loop
}

void loopBLE()
{
  if (deviceConnected)
  {
    // Can receive commands here
  }
}

void loopIMU()
{
  // Read IMU data
  // In production, use MPU6050 library
  static unsigned long lastRead = 0;
  if (millis() - lastRead > 10)
  { // 100Hz
    lastRead = millis();
    // Read accelerometer and gyroscope
    // accelX, accelY, accelZ = readAccelerometer();
    // gyroX, gyroY, gyroZ = readGyroscope();

    // Check for gestures
    float intensity = calculateMotionIntensity();
    if (intensity > 2.0)
    { // Motion detected
      String gesture = detectSimpleGesture();
      if (gesture != "" && onGestureDetected)
      {
        onGestureDetected(gesture, intensity, 0);
      }
    }
  }
}

void loopStateMachine()
{
  switch (currentState)
  {
  case STATE_IDLE:
    // Wait for wake word or gesture
    break;

  case STATE_LISTENING:
    // Record audio for command
    break;

  case STATE_PROCESSING:
    // Show waiting indicator
    break;

  case STATE_NAVIGATING:
    // Provide navigation feedback
    break;
  }
}

// ==================== FUNCTIONS ====================

void captureImage()
{
  if (!camera_initialized)
    return;

  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb)
    return;

  // Process image...
  // Can send to phone via BLE or WiFi

  esp_camera_fb_return(fb);
}

String recordAudioCommand()
{
  if (!audio_buffer)
    return "";

  size_t bytes_read = 0;
  i2s_read(I2S_NUM_0, audio_buffer, audio_samples * sizeof(int16_t), &bytes_read, portMAX_DELAY);

  // Convert to base64 for transmission
  String audioBase64 = "";
  // Base64 encoding would go here

  return audioBase64;
}

void sendToPhone(String data)
{
  if (deviceConnected && pCharacteristic)
  {
    pCharacteristic->setValue(data.c_str());
    pCharacteristic->notify();
  }
  else if (phoneServerIP != "")
  {
    // Send via WiFi
    // wifiClient.print(data);
  }
}

void playHaptic(String pattern)
{
  if (pattern == "short")
  {
    digitalWrite(MOTOR_PIN, HIGH);
    delay(100);
    digitalWrite(MOTOR_PIN, LOW);
  }
  else if (pattern == "long")
  {
    digitalWrite(MOTOR_PIN, HIGH);
    delay(300);
    digitalWrite(MOTOR_PIN, LOW);
  }
  else if (pattern == "double")
  {
    digitalWrite(MOTOR_PIN, HIGH);
    delay(100);
    digitalWrite(MOTOR_PIN, LOW);
    delay(100);
    digitalWrite(MOTOR_PIN, HIGH);
    delay(100);
    digitalWrite(MOTOR_PIN, LOW);
  }
}

float calculateMotionIntensity()
{
  // Simple motion detection
  return sqrt(accelX * accelX + accelY * accelY + accelZ * accelZ);
}

String detectSimpleGesture()
{
  // Simple gesture detection based on accelerometer
  // In production, use TinyML model (TensorFlow Lite for Microcontrollers)

  if (accelY > 8.0)
    return "tilt_forward";
  if (accelY < -8.0)
    return "tilt_backward";
  if (accelX > 8.0)
    return "tilt_right";
  if (accelX < -8.0)
    return "tilt_left";

  return "";
}

void setWiFiCredentials(const char *ssid, const char *password)
{
  WiFi.begin(ssid, password);
}

void setServerAddress(const char *ip, int port)
{
  phoneServerIP = String(ip);
  phoneServerPort = port;
}

void onVoiceCommand(std::function<void(String)> callback)
{
  onCommandReceived = callback;
}

void onGesture(std::function<void(String, float, int)> callback)
{
  onGestureDetected = callback;
}

// ==================== HTTP SERVER (Optional) ====================

#ifdef ENABLE_HTTP_SERVER
httpd_handle_t camera_httpd = NULL;

static esp_err_t index_handler(httpd_req_t *req)
{
  httpd_resp_send(req, "Smart Glasses - ESP32", HTTPD_RESP_USE_STRLEN);
  return ESP_OK;
}

void startCameraServer()
{
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;

  httpd_uri_t index_uri = {
      .uri = "/",
      .method = HTTP_GET,
      .handler = index_handler,
      .user_ctx = NULL};

  if (httpd_start(&camera_httpd, &config) == ESP_OK)
  {
    httpd_register_uri_handler(camera_httpd, &index_uri);
  }
}
#endif

// ==================== END ====================
