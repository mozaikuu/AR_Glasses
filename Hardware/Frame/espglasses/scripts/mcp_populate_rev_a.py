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

    labels = [
        ("VBUS_5V", 28, 36),
        ("VBAT_RAW", 28, 40),
        ("VSYS", 28, 44),
        ("+3V3_DIG", 28, 48),
        ("+3V3_AUD", 28, 52),
        ("GND", 28, 56),
        ("I2C_SDA", 196, 86),
        ("I2C_SCL", 196, 90),
        ("TOUCH1_IN", 196, 98),
        ("TOUCH2_IN", 196, 102),
        ("DAC_L_OUT", 196, 110),
        ("DAC_R_OUT", 196, 114),
        ("LED_STAT", 196, 122),
        ("UART_TX_DBG", 196, 130),
        ("UART_RX_DBG", 196, 134),
        ("EN", 196, 138),
        ("IO0", 196, 142),
    ]

    for net_name, x, y in labels:
        run_cmd(
            kicad,
            "add_schematic_net_label",
            {
                "schematicPath": str(SCH_PATH),
                "netName": net_name,
                "x": x,
                "y": y,
                "rotation": 0,
            },
        )
        print(f"Added label {net_name}")

    print(f"MCP population complete: {SCH_PATH}")


if __name__ == "__main__":
    main()
