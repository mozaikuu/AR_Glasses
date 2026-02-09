/**
 * Smart Glasses ESP32 - QR Code Location System
 *
 * This firmware handles:
 * - QR code scanning using camera
 * - Location detection from QR codes
 * - BLE communication with mobile app
 * - Display output for location info
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLECharacteristic.h>
#include <BLE2902.h>
#include <esp_camera.h>

// ==================== Configuration ====================

// BLE UUIDs
#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

// WiFi Configuration
const char *wifi_ssid = "YOUR_WIFI_SSID";
const char *wifi_password = "YOUR_WIFI_PASSWORD";
const char *server_url = "http://YOUR_SERVER_IP:5000";

// Server endpoint for location updates
const char *location_update_endpoint = "/api/v2/location/update";

// ==================== Pin Definitions ====================

// Camera pin definitions for ESP32-CAM
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

// Status LED
#define LED_PIN 33

// ==================== Global Variables ====================

bool deviceConnected = false;
bool lastDeviceConnected = false;
unsigned long lastScanTime = 0;
const unsigned long SCAN_INTERVAL = 2000; // 2 seconds between scans

// Current location data
String currentLocationId = "";
String currentLocationName = "";
int currentFloor = 0;
float currentX = 0;
float currentY = 0;

// QR Code data buffer
String qrData = "";

// BLE Characteristics
BLECharacteristic *pCharacteristic = nullptr;

// ==================== BLE Server Callbacks ====================

class MyServerCallbacks : public BLEServerCallbacks
{
  void onConnect(BLEServer *pServer)
  {
    deviceConnected = true;
    Serial.println("Phone connected");
    digitalWrite(LED_PIN, HIGH);
  };

  void onDisconnect(BLEServer *pServer)
  {
    deviceConnected = false;
    Serial.println("Phone disconnected");
    digitalWrite(LED_PIN, LOW);
    // Restart advertising
    BLEDevice::startAdvertising();
  }
};

// ==================== BLE Characteristic Callbacks ====================

class CharacteristicCallbacks : public BLECharacteristicCallbacks
{
  void onWrite(BLECharacteristic *pCharacteristic)
  {
    String value = pCharacteristic->getValue();
    if (value.length() > 0)
    {
      Serial.print("Received BLE command: ");
      Serial.println(value.c_str());

      // Handle commands from phone
      if (value == "GET_LOCATION")
      {
        sendLocationToPhone();
      }
      else if (value.startsWith("SCAN_QR"))
      {
        // Trigger QR scan
        scanAndProcessQR();
      }
    }
  }
};

// ==================== Camera Initialization ====================

bool initCamera()
{
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QQVGA; // 160x120 - small for QR detection
  config.jpeg_quality = 12;
  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK)
  {
    Serial.printf("Camera init failed with error 0x%x", err);
    return false;
  }

  Serial.println("Camera initialized successfully");
  return true;
}

// ==================== QR Code Scanning ====================

/**
 * Scan for QR codes in camera frame.
 * Note: This is a simplified version. For production, use a proper QR library
 * like esp32-camera-qr or integrate with a vision library.
 */
String scanQRCode()
{
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb)
  {
    Serial.println("Camera capture failed");
    return "";
  }

  // In a full implementation, you would:
  // 1. Use a QR detection library like ZBar or Quirc
  // 2. Process the image buffer
  // 3. Extract QR code data

  // For now, we'll simulate QR detection
  // In production, replace with actual QR decoding

  esp_camera_fb_return(fb);

  return ""; // Return empty if no QR detected
}

/**
 * Process scanned QR code data.
 * Expected format: JSON with location info
 */
bool processQRData(String data)
{
  if (data.length() == 0)
    return false;

  // Parse JSON data
  // Expected format:
  // {"type":"location","id":"lab1","name":"Engineering Lab 1","floor":1,"coordinates":{"x":0,"y":10}}

  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, data);

  if (error)
  {
    Serial.print("JSON parse failed: ");
    Serial.println(error.c_str());
    return false;
  }

  // Extract location data
  String type = doc["type"] | "";
  if (type != "location")
  {
    Serial.println("Invalid QR code type");
    return false;
  }

  currentLocationId = doc["id"] | "";
  currentLocationName = doc["name"] | "";
  currentFloor = doc["floor"] | 0;

  if (doc["coordinates"].containsKey("x"))
  {
    currentX = doc["coordinates"]["x"];
    currentY = doc["coordinates"]["y"];
  }

  Serial.println("Location detected:");
  Serial.print("  ID: ");
  Serial.println(currentLocationId);
  Serial.print("  Name: ");
  Serial.println(currentLocationName);
  Serial.print("  Floor: ");
  Serial.println(currentFloor);
  Serial.print("  Coordinates: (");
  Serial.print(currentX);
  Serial.print(", ");
  Serial.print(currentY);
  Serial.println(")");

  return true;
}

