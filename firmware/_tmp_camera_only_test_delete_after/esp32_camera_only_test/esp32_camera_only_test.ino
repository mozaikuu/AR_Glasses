#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include "esp_camera.h"
#include "esp_heap_caps.h"

// Camera-only temporary test sketch.
// Remove folder: Firmware/_tmp_camera_only_test_delete_after after testing.d:\0_code\Life_Recorder\esp32.ino

static const char *AP_SSID = "SmartGlasses_CamOnly";
static const char *AP_PASSWORD = "12345678";

// ESP32-WROVER / AI-Thinker style camera pin map used by this project.
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

WebServer server(80);
bool cameraReady = false;
bool cameraSafeMode = false;
String cameraLastError = "NOT_INITIALIZED";
uint32_t captureOkCount = 0;
uint32_t captureFailCount = 0;
uint32_t lastCaptureBytes = 0;
uint32_t lastCaptureMs = 0;

static void printMemorySnapshot(const char *stage)
{
  const size_t internalFree = heap_caps_get_free_size(MALLOC_CAP_INTERNAL);
  const size_t psramFree = heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
  Serial.printf("MEM[%s] INT_FREE=%u PSRAM_FREE=%u\n", stage, (unsigned)internalFree, (unsigned)psramFree);
}

static bool captureJpeg(size_t &bytesOut, uint32_t &msOut)
{
  const uint32_t t0 = millis();
  camera_fb_t *fb = nullptr;

  // Retry a few times because first frame(s) can occasionally fail.
  for (int i = 0; i < 3; ++i)
  {
    fb = esp_camera_fb_get();
    if (fb)
    {
      break;
    }
    delay(40);
  }

  // If capture fails in normal mode, retry once with a conservative profile.
  if (!fb && !cameraSafeMode)
  {
    Serial.println("WARN: capture failed, switching to safe profile...");
    esp_camera_deinit();

    camera_config_t safeCfg = {};
    safeCfg.ledc_channel = LEDC_CHANNEL_0;
    safeCfg.ledc_timer = LEDC_TIMER_0;
    safeCfg.pin_d0 = CAM_PIN_D0;
    safeCfg.pin_d1 = CAM_PIN_D1;
    safeCfg.pin_d2 = CAM_PIN_D2;
    safeCfg.pin_d3 = CAM_PIN_D3;
    safeCfg.pin_d4 = CAM_PIN_D4;
    safeCfg.pin_d5 = CAM_PIN_D5;
    safeCfg.pin_d6 = CAM_PIN_D6;
    safeCfg.pin_d7 = CAM_PIN_D7;
    safeCfg.pin_xclk = CAM_PIN_XCLK;
    safeCfg.pin_pclk = CAM_PIN_PCLK;
    safeCfg.pin_vsync = CAM_PIN_VSYNC;
    safeCfg.pin_href = CAM_PIN_HREF;
    safeCfg.pin_sccb_sda = CAM_PIN_SIOD;
    safeCfg.pin_sccb_scl = CAM_PIN_SIOC;
    safeCfg.pin_pwdn = CAM_PIN_PWDN;
    safeCfg.pin_reset = CAM_PIN_RESET;
    safeCfg.xclk_freq_hz = 10000000;
    safeCfg.pixel_format = PIXFORMAT_JPEG;
    safeCfg.frame_size = FRAMESIZE_QQVGA;
    safeCfg.jpeg_quality = 20;
    safeCfg.fb_count = 1;
    safeCfg.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
    safeCfg.fb_location = CAMERA_FB_IN_DRAM;

    const esp_err_t safeErr = esp_camera_init(&safeCfg);
    if (safeErr == ESP_OK)
    {
      cameraSafeMode = true;
      cameraReady = true;
      cameraLastError = "";
      Serial.println("Camera safe profile: OK");

      for (int i = 0; i < 3; ++i)
      {
        fb = esp_camera_fb_get();
        if (fb)
        {
          break;
        }
        delay(40);
      }
    }
    else
    {
      cameraReady = false;
      cameraLastError = "CAM_SAFE_INIT_ERR:" + String((int)safeErr);
      Serial.printf("ERR:CAM:SAFE_INIT:%d\n", (int)safeErr);
    }
  }

  if (!fb)
  {
    cameraLastError = "CAPTURE_FAIL";
    captureFailCount++;
    return false;
  }

  bytesOut = fb->len;
  msOut = millis() - t0;
  lastCaptureBytes = static_cast<uint32_t>(fb->len);
  lastCaptureMs = msOut;
  captureOkCount++;
  cameraLastError = "";

  esp_camera_fb_return(fb);
  return true;
}

