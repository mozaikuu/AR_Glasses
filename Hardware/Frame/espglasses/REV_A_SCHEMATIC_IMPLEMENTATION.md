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

- `espglasses.kicad_sch` is now recreated deterministically by MCP script and populated with Rev-A symbols.
- Net labels for power, I2C, touch, audio, LED, and UART/boot are placed by automation.
- Starter wiring is implemented (29 wire stubs + connected net labels on key connector and U1 pins).
- ERC passes cleanly (0 errors, 0 warnings, 0 info) using MCP.
- Active implementation script: `scripts/mcp_populate_rev_a.py`.

## Starter Wiring Implemented

- OLED connector `J2`: pin 1 `+3V3_DIG`, pin 2 `GND`, pin 3 `I2C_SCL`, pin 4 `I2C_SDA`
- Touch connector `J3`: pin 1 `TOUCH1_IN`, pin 2 `TOUCH2_IN`
- Audio connector `J4`: pin 1 `DAC_SUM`, pin 2 `GND`
- UART/boot header `J5`: pin 1 `UART_TX_DBG`, pin 2 `UART_RX_DBG`, pin 3 `EN`, pin 4 `IO0`, pin 5 `+3V3_DIG`, pin 6 `GND`
- LED connector `J6`: pin 1 `LED_STAT`, pin 2 `GND`
- U1 breakout starter mapping:
   - pin 2 `+3V3_DIG`, pin 1 `GND`
   - pin 32 `I2C_SCL`, pin 34 `I2C_SDA`
   - pin 26 `TOUCH1_IN`, pin 24 `TOUCH2_IN`
   - pin 16 `DAC_L_OUT`, pin 14 `DAC_R_OUT`
   - pin 10 `UART_TX_DBG`, pin 12 `UART_RX_DBG`
   - pin 6 `EN`, pin 4 `IO0`, pin 8 `LED_STAT`

## Footprints Assigned

- `U1`: `RF_Module:ESP32-WROOM-32`
- `J1`: `Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical`
- `J2`: `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical`
- `J3`: `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical`
- `J4`: `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical`
- `J5`: `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical`
- `J6`: `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical`
- `R1`, `R2`, `R3`: `Resistor_SMD:R_0603_1608Metric`
- `C1`, `C2`: `Capacitor_SMD:C_0603_1608Metric`
- `D1`: `LED_SMD:LED_0603_1608Metric`

## Notes For PCB Stage

- Schematic footprint fields are set and stable in automation.
- PCB is still an empty board shell until footprints are imported/placed on the board canvas.
- Current DRC failure is expected at this stage: `invalid_outline` (board outline not defined yet).

## PCB Implementation Status (Phase 2 Started)

- First-pass PCB floorplan is now applied with these placed references: `U1`, `J1`-`J6`, `R1`-`R3`, `C1`-`C2`, `D1`.
- Component positions were shifted into functional zones (connector row, passives cluster, ESP32 module area).
- Schematic-to-board sync is complete: 16 named nets imported and 43 pads assigned.
- Edge-related DRC blockers are cleared in the current board baseline (0 reported violations in MCP DRC check).
- Initial routing scripts were added for staged bring-up; experimental traces were reverted to keep a clean baseline before controlled net-by-net routing.
- Active PCB bootstrap scripts:
   - `scripts/bootstrap_rev_a_pcb.py`
   - `scripts/set_board_outline_and_rules.py`
   - `scripts/clear_all_tracks_rev_a.py`
   - `scripts/route_priority_nets_rev_a.py`
   - `scripts/route_led_chain_start.py`

## Rev-B Discrete Start

- A full discrete implementation track has started for the concrete purchased parts (camera-enabled direction).
- New implementation specification: `REV_B_DISCRETE_IMPLEMENTATION.md`.
- New component datasheet output: `bom/COMPONENT_DATASHEET.md`.
- New schematic population script baseline: `scripts/mcp_populate_rev_b_discrete.py`.
- Datasheet generator: `scripts/generate_component_datasheet.py`.
