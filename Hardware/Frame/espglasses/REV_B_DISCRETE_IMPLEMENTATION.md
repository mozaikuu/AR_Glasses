# ESPGlasses Rev-B Discrete Implementation (Concrete Parts)

This document starts implementation for the concrete-part approach: break module boards into component-level circuits that can be placed and routed directly in KiCad.

## Locked Inputs (From Purchased Parts)

- ESP32-WROVER-E development direction with OV2640 camera
- MPU-6050
- 1.3 inch I2C OLED
- HW-104 (exact variant still to be confirmed)
- 1S Li-ion charger Type-C board
- Li-ion battery 3.7V 1000mAh
- INMP441 digital microphone
- 8 ohm / 0.5W small speaker (20mm)

## PCB Envelope Targets

- Left arm: 140mm x 30mm
- Right arm: 140mm x 30mm
- Main frame section: 130mm x 50mm

## Decomposition Policy

1. Keep integrated ICs as ICs (no transistor-level replacement unless requested).
2. Replace purchased module boards with the equivalent IC-level reference circuits.
3. Keep footprints practical for assembly (0603 for passives unless function demands otherwise).
4. Maintain firmware-aligned net naming where practical.

## Block-by-Block Discrete Breakdown

### 1) ESP32 Core + Boot/Debug

- Core IC/module: ESP32-WROVER-E
- Support components:
  - EN pull-up resistor
  - IO0 pull-up and boot button path
  - Local decoupling capacitors (10uF + 100nF near power pins)
  - UART programming header / test pads
- Critical nets:
  - +3V3_DIG, GND, EN, IO0, UART_TX_DBG, UART_RX_DBG

### 2) Camera (OV2640)

- Sensor: OV2640 interface block
- Support components:
  - Camera connector or direct footprint (based on selected camera board breakout strategy)
  - XCLK, PCLK, VSYNC, HREF, SCCB (SDA/SCL), data lane nets
  - Local decoupling and analog rail filtering
- Critical note:
  - This is a major GPIO consumer; final pin map must be locked in schematic before routing.

### 3) IMU (MPU-6050)

- Core IC: MPU-6050
- Support components:
  - I2C pull-ups (if not already shared globally)
  - Decoupling capacitors
  - Address strap option (AD0)
- Nets:
  - I2C_SCL, I2C_SDA, +3V3_DIG, GND, optional INT

### 4) OLED 1.3 inch I2C

- Display block represented as panel connector + control/power lines
- Support components:
  - Shared I2C pull-up strategy validation (single pull-up domain)
  - Reset line option if panel requires it
- Nets:
  - I2C_SCL, I2C_SDA, +3V3_DIG, GND, OLED_RST(optional)

### 5) Li-ion Charging + Power Regulation

- USB-C power input
- 1S charger equivalent circuit (IC-level)
- System rail path and protection
- 3.3V regulation stage
- Support components:
  - Input/output bulk + bypass caps
  - Status LED and current-limit resistor
  - Reverse/current-path protection as required
- Nets:
  - VBUS_5V, VBAT_RAW, VSYS, +3V3_DIG, +3V3_AUD, GND

### 6) Microphone (INMP441)

- Core IC: INMP441 (digital I2S)
- Support components:
  - Decoupling capacitor near VDD
  - Optional bias/filter network per reference design
- Nets:
  - I2S_SD_IN, I2S_BCLK, I2S_WS, MIC_LR, +3V3_AUD, GND

### 7) Speaker + Audio Output

- Output transducer: 8 ohm / 0.5W speaker
- Amplifier stage: discrete IC-level audio amp block
- Support components:
  - Input coupling/filter network
  - Gain-setting resistors/caps (if amplifier requires)
  - Output stabilization network (if required by amp topology)
- Nets:
  - AUD_IN, SPK_OUT_P, SPK_OUT_N(or SPK_OUT + GND), +3V3_AUD, GND

### 8) HW-104 Block

- Status: unresolved exact variant
- Current implementation state:
  - Add placeholder functional block in docs only
  - Do not lock schematic symbol until exact function is confirmed
- Required for closure:
  - Board photo or seller link to identify exact HW-104 function

## Implementation Sequence (In Progress)

1. Create concrete BOM/datasheet with individual components.
2. Create decomposed net map and reference designator ranges.
3. Migrate schematic generation script from Rev-A placeholder connectors to discrete blocks.
4. Re-sync to PCB and run ERC/DRC.

## Current Status

- Rev-B discrete specification file created.
- Component datasheet generation tooling added.
- Next action: generate and validate initial concrete component datasheet, then wire into schematic generation script.
