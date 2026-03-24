from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MCP_PY = ROOT / "KiCAD-MCP-Server" / "python"
if str(MCP_PY) not in sys.path:
    sys.path.insert(0, str(MCP_PY))

from kicad_interface import KiCADInterface


SCH_PATH = Path(__file__).resolve().parents[1] / "espglasses.kicad_sch"
BACKUP_PATH = SCH_PATH.with_suffix(".kicad_sch.mcp.bak")


def run_cmd(kicad: KiCADInterface, command: str, params: dict) -> dict:
    result = kicad.handle_command(command, params)
    if not result.get("success"):
        raise RuntimeError(f"{command} failed: {result}")
    return result


def main() -> None:
    if SCH_PATH.exists():
        shutil.copy2(SCH_PATH, BACKUP_PATH)
        print(f"Backup written: {BACKUP_PATH}")

    kicad = KiCADInterface()

    # Recreate schematic from MCP template to ensure deterministic state.
    run_cmd(kicad, "create_schematic", {"filename": str(SCH_PATH)})

    components = [
        {
            "library": "Connector_Generic",
            "type": "Conn_02x19_Odd_Even",
            "reference": "U1",
            "value": "ESP32_DEV_BOARD_PIN_BREAKOUT",
            "x": 150,
            "y": 105,
        },
        {
            "library": "Connector_Generic",
            "type": "Conn_01x02",
            "reference": "J1",
            "value": "BATTERY_1S",
            "x": 60,
            "y": 40,
        },
        {
            "library": "Connector_Generic",
            "type": "Conn_01x04",
            "reference": "J2",
            "value": "OLED_SH1106_I2C",
            "x": 60,
            "y": 72,
        },
        {
            "library": "Connector_Generic",
            "type": "Conn_01x02",
            "reference": "J3",
            "value": "TOUCH_INPUTS",
            "x": 60,
            "y": 100,
        },
        {
            "library": "Connector_Generic",
            "type": "Conn_01x02",
            "reference": "J4",
            "value": "AUDIO_OUT_MONO",
            "x": 60,
            "y": 128,
        },
        {
            "library": "Connector_Generic",
            "type": "Conn_01x06",
            "reference": "J5",
            "value": "UART_BOOT_DEBUG",
            "x": 60,
            "y": 160,
        },
        {
            "library": "Connector_Generic",
            "type": "Conn_01x02",
            "reference": "J6",
            "value": "LED_STATUS",
            "x": 60,
            "y": 190,
        },
        {
            "library": "Device",
            "type": "R",
            "reference": "R1",
            "value": "1k",
            "x": 95,
            "y": 190,
        },
        {
            "library": "Device",
            "type": "LED",
            "reference": "D1",
            "value": "GREEN",
            "x": 108,
            "y": 190,
        },
        {
            "library": "Device",
            "type": "R",
            "reference": "R2",
            "value": "10k",
            "x": 112,
            "y": 52,
        },
        {
            "library": "Device",
            "type": "R",
            "reference": "R3",
            "value": "10k",
            "x": 124,
            "y": 52,
        },
        {
            "library": "Device",
            "type": "C",
            "reference": "C1",
            "value": "10uF",
            "x": 134,
            "y": 40,
        },
        {
            "library": "Device",
            "type": "C",
            "reference": "C2",
            "value": "100nF",
            "x": 144,
            "y": 40,
        },
    ]

    for component in components:
        run_cmd(
            kicad,
            "add_schematic_component",
            {"schematicPath": str(SCH_PATH), "component": component},
        )
        print(f"Added {component['reference']}")

    # Assign practical default footprints so PCB sync can proceed immediately.
    footprints = {
        "U1": "RF_Module:ESP32-WROOM-32",
        "J1": "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
        "J2": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
        "J3": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        "J4": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        "J5": "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
        "J6": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        "R1": "Resistor_SMD:R_0603_1608Metric",
        "R2": "Resistor_SMD:R_0603_1608Metric",
        "R3": "Resistor_SMD:R_0603_1608Metric",
        "C1": "Capacitor_SMD:C_0603_1608Metric",
        "C2": "Capacitor_SMD:C_0603_1608Metric",
        "D1": "LED_SMD:LED_0603_1608Metric",
    }

    for ref, footprint in footprints.items():
        run_cmd(
            kicad,
            "edit_schematic_component",
            {
                "schematicPath": str(SCH_PATH),
                "reference": ref,
                "footprint": footprint,
            },
        )
        print(f"Set {ref} footprint -> {footprint}")

    # Phase-2 starter wiring: assign named nets to relevant connector pins and
    # representative U1 breakout pins so electrical intent is explicit.
    pin_net_connections = [
        # Battery input connector J1
        ("J1", "1", "VBAT_RAW"),
        ("J1", "2", "GND"),
        # OLED connector J2: +3V3, GND, SCL, SDA
        ("J2", "1", "+3V3_DIG"),
        ("J2", "2", "GND"),
        ("J2", "3", "I2C_SCL"),
        ("J2", "4", "I2C_SDA"),
        # Touch connector J3
        ("J3", "1", "TOUCH1_IN"),
        ("J3", "2", "TOUCH2_IN"),
        # Audio connector J4: mono output and ground
        ("J4", "1", "DAC_SUM"),
        ("J4", "2", "GND"),
        # UART/boot header J5
        ("J5", "1", "UART_TX_DBG"),
        ("J5", "2", "UART_RX_DBG"),
        ("J5", "3", "EN"),
        ("J5", "4", "IO0"),
        ("J5", "5", "+3V3_DIG"),
        ("J5", "6", "GND"),
        # LED connector J6
        ("J6", "1", "LED_STAT"),
        ("J6", "2", "GND"),
        # LED chain and passive networks
        ("R1", "1", "LED_STAT"),
        ("R1", "2", "LED_A"),
        ("D1", "2", "LED_A"),
        ("D1", "1", "GND"),
        # DAC mono sum through resistors
        ("R2", "1", "DAC_L_OUT"),
        ("R2", "2", "DAC_SUM"),
        ("R3", "1", "DAC_R_OUT"),
        ("R3", "2", "DAC_SUM"),
        # 3V3 decoupling caps
        ("C1", "1", "+3V3_DIG"),
        ("C1", "2", "GND"),
        ("C2", "1", "+3V3_DIG"),
        ("C2", "2", "GND"),
        # Representative U1 breakout mapping for firmware-critical signals
        ("U1", "2", "+3V3_DIG"),
        ("U1", "1", "GND"),
        ("U1", "32", "I2C_SCL"),
        ("U1", "34", "I2C_SDA"),
        ("U1", "26", "TOUCH1_IN"),
        ("U1", "24", "TOUCH2_IN"),
        ("U1", "16", "DAC_L_OUT"),
        ("U1", "14", "DAC_R_OUT"),
        ("U1", "10", "UART_TX_DBG"),
        ("U1", "12", "UART_RX_DBG"),
        ("U1", "6", "EN"),
        ("U1", "4", "IO0"),
        ("U1", "8", "LED_STAT"),
    ]

    for ref, pin, net_name in pin_net_connections:
        run_cmd(
            kicad,
            "connect_to_net",
            {
                "schematicPath": str(SCH_PATH),
                "componentRef": ref,
                "pinName": str(pin),
                "netName": net_name,
            },
        )
        print(f"Connected {ref}.{pin} -> {net_name}")

    labels = [
        # Keep only high-level power rails as quick reference labels.
        ("VBUS_5V", 28, 36),
        ("VBAT_RAW", 28, 40),
        ("VSYS", 28, 44),
        ("+3V3_DIG", 28, 48),
        ("+3V3_AUD", 28, 52),
        ("GND", 28, 56),
    ]

    for net_name, x, y in labels:
        run_cmd(
            kicad,
            "add_schematic_net_label",
            {
                "schematicPath": str(SCH_PATH),
                "netName": net_name,
                "position": [x, y],
                "orientation": 0,
            },
        )
        print(f"Added label {net_name}")

    print(f"MCP population complete: {SCH_PATH}")


if __name__ == "__main__":
    main()
