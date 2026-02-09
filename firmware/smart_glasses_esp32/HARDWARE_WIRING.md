# ESP32 Smart Glasses Hardware Wiring

## Compact Hobby/Mechatronics Components

---

## Pinout Diagram (Compact Build)

```
┌────────────────────────────────────────────────────────┐
│              ESP32-C3 SuperMini / DevKit                │
│                                                        │
│  GPIO 21 ───→ SDA (MPU6050 / OLED)                     │
│  GPIO 22 ───→ SCL (MPU6050 / OLED)                      │
│                                                        │
│  GPIO  4 ───→ I2S DOUT (INMP441 Mic)                   │
│  GPIO 15 ───→ I2S WS   (INMP441 Mic)                   │
│  GPIO 14 ───→ I2S SCK  (INMP441 Mic)                   │
│                                                        │
│  GPIO 13 ───→ MOSFET Gate → Vibration Motor            │
│  GPIO  5 ───→ (Optional: Button)                        │
│                                                        │
│  3.3V ───→ VCC (MPU6050, INMP441, OLED)               │
│  GND  ───→ GND (All components)                        │
└────────────────────────────────────────────────────────┘
```

---

## Component Connections

### 1. MPU6050 IMU (6-axis Accelerometer + Gyroscope)

| MPU6050 Pin | ESP32 Pin | Notes          |
| ----------- | --------- | -------------- |
| VCC         | 3.3V      |                |
| GND         | GND       |                |
| SCL         | GPIO 22   |                |
| SDA         | GPIO 21   |                |
| AD0         | GND       | Address = 0x68 |

### 2. INMP441 I2S Microphone

| INMP441 Pin | ESP32 Pin | Notes        |
| ----------- | --------- | ------------ |
| VCC         | 3.3V      |              |
| GND         | GND       |              |
| SCK         | GPIO 14   | Bit Clock    |
| WS          | GPIO 15   | Word Select  |
| DOUT        | GPIO 4    | Data Output  |
| L/R         | GND       | Left Channel |

### 3. Mini Vibration Motor (0830 Flat Motor)

```
GPIO 13 ──[100Ω]──→ AO3400 MOSFET Gate
                     │
MOSFET Drain ──────→ Motor (+)
                     │
MOSFET Source ─────→ GND
                     │
1N4007 Diode ──────→ Across motor terminals (cathode to +)
```

### 4. Optional: SSD1306 OLED Display

| OLED Pin | ESP32 Pin | Notes              |
| -------- | --------- | ------------------ |
| VCC      | 3.3V      |                    |
| GND      | GND       |                    |
| SCL      | GPIO 22   | Share with MPU6050 |
| SDA      | GPIO 21   | Share with MPU6050 |

### 5. Optional: Push Button

| Button Pin | ESP32 Pin | Notes            |
| ---------- | --------- | ---------------- |
| One side   | GPIO 5    |                  |
| Other side | GND       | Use INPUT_PULLUP |

---

## Power Supply

**Recommended Battery:** 302030 LiPo (150mAh, 30x20x3mm)

```
Battery (+) ──→ ESP32 VIN or 5V pin
Battery (-) ──→ ESP32 GND
              │
TP4056 Charger Module (for USB charging)
Battery (+) ──→ B+
Battery (-) ──→ B-
USB 5V ──────→ IN+
GND ─────────→ IN-
```

---

## Complete Wiring Table

| Component       | VCC  | GND | Signal 1             | Signal 2      | Signal 3     |
| --------------- | ---- | --- | -------------------- | ------------- | ------------ |
| MPU6050         | 3.3V | GND | GPIO 21 (SDA)        | GPIO 22 (SCL) | -            |
| INMP441         | 3.3V | GND | GPIO 4 (DOUT)        | GPIO 14 (SCK) | GPIO 15 (WS) |
| Vibration Motor | -    | GND | GPIO 13 (via MOSFET) | -             | -            |
| OLED (optional) | 3.3V | GND | GPIO 21 (SDA)        | GPIO 22 (SCL) | -            |
| Button          | -    | GND | GPIO 5               | -             | -            |

---

## Compact Assembly Tips

1. **MPU6050** → Bridge/nose pad area (detects head movement)
2. **INMP441 Mic** → Temple tip (near ear)
3. **ESP32** → Temple arm (middle section)
4. **Battery** → Other temple arm
5. **Vibration Motor** → Ear piece area
6. **OLED** → Inside lens area (if display desired)

---

## Minimal Code Test

```cpp
#include <Wire.h>
#include <MPU6050.h>

#define MOTOR_PIN 13
#define MIC_DATA 4
#define MIC_WS 15
#define MIC_SCK 14

MPU6050 mpu;

void setup() {
  Serial.begin(115200);

  // IMU
  Wire.begin(21, 22);
  mpu.begin(MPU6050_ADDR);

  // Motor
  pinMode(MOTOR_PIN, OUTPUT);
  digitalWrite(MOTOR_PIN, LOW);

  Serial.println("Ready!");
}

void loop() {
  // Read IMU
  Vector accel = mpu.readAccel();
  Serial.print("Accel: ");
  Serial.print(accel.X); Serial.print(", ");
  Serial.print(accel.Y); Serial.print(", ");
  Serial.println(accel.Z);

  delay(100);
}
```
