# Smart Glasses Components Guide

## Compact Hobby/Mechatronics Parts for Wearable Project

---

## 1. Microphone - INMP441 (I2S Digital)

**Why:** Compact, low power, I2S digital output (no ADC needed)

| Pin  | ESP32 Pin | Notes        |
| ---- | --------- | ------------ |
| VCC  | 3.3V      |              |
| GND  | GND       |              |
| SCL  | GPIO 14   | I2S Clock    |
| WS   | GPIO 15   | Word Select  |
| DOUT | GPIO 4    | Data Out     |
| L/R  | GND       | Left channel |

**Price:** ~$1-2 (AliExpress)

**Code:**

```cpp
#include "driver/i2s.h"

void setup() {
  i2s_config_t config = {
    .mode = I2S_MODE_MASTER | I2S_MODE_RX,
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .dma_buf_count = 2,
    .dma_buf_len = 256,
  };

  i2s_pin_config_t pins = {
    .bck_io_num = 14,
    .ws_io_num = 15,
    .data_out_num = -1,
    .data_in_num = 4,
  };

  i2s_driver_install(0, &config, 0, NULL);
  i2s_set_pin(0, &pins);
}
```

---

## 2. IMU - MPU6050 (6-axis)

**Why:** Small, cheap, accelerometer + gyroscope in one

| Pin | ESP32 Pin | Notes        |
| --- | --------- | ------------ |
| VCC | 3.3V      |              |
| GND | GND       |              |
| SCL | GPIO 32   |              |
| SDA | GPIO 33   |              |
| AD0 | GND       | Address 0x68 |

**Price:** ~$0.50-1 (AliExpress)

**Library:** "MPU6050" by Electronic Cats

**Code:**

```cpp
#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

void setup() {
  Wire.begin(33, 32);
  mpu.begin(MPU6050_ADDR);
  mpu.setGyroRange(MPU6050_RANGE_500DPS);
  mpu.setAccelRange(MPU6050_RANGE_2G);
}

void loop() {
  Vector accel = mpu.readAccel();
  Vector gyro = mpu.readGyro();
  // accel.X, accel.Y, accel.Z
}
```

---

## 3. Vibration Motor - Mini Flat Motor

**Why:** Small, silent, good for haptic feedback

| Motor Pin | ESP32 Pin | Notes                 |
| --------- | --------- | --------------------- |
| Positive  | GPIO 13   | Via MOSFET/Transistor |
| Negative  | GND       |                       |

**Recommended Parts:**

-  **Motor:** 0830 flat vibration motor (8x3mm)
-  **Driver:** AO3400 MOSFET or 2N2222 transistor
-  **Diode:** 1N4007 (flyback protection)

**Circuit:**

```
GPIO 13 ──[100Ω]──→ MOSFET Gate
                    │
MOSFET Drain ─────→ Motor (+)
                    │
MOSFET Source ────→ GND
                    │
Motor (-) ─────────→ GND
                    │
1N4007 ───[Anode→GND, Cathode→Motor(+)]
```

**Code:**

```cpp
#define MOTOR_PIN 13

void setup() { pinMode(MOTOR_PIN, OUTPUT); }

void vibrate(int ms) {
  digitalWrite(MOTOR_PIN, HIGH);
  delay(ms);
  digitalWrite(MOTOR_PIN, LOW);
}
```

---

## 4. Power - 3.7V LiPo Battery

**Why:** Small, rechargeable, powers ESP32 directly

| Battery  | ESP32         |
| -------- | ------------- |
| Positive | VIN or 5V pin |
| Negative | GND           |

**Recommended Batteries:**

-  **302030:** 150mAh, 30x20x3mm
-  **401020:** 200mAh, 40x10x2mm
-  **501010:** 80mAh, 50x10x1mm

**Charging:** TP4056 USB charger module

---

## 5. Display - SSD1306 OLED (Optional)

**Why:** Small, low power, shows status/info

| Pin | ESP32 Pin | Notes |
| --- | --------- | ----- |
| VCC | 3.3V      |       |
| GND | GND       |       |
| SCL | GPIO 22   |       |
| SDA | GPIO 21   |       |

**Price:** ~$1-2 (128x64 OLED)

**Library:** "ESP8266 OLED" by Daniel Eichhorn

---

## 6. ESP32 Board - ESP32-C3 or ESP32-S3

**Why:** Smaller than Dev Kit, lower power

**Recommended:**

-  **ESP32-C3 SuperMini:** 23x18mm
-  **ESP32-S3 Tiny:** 25x20mm
-  **Bare ESP32 chip:** With custom PCB (most compact)

---

## Complete Bill of Materials

| Component                 | Size    | Price | Link       |
| ------------------------- | ------- | ----- | ---------- |
| ESP32-C3 SuperMini        | 23x18mm | $3-4  | AliExpress |
| INMP441 Mic               | 4x4mm   | $1-2  | AliExpress |
| MPU6050                   | 15x20mm | $0.50 | AliExpress |
| Mini Vibration Motor 0830 | 8x3mm   | $0.50 | AliExpress |
| SSD1306 OLED              | 27x27mm | $1-2  | AliExpress |
| LiPo 302030               | 150mAh  | $2-3  | AliExpress |
| TP4056 Charger            | 15x8mm  | $0.50 | AliExpress |
| MOSFET AO3400             | SOT-23  | $0.10 | AliExpress |

**Total Cost:** ~$10-15

---

## Minimal Wiring (No Display)

```
┌─────────────────────────┐
│    ESP32-C3 SuperMini   │
│                         │
│  GPIO 21 ───→ SDA MPU   │
│  GPIO 22 ───→ SCL MPU   │
│  GPIO  4 ───→ DOUT INMP │
│  GPIO 15 ───→ WS   INMP │
│  GPIO 14 ───→ SCK  INMP │
│  GPIO 13 ───→ Motor     │
│  3.3V  ───→ VCC MPU/INMP│
│  GND   ───→ GND All     │
└─────────────────────────┘
```

---

## Assembly Tips

1. **Use flex cable** for microphone (place near ear)
2. **Temple mount** for ESP32 and battery
3. **Bridge nose pad** for MPU6050 (detects head movement)
4. **Arm tip** for vibration motor
5. **Keep wires short** to reduce interference
