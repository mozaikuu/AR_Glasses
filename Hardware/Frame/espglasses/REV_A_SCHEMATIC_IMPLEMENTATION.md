# ESPGlasses Rev-A Schematic Implementation

This file is the implementation companion for `espglasses.kicad_sch`.

## Locked Hardware Assumptions

- ESP32 dev board profile (exact module not yet locked)
- No camera in Rev-A
- I2C OLED on GPIO21 (SDA) and GPIO22 (SCL)
- Touch inputs on GPIO5 and GPIO18
- DAC audio on GPIO25/GPIO26 with mono output path
- Status LED on GPIO2
- Power path: 1S LiPo + USB-C charging + regulated 3.3V rail

## Net Names To Use In Schematic

- Power: `VBUS_5V`, `VBAT_RAW`, `VSYS`, `+3V3_DIG`, `+3V3_AUD`, `GND`
- OLED I2C: `I2C_SDA`, `I2C_SCL`, `OLED_RST` (optional)
- Touch: `TOUCH1_IN`, `TOUCH2_IN`
- Audio: `DAC_L_OUT`, `DAC_R_OUT`, `DAC_SUM`, `AUD_IN`, `SPK_OUT`
- LED: `LED_STAT`
- Debug/boot: `UART_TX_DBG`, `UART_RX_DBG`, `EN`, `IO0`

## Core Blocks To Place (Phase 1)

1. ESP32 core/dev-board header block
2. USB-C 5V input + charger + battery connector
3. 3.3V regulation and decoupling network
4. SH1106 OLED connector (4-pin minimum)
5. Touch input connectors for GPIO5/GPIO18
6. DAC mono-sum + RC low-pass + audio amp input/output
7. LED + resistor on GPIO2
8. UART/boot header and test points

## Minimum Bring-Up Test Points

- TP_VBUS_5V
- TP_VBAT
- TP_3V3
- TP_GND
- TP_EN
- TP_IO0
- TP_TX
- TP_RX
- TP_DAC_SUM

## Practical Notes

- Keep analog audio path physically separated from ESP32 antenna region.
- Add a ferrite and local bulk cap to `+3V3_AUD` if audio noise is observed.
- Keep I2C pull-ups only once on the bus.
- Keep boot straps safe: no external circuitry should force wrong boot mode on EN/IO0.

## Current Status

- `espglasses.kicad_sch` initialized from KiCad-MCP template.
- Automation script scaffold added at `scripts/bootstrap_rev_a_schematic.py`.
- Full auto-placement is blocked on local KiCad Python module (`pcbnew`) not being available.
