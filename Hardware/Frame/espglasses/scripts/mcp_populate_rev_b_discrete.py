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
BACKUP_PATH = SCH_PATH.with_suffix(".kicad_sch.rev_b.bak")


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
    run_cmd(kicad, "create_schematic", {"filename": str(SCH_PATH)})

    # Rev-B discrete component placement baseline.
    # Connector policy:
    # - Keep only USB-C charging (J5), Micro-USB programming (J6), and battery JST (J1).
    # - Convert prior external headers to internal nets + test pads.
    # Note: HW-104 is intentionally excluded until exact variant is identified.
    components = [
        # Core processing + camera + sensing IC blocks
        {"library": "Connector_Generic", "type": "Conn_02x19_Odd_Even", "reference": "U1", "value": "ESP32_WROVER_E_CORE", "x": 150, "y": 105},
        {"library": "Connector_Generic", "type": "Conn_02x10_Odd_Even", "reference": "U2", "value": "OV2640_CAMERA_IF", "x": 210, "y": 70},
        {"library": "Connector_Generic", "type": "Conn_01x08", "reference": "U3", "value": "MPU6050_CORE", "x": 210, "y": 105},
        {"library": "Connector_Generic", "type": "Conn_01x06", "reference": "U4", "value": "INMP441_CORE", "x": 210, "y": 135},
        # Charging + regulation + amplifier represented as IC-level circuit blocks
        {"library": "Connector_Generic", "type": "Conn_01x08", "reference": "U5", "value": "LIION_CHARGER_IC_CORE", "x": 85, "y": 42},
        {"library": "Connector_Generic", "type": "Conn_01x05", "reference": "U6", "value": "REGULATOR_3V3_CORE", "x": 115, "y": 42},
        {"library": "Connector_Generic", "type": "Conn_01x08", "reference": "U7", "value": "AUDIO_AMP_CORE", "x": 175, "y": 165},
        {"library": "Connector_Generic", "type": "Conn_01x10", "reference": "U8", "value": "USB_UART_BRIDGE_CORE", "x": 85, "y": 145},
        # External connectors (SMD only)
        {"library": "Connector_Generic", "type": "Conn_01x02", "reference": "J1", "value": "BATTERY_1S", "x": 55, "y": 42},
        {"library": "Connector_Generic", "type": "Conn_01x06", "reference": "J5", "value": "USBC_POWER_IN", "x": 55, "y": 25},
        {"library": "Connector_Generic", "type": "Conn_01x05", "reference": "J6", "value": "MICRO_USB_PROG", "x": 55, "y": 145},
        # Test pads replacing removed external headers
        {"library": "Connector_Generic", "type": "Conn_01x01", "reference": "TP1", "value": "TP_UART_TX", "x": 35, "y": 150},
        {"library": "Connector_Generic", "type": "Conn_01x01", "reference": "TP2", "value": "TP_UART_RX", "x": 35, "y": 153},
        {"library": "Connector_Generic", "type": "Conn_01x01", "reference": "TP3", "value": "TP_EN", "x": 35, "y": 156},
        {"library": "Connector_Generic", "type": "Conn_01x01", "reference": "TP4", "value": "TP_IO0", "x": 35, "y": 159},
        {"library": "Connector_Generic", "type": "Conn_01x01", "reference": "TP5", "value": "TP_I2C_SCL", "x": 35, "y": 75},
        {"library": "Connector_Generic", "type": "Conn_01x01", "reference": "TP6", "value": "TP_I2C_SDA", "x": 35, "y": 78},
        {"library": "Connector_Generic", "type": "Conn_01x01", "reference": "TP7", "value": "TP_SPK_P", "x": 35, "y": 170},
        {"library": "Connector_Generic", "type": "Conn_01x01", "reference": "TP8", "value": "TP_SPK_N", "x": 35, "y": 173},
        # Passives and indicators
        {"library": "Device", "type": "R", "reference": "R1", "value": "1k", "x": 98, "y": 182},
        {"library": "Device", "type": "LED", "reference": "D1", "value": "GREEN", "x": 110, "y": 182},
        {"library": "Device", "type": "R", "reference": "R2", "value": "10k", "x": 95, "y": 78},
        {"library": "Device", "type": "R", "reference": "R3", "value": "10k", "x": 105, "y": 78},
        {"library": "Device", "type": "R", "reference": "R4", "value": "10k", "x": 135, "y": 130},
        {"library": "Device", "type": "R", "reference": "R5", "value": "10k", "x": 145, "y": 130},
        {"library": "Device", "type": "C", "reference": "C1", "value": "10uF", "x": 120, "y": 52},
        {"library": "Device", "type": "C", "reference": "C2", "value": "100nF", "x": 130, "y": 52},
        {"library": "Device", "type": "C", "reference": "C3", "value": "10uF", "x": 118, "y": 30},
        {"library": "Device", "type": "C", "reference": "C4", "value": "100nF", "x": 198, "y": 142},
        {"library": "Device", "type": "C", "reference": "C5", "value": "100nF", "x": 198, "y": 110},
    ]

    for component in components:
        run_cmd(
            kicad,
            "add_schematic_component",
            {"schematicPath": str(SCH_PATH), "component": component},
        )
        print(f"Added {component['reference']}")

    footprints = {
        "U1": "RF_Module:ESP32-WROOM-32E",
        "U2": "Connector_FFC-FPC:TE_2-1734839-0_1x20-1MP_P0.5mm_Horizontal",
        "U3": "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.65x2.65mm",
        "U4": "Package_DFN_QFN:DFN-6-1EP_3x2mm_P0.5mm_EP1.65x1.35mm",
        "U5": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        "U6": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        "U7": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
        "U8": "Package_DFN_QFN:QFN-28-1EP_5x5mm_P0.5mm_EP3.35x3.35mm",
        "J1": "Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal",
        "J5": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
        "J6": "Connector_USB:USB_Micro-B_Molex-105017-0001",
        "TP1": "TestPoint:TestPoint_Pad_D1.0mm",
        "TP2": "TestPoint:TestPoint_Pad_D1.0mm",
        "TP3": "TestPoint:TestPoint_Pad_D1.0mm",
        "TP4": "TestPoint:TestPoint_Pad_D1.0mm",
        "TP5": "TestPoint:TestPoint_Pad_D1.0mm",
        "TP6": "TestPoint:TestPoint_Pad_D1.0mm",
        "TP7": "TestPoint:TestPoint_Pad_D1.0mm",
        "TP8": "TestPoint:TestPoint_Pad_D1.0mm",
        "R1": "Resistor_SMD:R_0603_1608Metric",
        "R2": "Resistor_SMD:R_0603_1608Metric",
        "R3": "Resistor_SMD:R_0603_1608Metric",
        "R4": "Resistor_SMD:R_0603_1608Metric",
        "R5": "Resistor_SMD:R_0603_1608Metric",
        "C1": "Capacitor_SMD:C_0603_1608Metric",
        "C2": "Capacitor_SMD:C_0603_1608Metric",
        "C3": "Capacitor_SMD:C_0603_1608Metric",
        "C4": "Capacitor_SMD:C_0603_1608Metric",
        "C5": "Capacitor_SMD:C_0603_1608Metric",
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

    # Rev-B net mapping baseline (component-level rails + interfaces).
    net_map = [
        ("J5", "1", "VBUS_5V"),
        ("J5", "6", "GND"),
        ("J6", "1", "VBUS_5V"),
        ("J6", "5", "GND"),
        ("J6", "2", "USB_PROG_D-"),
        ("J6", "3", "USB_PROG_D+"),
        ("J1", "1", "VBAT_RAW"),
        ("J1", "2", "GND"),
        ("U5", "1", "VBUS_5V"),
        ("U5", "2", "VBAT_RAW"),
        ("U5", "3", "VSYS"),
        ("U5", "4", "GND"),
        ("U6", "1", "VSYS"),
        ("U6", "2", "+3V3_DIG"),
        ("U6", "3", "GND"),
        ("C1", "1", "+3V3_DIG"),
        ("C1", "2", "GND"),
        ("C2", "1", "+3V3_DIG"),
        ("C2", "2", "GND"),
        ("C3", "1", "VSYS"),
        ("C3", "2", "GND"),
        ("U1", "2", "+3V3_DIG"),
        ("U1", "1", "GND"),
        ("U1", "32", "I2C_SCL"),
        ("U1", "34", "I2C_SDA"),
        ("TP5", "1", "I2C_SCL"),
        ("TP6", "1", "I2C_SDA"),
        ("R2", "1", "+3V3_DIG"),
        ("R2", "2", "I2C_SCL"),
        ("R3", "1", "+3V3_DIG"),
        ("R3", "2", "I2C_SDA"),
        ("U3", "1", "+3V3_DIG"),
        ("U3", "2", "GND"),
        ("U3", "3", "I2C_SCL"),
        ("U3", "4", "I2C_SDA"),
        ("C5", "1", "+3V3_DIG"),
        ("C5", "2", "GND"),
        ("U4", "1", "+3V3_AUD"),
        ("U4", "2", "GND"),
        ("U4", "3", "I2S_BCLK"),
        ("U4", "4", "I2S_WS"),
        ("U4", "5", "I2S_SD_IN"),
        ("U4", "6", "MIC_LR"),
        ("C4", "1", "+3V3_AUD"),
        ("C4", "2", "GND"),
        ("U1", "16", "AUD_IN"),
        ("U7", "1", "AUD_IN"),
        ("U7", "2", "SPK_OUT_P"),
        ("U7", "3", "SPK_OUT_N"),
        ("U7", "4", "+3V3_AUD"),
        ("U7", "5", "GND"),
        ("TP7", "1", "SPK_OUT_P"),
        ("TP8", "1", "SPK_OUT_N"),
        # USB-UART bridge + auto-program control path
        ("U8", "1", "VBUS_5V"),
        ("U8", "2", "GND"),
        ("U8", "3", "USB_PROG_D+"),
        ("U8", "4", "USB_PROG_D-"),
        ("U8", "5", "UART_RX_DBG"),
        ("U8", "6", "UART_TX_DBG"),
        ("U8", "7", "EN"),
        ("U8", "8", "IO0"),
        ("U8", "9", "+3V3_DIG"),
        ("U8", "10", "GND"),
        ("U1", "10", "UART_TX_DBG"),
        ("U1", "12", "UART_RX_DBG"),
        ("U1", "6", "EN"),
        ("U1", "4", "IO0"),
        ("R4", "1", "+3V3_DIG"),
        ("R4", "2", "EN"),
        ("R5", "1", "+3V3_DIG"),
        ("R5", "2", "IO0"),
        ("TP1", "1", "UART_TX_DBG"),
        ("TP2", "1", "UART_RX_DBG"),
        ("TP3", "1", "EN"),
        ("TP4", "1", "IO0"),
        ("U1", "8", "LED_STAT"),
        ("R1", "1", "LED_STAT"),
        ("R1", "2", "LED_A"),
        ("D1", "2", "LED_A"),
        ("D1", "1", "GND"),
        # Camera interface baseline nets
        ("U2", "1", "+3V3_DIG"),
        ("U2", "2", "GND"),
        ("U2", "3", "CAM_SIOC"),
        ("U2", "4", "CAM_SIOD"),
        ("U2", "5", "CAM_XCLK"),
        ("U2", "6", "CAM_PCLK"),
        ("U2", "7", "CAM_VSYNC"),
        ("U2", "8", "CAM_HREF"),
        ("U2", "9", "CAM_D0"),
        ("U2", "10", "CAM_D1"),
        ("U2", "11", "CAM_D2"),
        ("U2", "12", "CAM_D3"),
        ("U2", "13", "CAM_D4"),
        ("U2", "14", "CAM_D5"),
        ("U2", "15", "CAM_D6"),
        ("U2", "16", "CAM_D7"),
    ]

    for ref, pin, net_name in net_map:
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

    labels = [
        ("VBUS_5V", 22, 20),
        ("VBAT_RAW", 22, 24),
        ("VSYS", 22, 28),
        ("+3V3_DIG", 22, 32),
        ("+3V3_AUD", 22, 36),
        ("GND", 22, 40),
        ("I2C_SCL", 22, 48),
        ("I2C_SDA", 22, 52),
        ("USB_PROG_D+", 22, 56),
        ("USB_PROG_D-", 22, 58),
        ("I2S_BCLK", 22, 60),
        ("I2S_WS", 22, 64),
        ("I2S_SD_IN", 22, 68),
        ("AUD_IN", 22, 76),
        ("SPK_OUT_P", 22, 80),
        ("SPK_OUT_N", 22, 84),
        ("CAM_XCLK", 22, 92),
        ("CAM_PCLK", 22, 96),
        ("CAM_VSYNC", 22, 100),
        ("CAM_HREF", 22, 104),
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

    print(f"Rev-B discrete schematic population complete: {SCH_PATH}")


if __name__ == "__main__":
    main()
