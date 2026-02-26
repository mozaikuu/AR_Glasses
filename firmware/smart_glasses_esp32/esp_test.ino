#include <Arduino.h>
#include <Wire.h>
// #include "driver/i2s.h"

// Set to 1 if the U8g2 library is installed and you want a full OLED draw test.
#define USE_SH1106_U8G2 1

#if USE_SH1106_U8G2
#include <U8g2lib.h>
U8G2_SH1106_128X64_NONAME_F_HW_I2C gDisplay(U8G2_R0, U8X8_PIN_NONE);
#endif

// ---------------------------
// Pin configuration
// ---------------------------
static const int PIN_I2C_SDA = 21;
static const int PIN_I2C_SCL = 22;

static const int PIN_TOUCH_1 = 5;
static const int PIN_TOUCH_2 = 18; // optional

static const int PIN_AUDIO_OUT = 25; // to HW-104 IN

// Analog mic input (if using MAX9814/MAX4466 style preamp)
static const int PIN_MIC_ANALOG = 34;

// I2S mic input pins (INMP441 / ICS-43434 style)
static const int PIN_I2S_BCK = 14;
static const int PIN_I2S_WS = 15;
static const int PIN_I2S_SD = 4;

static const int TOUCH_ACTIVE_LEVEL = HIGH;

static const uint8_t OLED_ADDR_A = 0x3C;
static const uint8_t OLED_ADDR_B = 0x3D;

void printMenu();
void testOled();
void testTouch();
void testAudioOut();
void testAnalogMic();
void testI2SMic();
void runAllTests();

int readSerialCommand()
{
  if (!Serial.available())
  {
    return -1;
  }

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if (cmd.length() == 0)
  {
    return -1;
  }

  return cmd.charAt(0);
}

bool i2cDevicePresent(uint8_t addr)
{
  Wire.beginTransmission(addr);
  return (Wire.endTransmission() == 0);
}

void setup()
{
  Serial.begin(115200);
  delay(700);

  pinMode(PIN_TOUCH_1, INPUT);
  pinMode(PIN_TOUCH_2, INPUT);

  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);

  analogReadResolution(12);

  Serial.println("\n=== ESP32 Component Test (esp_test.ino) ===");
  Serial.println("Wire per HARDWARE_WIRING.md before running tests.");
  printMenu();
}

void loop()
{
  int c = readSerialCommand();
  if (c == -1)
  {
    delay(10);
    return;
  }

  switch (c)
  {
  case '1':
    testOled();
    break;
  case '2':
    testTouch();
    break;
  case '3':
    testAudioOut();
    break;
  case '4':
    testAnalogMic();
    break;
  case '5':
    // testI2SMic();
    break;
  case 'a':
  case 'A':
    runAllTests();
    break;
  case 'm':
  case 'M':
    printMenu();
    break;
  default:
    Serial.println("Unknown command. Press m for menu.");
    break;
  }
}

void printMenu()
{
  Serial.println("\nSelect test:");
  Serial.println("1 = OLED (I2C + SH1106)");
  Serial.println("2 = Touch inputs (GPIO5 + GPIO18)");
  Serial.println("3 = Audio out -> amplifier/speaker");
  Serial.println("4 = Analog mic level (MAX9814/MAX4466 -> ADC)");
  Serial.println("5 = I2S mic level (INMP441/ICS-43434)");
  Serial.println("A = Run all tests");
  Serial.println("M = Show menu");
}

void testOled()
{
  Serial.println("\n[OLED] Starting I2C scan...");

  bool found = false;
  for (uint8_t addr = 1; addr < 127; addr++)
  {
    if (i2cDevicePresent(addr))
    {
      found = true;
      Serial.print("[OLED] I2C device found at 0x");
      if (addr < 16)
        Serial.print('0');
      Serial.println(addr, HEX);
    }
  }

  if (!found)
  {
    Serial.println("[OLED] No I2C devices found. Check SDA/SCL, power, and GND.");
    return;
  }

  if (!i2cDevicePresent(OLED_ADDR_A) && !i2cDevicePresent(OLED_ADDR_B))
  {
    Serial.println("[OLED] SH1106 not found at 0x3C or 0x3D.");
    return;
  }

#if USE_SH1106_U8G2
  gDisplay.begin();
  gDisplay.clearBuffer();
  gDisplay.setFont(u8g2_font_6x10_tr);
  gDisplay.drawStr(0, 12, "ESP32 OLED TEST");
  gDisplay.drawStr(0, 28, "SH1106 detected");
  gDisplay.drawStr(0, 44, "If readable: PASS");
  gDisplay.sendBuffer();
  delay(1400);

  gDisplay.clearBuffer();
  gDisplay.drawFrame(0, 0, 128, 64);
  gDisplay.drawLine(0, 0, 127, 63);
  gDisplay.drawLine(0, 63, 127, 0);
  gDisplay.drawCircle(64, 32, 16);
  gDisplay.sendBuffer();
  delay(1400);

  gDisplay.clearBuffer();
  gDisplay.setFont(u8g2_font_ncenB08_tr);
  gDisplay.drawStr(14, 34, "OLED PASS");
  gDisplay.sendBuffer();

  Serial.println("[OLED] Draw test done. If screen showed graphics/text, PASS.");
#else
  Serial.println("[OLED] SH1106 address detected. U8g2 test disabled (USE_SH1106_U8G2=0).");
#endif
}

