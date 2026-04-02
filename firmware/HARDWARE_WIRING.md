# ESP32 Smart Glasses Hardware Wiring

This wiring removes the vibration motor and matches your listed hardware.

## Wiring Diagram (Recommended Baseline)

```text
Li-po Battery
   -> TP4056 B+ / B-
TP4056 OUT+ / OUT-
   -> Power switch
   -> ESP32 power input path (3.3V regulated or 5V boosted, board-dependent)

ESP32 I2C bus:
  GPIO21 -> SH1106 SDA
  GPIO22 -> SH1106 SCL
  3.3V   -> SH1106 VCC
  GND    -> SH1106 GND

ESP32 Touch:
  GPIO5  <- Touch1 OUT
  GPIO18 <- Touch2 OUT (optional)
  3.3V   -> Touch VCC
  GND    -> Touch GND

ESP32 Audio Out -> HW-104 IN
HW-104 OUT -> Laptop speaker(s)

ESP32 Mic Input (INMP441 I2S):
  GPIO14 <- INMP441 SCK
  GPIO15 <- INMP441 WS
  GPIO4  <- INMP441 SD
  3.3V   -> INMP441 VDD
  GND    -> INMP441 GND
  GND/3.3V -> INMP441 L/R (channel select)
```

## Connection Tables

### 1. SH1106 OLED

| OLED Pin | ESP32 Pin |
| -------- | --------- |
| VCC      | 3.3V      |
| GND      | GND       |
| SCL      | GPIO22    |
| SDA      | GPIO21    |

### 2. Touch Module(s)

| Touch Pin | ESP32 Pin |
| --------- | --------- |
| VCC       | 3.3V      |
| GND       | GND       |
| OUT       | GPIO5     |

Optional second touch OUT: `GPIO18`.

### 3. Microphone

#### Option A (recommended): INMP441 6-pin I2S mic

| INMP441 Pin | ESP32 Pin / Note                         |
| ----------- | ---------------------------------------- |
| VDD         | 3.3V                                     |
| GND         | GND                                      |
| SCK         | GPIO14                                   |
| WS          | GPIO15                                   |
| SD          | GPIO4                                    |
| L/R         | GND = Left channel, 3.3V = Right channel |

For a single mic, tie L/R to either GND or 3.3V (do not leave it floating).

#### Option B: raw MEMS capsule

Raw MEMS is not directly compatible. Add a proper analog preamp/bias stage first.

### 4. Audio Amplifier (HW-104)

| HW-104 Pin | Connection                   |
| ---------- | ---------------------------- |
| VCC        | Power rail per module rating |
| GND        | Common GND                   |
| IN         | ESP32 audio output           |
| SPK+/-     | Speaker terminals            |

## Power Checklist

1. Confirm your ESP32 board power requirement before wiring battery output.
2. Keep all grounds common (ESP32, OLED, touch, mic, amp).
3. Add a physical switch on system output line.
4. Test OLED and touch first, then add audio, then mic.

## Backend Connection Architecture

Recommended chain:

1. ESP32 <-> Phone over BLE
2. Phone -> Backend HTTP API (`server/gateway.py` / `server/api_v2.py`)
3. Phone -> ESP32 over BLE (commands/text to display)

Why this is best:

1. BLE is good for local control packets
2. Phone handles internet + larger payloads + authentication
3. Easier debugging than direct ESP32 cloud pipeline

## API Endpoints to Use in Bridge App

1. `POST /v2/voice/transcribe`
2. `POST /v2/voice/process`
3. `POST /v2/gesture/recognize`
4. `POST /v2/multimodal/process`

Server is started from `start_gateway.py`.
