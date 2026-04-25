# Component Datasheet (Initial Concrete Set)

This file is generated from the concrete purchased-part implementation model.
Entries are the individual component-level building blocks for Rev-B decomposition.

| Ref | Part | Package | Role | Rail/Signal | Notes |
|---|---|---|---|---|---|
| U1 | ESP32-WROVER-E | Module | Main MCU + Wi-Fi/BLE | +3V3_DIG | Camera-capable ESP32 core |
| U2 | OV2640 | Camera sensor module/FFC | Image sensor | CAM_* | Parallel camera interface block |
| U3 | MPU-6050 | QFN (module-equivalent support) | 6-axis IMU | I2C_* | I2C sensor |
| U4 | INMP441 | LGA | Digital MEMS microphone | I2S_* | I2S microphone |
| U5 | Li-ion charger IC (Type-C input) | SOP/QFN | Battery charging | VBUS_5V/VBAT_RAW | Equivalent of purchased Type-C charger board |
| U6 | 3.3V regulator IC | SOT-223/SOT-23-5 | System regulation | VSYS/+3V3_DIG | Equivalent of purchased regulator stage |
| U7 | Audio amplifier IC | SOP/QFN | Speaker drive | AUD_IN/SPK_OUT | For 8 ohm 0.5W speaker |
| J1 | Li-ion battery connector | 2-pin JST | Battery input | VBAT_RAW | 3.7V 1000mAh battery |
| J2 | OLED panel connector | 4-pin header/FFC | Display interface | I2C_SCL/I2C_SDA | 1.3 inch I2C OLED |
| J3 | Camera connector | FFC/header | Camera link | CAM_* | OV2640 connection |
| J4 | Speaker connector | 2-pin | Audio transducer output | SPK_OUT | 20mm 8 ohm speaker |
| J5 | UART/boot header | 1x6 2.54mm | Debug/programming | UART/EN/IO0 | Bring-up and flashing |
| D1 | Status LED | 0603 | Power/status indication | LED_STAT | User-visible status |
| R1 | 1k | 0603 | LED current limit | LED_STAT | Status LED resistor |
| R2 | 10k | 0603 | I2C pull-up | I2C_SCL | Bus pull-up |
| R3 | 10k | 0603 | I2C pull-up | I2C_SDA | Bus pull-up |
| R4 | 10k | 0603 | EN pull-up | EN | ESP32 enable strap |
| R5 | 10k | 0603 | IO0 pull-up | IO0 | ESP32 boot strap |
| C1 | 10uF | 0603/0805 | Bulk decoupling | +3V3_DIG | Near ESP32/regulator |
| C2 | 100nF | 0603 | HF decoupling | +3V3_DIG | Near ESP32 power pins |
| C3 | 10uF | 0603/0805 | Regulator output bulk | +3V3_DIG | Regulator stability |
| C4 | 100nF | 0603 | Mic decoupling | +3V3_AUD | Near INMP441 |
| C5 | 100nF | 0603 | IMU decoupling | +3V3_DIG | Near MPU-6050 |
| X1 | HW-104 (exact variant pending) | Unknown | Unresolved purchased module | TBD | Needs exact module identification before schematic lock |

## Notes

- HW-104 is intentionally marked unresolved until exact module function is confirmed.
- Final manufacturer part numbers and exact footprints should be locked before fabrication.
- This file is intended to be updated as schematic references are finalized.