void testTouch()
{
  Serial.println("\n[TOUCH] Monitoring for 15 seconds...");
  Serial.println("[TOUCH] Touch pad 1 and pad 2; watch state changes below.");

  bool last1 = digitalRead(PIN_TOUCH_1);
  bool last2 = digitalRead(PIN_TOUCH_2);

  unsigned long start = millis();
  while (millis() - start < 15000)
  {
    bool now1 = (digitalRead(PIN_TOUCH_1) == TOUCH_ACTIVE_LEVEL);
    bool now2 = (digitalRead(PIN_TOUCH_2) == TOUCH_ACTIVE_LEVEL);

    if (now1 != last1)
    {
      last1 = now1;
      Serial.print("[TOUCH] GPIO5 -> ");
      Serial.println(now1 ? "PRESSED" : "RELEASED");
    }

    if (now2 != last2)
    {
      last2 = now2;
      Serial.print("[TOUCH] GPIO18 -> ");
      Serial.println(now2 ? "PRESSED" : "RELEASED");
    }

    delay(20);
  }

  Serial.println("[TOUCH] Test complete.");
}

void testAudioOut()
{
  Serial.println("\n[AUDIO] Starting Frequency Sweep (200Hz to 2000Hz)...");
  Serial.println("[AUDIO] Listen for clarity and check for any rattling/distortion.");

  // Use the new ESP32 3.0 LEDC API
  ledcAttach(PIN_AUDIO_OUT, 200, 10); // Start at 200Hz

  // Sweep Up
  for (int freq = 200; freq <= 2000; freq += 10)
  {
    ledcWriteTone(PIN_AUDIO_OUT, freq);
    delay(20); // 20ms at each frequency for a smooth glide
  }

  // Sweep Down
  for (int freq = 2000; freq >= 200; freq -= 10)
  {
    ledcWriteTone(PIN_AUDIO_OUT, freq);
    delay(20);
  }

  ledcWriteTone(PIN_AUDIO_OUT, 0); // Silence
  ledcDetach(PIN_AUDIO_OUT);

  Serial.println("[AUDIO] Sweep complete.");
}

void testAnalogMic()
{
  Serial.println("\n[ANALOG MIC] Sampling 5 seconds...");
  Serial.println("[ANALOG MIC] Speak/clap near the mic and observe peak-to-peak values.");

  uint16_t minV = 4095;
  uint16_t maxV = 0;

  unsigned long start = millis();
  unsigned long lastPrint = 0;

  while (millis() - start < 5000)
  {
    uint16_t v = analogRead(PIN_MIC_ANALOG);
    if (v < minV)
      minV = v;
    if (v > maxV)
      maxV = v;

    if (millis() - lastPrint > 350)
    {
      lastPrint = millis();
      Serial.print("[ANALOG MIC] value=");
      Serial.print(v);
      Serial.print(" p2p=");
      Serial.println(maxV - minV);
    }
  }

  Serial.print("[ANALOG MIC] Final p2p=");
  Serial.println(maxV - minV);
  Serial.println("[ANALOG MIC] If p2p rises clearly when speaking, PASS.");
}

// void testI2SMic()
// {
//   Serial.println("\n[I2S MIC] Initializing I2S read...");

//   i2s_config_t i2sConfig = {
//       .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
//       .sample_rate = 16000,
//       .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
//       .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
//       .communication_format = I2S_COMM_FORMAT_I2S,
//       .intr_alloc_flags = 0,
//       .dma_buf_count = 4,
//       .dma_buf_len = 256,
//       .use_apll = false,
//       .tx_desc_auto_clear = false,
//       .fixed_mclk = 0};

//   i2s_pin_config_t pinConfig = {
//       .bck_io_num = PIN_I2S_BCK,
//       .ws_io_num = PIN_I2S_WS,
//       .data_out_num = -1,
//       .data_in_num = PIN_I2S_SD};

//   i2s_driver_uninstall(I2S_NUM_0);
//   esp_err_t ok = i2s_driver_install(I2S_NUM_0, &i2sConfig, 0, nullptr);
//   if (ok != ESP_OK)
//   {
//     Serial.print("[I2S MIC] i2s_driver_install failed, code=");
//     Serial.println((int)ok);
//     return;
//   }

//   ok = i2s_set_pin(I2S_NUM_0, &pinConfig);
//   if (ok != ESP_OK)
//   {
//     Serial.print("[I2S MIC] i2s_set_pin failed, code=");
//     Serial.println((int)ok);
//     i2s_driver_uninstall(I2S_NUM_0);
//     return;
//   }

//   Serial.println("[I2S MIC] Reading for 5 seconds. Speak/clap near mic.");

//   int16_t samples[256];
//   unsigned long start = millis();
//   unsigned long lastPrint = 0;

//   while (millis() - start < 5000)
//   {
//     size_t bytesRead = 0;
//     i2s_read(I2S_NUM_0, samples, sizeof(samples), &bytesRead, portMAX_DELAY);

//     int count = bytesRead / sizeof(int16_t);
//     if (count <= 0)
//       continue;

//     int32_t peak = 0;
//     for (int i = 0; i < count; i++)
//     {
//       int32_t a = abs((int32_t)samples[i]);
//       if (a > peak)
//         peak = a;
//     }

//     if (millis() - lastPrint > 300)
//     {
//       lastPrint = millis();
//       Serial.print("[I2S MIC] peak=");
//       Serial.println(peak);
//     }
//   }

//   i2s_driver_uninstall(I2S_NUM_0);
//   Serial.println("[I2S MIC] Test complete. If peaks jump on voice/clap, PASS.");
// }

void runAllTests()
{
  Serial.println("\n[AUTO] Running all component tests in sequence...");
  testOled();
  testTouch();
  testAudioOut();
  testAnalogMic();
  // testI2SMic();
  Serial.println("[AUTO] Sequence complete.");
}
