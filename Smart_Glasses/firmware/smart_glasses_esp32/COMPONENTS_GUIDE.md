# Smart Glasses Components Guide

This guide is aligned to your actual hardware and removes the vibration motor.

## Components You Already Have

1. Touch module
2. TP4056 1S BMS/charger module
3. SH1106 OLED display
4. HW-104 audio amplifier
5. Laptop speakers (Compaq Mini)
6. Li-po battery
7. Raw MEMS microphone element
8. Spare 5V to 3.3V regulator
9. Extra touch pad

## Components You Still Need

1. ESP32 board (required)
2. Power switch (required)
3. Microphone front-end (required if you want voice input from glasses)
4. Depending on ESP32 board input, possibly a 3.7V to 5V boost converter

## Microphone Requirement (Critical)

A raw MEMS capsule is not plug-and-play with ESP32.

You need one of these:

1. Recommended: I2S MEMS microphone breakout (INMP441 or ICS-43434)
2. Alternative: analog mic preamp module (MAX9814 or MAX4466) feeding ESP32 ADC

Without one of those, reliable voice capture will not work.

## Power Architecture

1. Li-po -> TP4056 (B+ / B-) for charge/protection
2. System power from TP4056 OUT+ / OUT-
3. Then choose one:
   - If your ESP32 board takes 5V on VIN/USB: add boost converter (3.7V to 5V)
   - If your board accepts regulated 3.3V input: use stable 3.3V regulator path

## SH1106 OLED (I2C)

| SH1106 Pin | ESP32 Pin |
| ---------- | --------- |
| VCC        | 3.3V      |
| GND        | GND       |
| SCL        | GPIO 22   |
| SDA        | GPIO 21   |

## Touch Inputs

| Touch Module Pin | ESP32 Pin |
| ---------------- | --------- |
| VCC              | 3.3V      |
| GND              | GND       |
| OUT              | GPIO 5    |

Second touch pad (optional): `GPIO18`.

## Audio Output Path

1. ESP32 audio output -> HW-104 amplifier input
2. HW-104 output -> laptop speakers

Notes:

1. Classic ESP32 can use built-in DAC (`GPIO25`/`GPIO26`) for cleaner analog output
2. ESP32-C3 has no DAC; for good quality use an external I2S DAC module

## Final BOM to Finish the Project

1. ESP32 board
2. TP4056 module
3. Li-po battery
4. SH1106 OLED
5. Touch module(s)
6. HW-104 amplifier + speakers
7. Microphone front-end option:
   - I2S MEMS breakout (recommended), or
   - analog preamp module
8. Power switch
9. Optional boost converter (if your ESP32 board requires 5V input)