/**
 * Scan and process QR code.
 */
void scanAndProcessQR()
{
  if (millis() - lastScanTime < SCAN_INTERVAL)
  {
    return; // Don't scan too frequently
  }

  lastScanTime = millis();

  String qr = scanQRCode();
  if (qr.length() > 0)
  {
    if (processQRData(qr))
    {
      // Location updated successfully
      // Send update to server
      sendLocationToServer();

      // Send to phone via BLE
      sendLocationToPhone();
    }
  }
}

// ==================== Server Communication ====================

void sendLocationToServer()
{
  if (WiFi.status() == WL_CONNECTED)
  {
    HTTPClient http;

    String url = String(server_url) + location_update_endpoint;
    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    // Create JSON payload
    String payload = "{";
    payload += "\"id\":\"" + currentLocationId + "\",";
    payload += "\"name\":\"" + currentLocationName + "\",";
    payload += "\"floor\":" + String(currentFloor) + ",";
    payload += "\"x\":" + String(currentX) + ",";
    payload += "\"y\":" + String(currentY) + ",";
    payload += "\"timestamp\":\"" + String(millis()) + "\"";
    payload += "}";

    int httpResponseCode = http.POST(payload);

    if (httpResponseCode > 0)
    {
      String response = http.getString();
      Serial.println("Server response: " + response);
    }
    else
    {
      Serial.print("Server error: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  }
  else
  {
    Serial.println("WiFi not connected");
  }
}

// ==================== BLE Communication ====================

void sendLocationToPhone()
{
  if (deviceConnected && pCharacteristic != nullptr)
  {
    String locationData = "{";
    locationData += "\"id\":\"" + currentLocationId + "\",";
    locationData += "\"name\":\"" + currentLocationName + "\",";
    locationData += "\"floor\":" + String(currentFloor);
    locationData += "}";

    pCharacteristic->setValue(locationData.c_str());
    pCharacteristic->notify();
    Serial.println("Location sent to phone via BLE");
  }
}

// ==================== Display Functions ====================

/**
 * Display current location on the glasses display.
 * Implement this based on your display hardware.
 */
void displayLocation()
{
  // Clear display
  // display.clear();

  // Show location name
  // display.setCursor(0, 0);
  // display.println("Location:");
  // display.println(currentLocationName);

  // Show floor info
  // display.setCursor(0, 40);
  // display.print("Floor: "); display.println(currentFloor);

  // Show coordinates
  // display.setCursor(0, 60);
  // display.print("X:"); display.print(currentX);
  // display.print(" Y:"); display.print(currentY);

  // Update display
  // display.display();
}

// ==================== Setup ====================

void setup()
{
  Serial.begin(115200);
  Serial.println("Smart Glasses QR Location System");

  // Initialize LED pin
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Initialize camera
  if (!initCamera())
  {
    Serial.println("Camera init failed!");
    while (1)
      ;
  }

  // Connect to WiFi
  Serial.print("Connecting to WiFi");
  WiFi.begin(wifi_ssid, wifi_password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Initialize BLE
  BLEDevice::init("Smart Glasses QR");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(
      CHARACTERISTIC_UUID,
      BLECharacteristic::PROPERTY_NOTIFY |
          BLECharacteristic::PROPERTY_WRITE);
  pCharacteristic->addDescriptor(new BLE2902());
  pCharacteristic->setCallbacks(new CharacteristicCallbacks());

  pService->start();

  // Start advertising
  BLEDevice::startAdvertising();
  Serial.println("BLE advertising started");
  Serial.println("Smart Glasses QR system ready!");
}

// ==================== Main Loop ====================

void loop()
{
  // Handle BLE disconnection/reconnection
  if (!deviceConnected && lastDeviceConnected)
  {
    delay(500);
    BLEDevice::startAdvertising();
    lastDeviceConnected = deviceConnected;
  }

  // Check for QR code scan
  scanAndProcessQR();

  // Update display with current location
  if (currentLocationId.length() > 0)
  {
    displayLocation();
  }

  delay(100);
}
