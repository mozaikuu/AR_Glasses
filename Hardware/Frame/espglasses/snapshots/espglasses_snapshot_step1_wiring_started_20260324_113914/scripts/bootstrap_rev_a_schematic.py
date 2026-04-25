from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MCP_PY = ROOT / "KiCAD-MCP-Server" / "python"
if str(MCP_PY) not in sys.path:
    sys.path.insert(0, str(MCP_PY))

try:
    from commands.schematic import SchematicManager
    from commands.component_schematic import ComponentManager
except ModuleNotFoundError as exc:
    if exc.name == "pcbnew":
        print("ERROR: KiCad Python module 'pcbnew' is not available in this environment.")
        print("Install KiCad 9 and run this script from an environment where pcbnew can be imported.")
        raise SystemExit(2)
    raise


SCH_PATH = Path(__file__).resolve().parents[1] / "espglasses.kicad_sch"
BACKUP_PATH = SCH_PATH.with_suffix(".kicad_sch.bak")


def add_component(schematic, definition: dict) -> None:
    symbol = ComponentManager.add_component(schematic, definition, SCH_PATH)
    lib_id = symbol.lib_id.value if hasattr(symbol, "lib_id") else "unknown"

    # Do not accept silent fallback for connector blocks.
    expected_library = definition.get("library")
    if expected_library == "Connector_Generic" and not lib_id.startswith("Connector_Generic:"):
        raise RuntimeError(
            f"Connector symbol load failed for {definition['reference']}: got {lib_id}. "
            "Set KICAD9_SYMBOL_DIR to your KiCad symbols folder before running."
        )

    print(f"Added {definition['reference']}: {lib_id}")


def main() -> None:
    if "KICAD9_SYMBOL_DIR" not in os.environ:
        print(
            "WARNING: KICAD9_SYMBOL_DIR is not set. "
            "Connector symbols may fail to resolve in dynamic loading."
        )

    if SCH_PATH.exists():
        shutil.copy2(SCH_PATH, BACKUP_PATH)
        print(f"Backup written: {BACKUP_PATH}")

    # Rebuild from KiCAD-MCP template so dynamic symbol loading has base structure.
    schematic = SchematicManager.create_schematic(str(SCH_PATH))

    # Rev-A block placeholders tied to current firmware pin assumptions.
    components = [
        {
            "reference": "U1",
            "library": "Connector_Generic",
            "type": "Conn_02x19_Odd_Even",
            "value": "ESP32_DEV_BOARD_PIN_BREAKOUT",
            "x": 140,
            "y": 100,
        },
        {
            "reference": "J1",
            "library": "Connector_Generic",
            "type": "Conn_01x02",
            "value": "BATTERY_1S",
            "x": 55,
            "y": 40,
        },
        {
            "reference": "J2",
            "library": "Connector_Generic",
            "type": "Conn_01x04",
            "value": "OLED_SH1106_I2C",
            "x": 55,
            "y": 75,
        },
        {
            "reference": "J3",
            "library": "Connector_Generic",
            "type": "Conn_01x02",
            "value": "TOUCH_INPUTS",
            "x": 55,
            "y": 105,
        },
        {
            "reference": "J4",
            "library": "Connector_Generic",
            "type": "Conn_01x02",
            "value": "AUDIO_OUT_MONO",
            "x": 55,
            "y": 135,
        },
        {
            "reference": "J5",
            "library": "Connector_Generic",
            "type": "Conn_01x06",
            "value": "UART_BOOT_DEBUG",
            "x": 55,
            "y": 165,
        },
        {
            "reference": "J6",
            "library": "Connector_Generic",
            "type": "Conn_01x02",
            "value": "LED_STATUS",
            "x": 55,
            "y": 190,
        },
        {
            "reference": "R1",
            "library": "Device",
            "type": "R",
            "value": "1k",
            "x": 85,
            "y": 190,
        },
        {
            "reference": "D1",
            "library": "Device",
            "type": "LED",
            "value": "GREEN",
            "x": 100,
            "y": 190,
        },
        {
            "reference": "R2",
            "library": "Device",
            "type": "R",
            "value": "10k",
            "x": 100,
            "y": 55,
        },
        {
            "reference": "R3",
            "library": "Device",
            "type": "R",
            "value": "10k",
            "x": 110,
            "y": 55,
        },
        {
            "reference": "C1",
            "library": "Device",
            "type": "C",
            "value": "10uF",
            "x": 120,
            "y": 40,
        },
        {
            "reference": "C2",
            "library": "Device",
            "type": "C",
            "value": "100nF",
            "x": 130,
            "y": 40,
        },
    ]

    for component in components:
        add_component(schematic, component)

    schematic.write(str(SCH_PATH))
    print(f"Schematic written: {SCH_PATH}")


if __name__ == "__main__":
    main()