static void setupCamera()
{
  cameraSafeMode = false;

  camera_config_t cfg = {};
  cfg.ledc_channel = LEDC_CHANNEL_0;
  cfg.ledc_timer = LEDC_TIMER_0;
  cfg.pin_d0 = CAM_PIN_D0;
  cfg.pin_d1 = CAM_PIN_D1;
  cfg.pin_d2 = CAM_PIN_D2;
  cfg.pin_d3 = CAM_PIN_D3;
  cfg.pin_d4 = CAM_PIN_D4;
  cfg.pin_d5 = CAM_PIN_D5;
  cfg.pin_d6 = CAM_PIN_D6;
  cfg.pin_d7 = CAM_PIN_D7;
  cfg.pin_xclk = CAM_PIN_XCLK;
  cfg.pin_pclk = CAM_PIN_PCLK;
  cfg.pin_vsync = CAM_PIN_VSYNC;
  cfg.pin_href = CAM_PIN_HREF;
  cfg.pin_sccb_sda = CAM_PIN_SIOD;
  cfg.pin_sccb_scl = CAM_PIN_SIOC;
  cfg.pin_pwdn = CAM_PIN_PWDN;
  cfg.pin_reset = CAM_PIN_RESET;
  cfg.xclk_freq_hz = 10000000;
  cfg.pixel_format = PIXFORMAT_JPEG;
  cfg.frame_size = FRAMESIZE_QVGA;
  cfg.jpeg_quality = 12;
  cfg.fb_count = 2;
  cfg.grab_mode = CAMERA_GRAB_LATEST;
  cfg.fb_location = CAMERA_FB_IN_PSRAM;

  const esp_err_t err = esp_camera_init(&cfg);
  if (err != ESP_OK)
  {
    cameraReady = false;
    cameraLastError = "CAM_INIT_ERR:" + String((int)err);
    Serial.printf("ERR:CAM:INIT:%d\n", (int)err);
    return;
  }

  cameraReady = true;
  cameraLastError = "";
  Serial.println("Camera init: OK");

  // Warm-up frame to stabilize first real capture.
  size_t warmupBytes = 0;
  uint32_t warmupMs = 0;
  (void)captureJpeg(warmupBytes, warmupMs);
}

static String jsonEscape(const String &in)
{
  String out;
  out.reserve(in.length() + 8);
  for (size_t i = 0; i < in.length(); ++i)
  {
    const char c = in[i];
    if (c == '"' || c == '\\')
    {
      out += '\\';
    }
    out += c;
  }
  return out;
}

static String statusJson()
{
  String json = "{";
  json += "\"ok\":";
  json += cameraReady ? "true" : "false";
  json += ",\"ready\":";
  json += cameraReady ? "true" : "false";
  json += ",\"safe_mode\":";
  json += cameraSafeMode ? "true" : "false";
  json += ",\"last_error\":\"";
  json += jsonEscape(cameraLastError);
  json += "\"";
  json += ",\"capture_ok_count\":" + String(captureOkCount);
  json += ",\"capture_fail_count\":" + String(captureFailCount);
  json += ",\"last_capture_bytes\":" + String(lastCaptureBytes);
  json += ",\"last_capture_ms\":" + String(lastCaptureMs);
  json += ",\"uptime_ms\":" + String(millis());
  json += "}";
  return json;
}

static void handleRoot()
{
  String msg;
  msg += "ESP32 camera-only test\n";
  msg += "GET /status\n";
  msg += "GET /capture or POST /capture\n";
  msg += "Serial commands: STATUS, SNAP, REINIT\n";
  server.send(200, "text/plain", msg);
}

static void handleStatus()
{
  server.send(200, "application/json", statusJson());
}

static void handleCapture()
{
  if (!cameraReady)
  {
    server.send(503, "application/json", statusJson());
    return;
  }

  size_t bytes = 0;
  uint32_t ms = 0;
  const bool ok = captureJpeg(bytes, ms);

  String json = "{";
  json += "\"ok\":";
  json += ok ? "true" : "false";
  json += ",\"bytes\":" + String(bytes);
  json += ",\"capture_ms\":" + String(ms);
  json += ",\"status\":";
  json += statusJson();
  json += "}";

  server.send(ok ? 200 : 500, "application/json", json);
}

static void handleSerialCommand(String cmd)
{
  cmd.trim();
  if (cmd.length() == 0)
  {
    return;
  }

  if (cmd == "STATUS")
  {
    Serial.println(statusJson());
    return;
  }

  if (cmd == "SNAP")
  {
    size_t bytes = 0;
    uint32_t ms = 0;
    const bool ok = captureJpeg(bytes, ms);
    if (ok)
    {
      Serial.printf("CAPTURE_OK bytes=%u ms=%u\n", (unsigned)bytes, (unsigned)ms);
    }
    else
    {
      Serial.printf("CAPTURE_FAIL err=%s\n", cameraLastError.c_str());
    }
    return;
  }

  if (cmd == "REINIT")
  {
    Serial.println("Reinitializing camera...");
    esp_camera_deinit();
    setupCamera();
    Serial.println(statusJson());
    return;
  }

  Serial.println("Unknown command. Use STATUS, SNAP, REINIT");
}

void setup()
{
  Serial.begin(115200);
  delay(300);

  Serial.println("=== ESP32 Camera-Only Test ===");
  printMemorySnapshot("boot");

  setupCamera();

  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);
  Serial.print("AP SSID: ");
  Serial.println(AP_SSID);
  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());

  server.on("/", HTTP_GET, handleRoot);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/capture", HTTP_POST, handleCapture);
  server.begin();

  Serial.println("HTTP server started");
  Serial.println("Ready. Send 'SNAP' on serial to test capture.");
  printMemorySnapshot("ready");
}

void loop()
{
  server.handleClient();

  static char buf[64];
  static size_t len = 0;
  while (Serial.available() > 0)
  {
    const char c = static_cast<char>(Serial.read());
    if (c == '\r')
    {
      continue;
    }
    if (c == '\n')
    {
      buf[len] = '\0';
      handleSerialCommand(String(buf));
      len = 0;
      continue;
    }
    if (len < sizeof(buf) - 1)
    {
      buf[len++] = c;
    }
  }
}
