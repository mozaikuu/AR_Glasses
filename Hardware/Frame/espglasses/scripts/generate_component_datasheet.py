from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


OUT_PATH = Path(__file__).resolve().parents[1] / "bom" / "COMPONENT_DATASHEET.md"


@dataclass(frozen=True)
class Component:
    ref: str
    part: str
    package: str
    role: str
    rail_or_signal: str
    note: str


COMPONENTS: list[Component] = [
    Component("U1", "ESP32-WROVER-E", "Module", "Main MCU + Wi-Fi/BLE", "+3V3_DIG", "Camera-capable ESP32 core"),
    Component("U2", "OV2640", "Camera sensor module/FFC", "Image sensor", "CAM_*", "Parallel camera interface block"),
    Component("U3", "MPU-6050", "QFN (module-equivalent support)", "6-axis IMU", "I2C_*", "I2C sensor"),
    Component("U4", "INMP441", "LGA", "Digital MEMS microphone", "I2S_*", "I2S microphone"),
    Component("U5", "Li-ion charger IC (Type-C input)", "SOP/QFN", "Battery charging", "VBUS_5V/VBAT_RAW", "Equivalent of purchased Type-C charger board"),
    Component("U6", "3.3V regulator IC", "SOT-223/SOT-23-5", "System regulation", "VSYS/+3V3_DIG", "Equivalent of purchased regulator stage"),
    Component("U7", "Audio amplifier IC", "SOP/QFN", "Speaker drive", "AUD_IN/SPK_OUT", "For 8 ohm 0.5W speaker"),
    Component("J1", "Li-ion battery connector", "2-pin JST", "Battery input", "VBAT_RAW", "3.7V 1000mAh battery"),
    Component("J2", "OLED panel connector", "4-pin header/FFC", "Display interface", "I2C_SCL/I2C_SDA", "1.3 inch I2C OLED"),
    Component("J3", "Camera connector", "FFC/header", "Camera link", "CAM_*", "OV2640 connection"),
    Component("J4", "Speaker connector", "2-pin", "Audio transducer output", "SPK_OUT", "20mm 8 ohm speaker"),
    Component("J5", "UART/boot header", "1x6 2.54mm", "Debug/programming", "UART/EN/IO0", "Bring-up and flashing"),
    Component("D1", "Status LED", "0603", "Power/status indication", "LED_STAT", "User-visible status"),
    Component("R1", "1k", "0603", "LED current limit", "LED_STAT", "Status LED resistor"),
    Component("R2", "10k", "0603", "I2C pull-up", "I2C_SCL", "Bus pull-up"),
    Component("R3", "10k", "0603", "I2C pull-up", "I2C_SDA", "Bus pull-up"),
    Component("R4", "10k", "0603", "EN pull-up", "EN", "ESP32 enable strap"),
    Component("R5", "10k", "0603", "IO0 pull-up", "IO0", "ESP32 boot strap"),
    Component("C1", "10uF", "0603/0805", "Bulk decoupling", "+3V3_DIG", "Near ESP32/regulator"),
    Component("C2", "100nF", "0603", "HF decoupling", "+3V3_DIG", "Near ESP32 power pins"),
    Component("C3", "10uF", "0603/0805", "Regulator output bulk", "+3V3_DIG", "Regulator stability"),
    Component("C4", "100nF", "0603", "Mic decoupling", "+3V3_AUD", "Near INMP441"),
    Component("C5", "100nF", "0603", "IMU decoupling", "+3V3_DIG", "Near MPU-6050"),
    Component("X1", "HW-104 (exact variant pending)", "Unknown", "Unresolved purchased module", "TBD", "Needs exact module identification before schematic lock"),
]


def render_markdown(items: list[Component]) -> str:
    lines: list[str] = []
    lines.append("# Component Datasheet (Initial Concrete Set)")
    lines.append("")
    lines.append("This file is generated from the concrete purchased-part implementation model.")
    lines.append("Entries are the individual component-level building blocks for Rev-B decomposition.")
    lines.append("")
    lines.append("| Ref | Part | Package | Role | Rail/Signal | Notes |")
    lines.append("|---|---|---|---|---|---|")
    for c in items:
        lines.append(
            f"| {c.ref} | {c.part} | {c.package} | {c.role} | {c.rail_or_signal} | {c.note} |"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- HW-104 is intentionally marked unresolved until exact module function is confirmed.")
    lines.append("- Final manufacturer part numbers and exact footprints should be locked before fabrication.")
    lines.append("- This file is intended to be updated as schematic references are finalized.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(render_markdown(COMPONENTS), encoding="utf-8")
    print(f"Wrote datasheet: {OUT_PATH}")
    print(f"Component count: {len(COMPONENTS)}")


if __name__ == "__main__":
    main()
