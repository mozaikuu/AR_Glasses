from __future__ import annotations

from pathlib import Path

import pcbnew


BOARD_PATH = Path(__file__).resolve().parents[1] / "espglasses.kicad_pcb"

# First-pass envelope for a glasses-arm style board.
OUTLINE = {
    "x": 0.0,
    "y": 0.0,
    "w": 180.0,
    "h": 50.0,
}

PLACEMENTS = [
    # Core processing + camera/sensor/audio IC region
    {"ref": "U1", "value": "ESP32_WROVER_E_CORE", "footprint": "RF_Module:ESP32-WROOM-32E", "x": 145.0, "y": 26.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "U2", "value": "OV2640_CAMERA_IF", "footprint": "Connector_FFC-FPC:TE_1734839-0_1x20-1MP_P0.5mm_Horizontal", "x": 166.0, "y": 10.0, "rot": 180.0, "layer": "F.Cu"},
    {"ref": "U3", "value": "MPU6050_CORE", "footprint": "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.65x2.65mm", "x": 125.0, "y": 12.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "U4", "value": "INMP441_CORE", "footprint": "Package_LGA:LGA-6_3x4mm_P0.5mm", "x": 117.0, "y": 18.0, "rot": 90.0, "layer": "F.Cu"},
    {"ref": "U5", "value": "LIION_CHARGER_IC_CORE", "footprint": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "x": 30.0, "y": 26.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "U6", "value": "REGULATOR_3V3_CORE", "footprint": "Package_TO_SOT_SMD:SOT-223-3_TabPin2", "x": 44.0, "y": 26.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "U7", "value": "AUDIO_AMP_CORE", "footprint": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", "x": 88.0, "y": 26.0, "rot": 0.0, "layer": "F.Cu"},
    # External connectors
    {"ref": "J5", "value": "USBC_POWER_IN", "footprint": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "x": 8.0, "y": 25.0, "rot": 270.0, "layer": "F.Cu"},
    {"ref": "J1", "value": "BATTERY_1S", "footprint": "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", "x": 18.0, "y": 40.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "J2", "value": "OLED_I2C_PANEL", "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "x": 70.0, "y": 42.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "J4", "value": "UART_BOOT_DEBUG", "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", "x": 54.0, "y": 42.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "J3", "value": "SPEAKER_8OHM", "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", "x": 102.0, "y": 42.0, "rot": 0.0, "layer": "F.Cu"},
    # Passives and indicator clusters
    {"ref": "R1", "value": "1k", "footprint": "Resistor_SMD:R_0603_1608Metric", "x": 109.0, "y": 34.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "D1", "value": "GREEN", "footprint": "LED_SMD:LED_0603_1608Metric", "x": 113.0, "y": 34.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "R2", "value": "10k", "footprint": "Resistor_SMD:R_0603_1608Metric", "x": 74.0, "y": 34.0, "rot": 90.0, "layer": "F.Cu"},
    {"ref": "R3", "value": "10k", "footprint": "Resistor_SMD:R_0603_1608Metric", "x": 78.0, "y": 34.0, "rot": 90.0, "layer": "F.Cu"},
    {"ref": "R4", "value": "10k", "footprint": "Resistor_SMD:R_0603_1608Metric", "x": 121.0, "y": 23.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "R5", "value": "10k", "footprint": "Resistor_SMD:R_0603_1608Metric", "x": 125.0, "y": 23.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "C1", "value": "10uF", "footprint": "Capacitor_SMD:C_0603_1608Metric", "x": 47.0, "y": 32.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "C2", "value": "100nF", "footprint": "Capacitor_SMD:C_0603_1608Metric", "x": 51.0, "y": 32.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "C3", "value": "10uF", "footprint": "Capacitor_SMD:C_0603_1608Metric", "x": 34.0, "y": 32.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "C4", "value": "100nF", "footprint": "Capacitor_SMD:C_0603_1608Metric", "x": 95.0, "y": 32.0, "rot": 0.0, "layer": "F.Cu"},
    {"ref": "C5", "value": "100nF", "footprint": "Capacitor_SMD:C_0603_1608Metric", "x": 121.0, "y": 16.0, "rot": 0.0, "layer": "F.Cu"},
]


def pt_mm(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def set_rules(board: pcbnew.BOARD) -> None:
    ds = board.GetDesignSettings()
    if hasattr(ds, "SetMinClearance"):
        ds.SetMinClearance(pcbnew.FromMM(0.2))
    elif hasattr(ds, "m_MinClearance"):
        ds.m_MinClearance = pcbnew.FromMM(0.2)

    if hasattr(ds, "SetMinTrackWidth"):
        ds.SetMinTrackWidth(pcbnew.FromMM(0.2))
    elif hasattr(ds, "m_TrackMinWidth"):
        ds.m_TrackMinWidth = pcbnew.FromMM(0.2)

    if hasattr(ds, "SetMinViaDiameter"):
        ds.SetMinViaDiameter(pcbnew.FromMM(0.6))
    elif hasattr(ds, "m_ViasMinSize"):
        ds.m_ViasMinSize = pcbnew.FromMM(0.6)

    if hasattr(ds, "SetMinViaDrill"):
        ds.SetMinViaDrill(pcbnew.FromMM(0.3))
    elif hasattr(ds, "m_ViasMinDrill"):
        ds.m_ViasMinDrill = pcbnew.FromMM(0.3)


def reset_outline(board: pcbnew.BOARD) -> None:
    for drawing in list(board.GetDrawings()):
        if drawing.GetLayer() == pcbnew.Edge_Cuts:
            board.Remove(drawing)

    x = OUTLINE["x"]
    y = OUTLINE["y"]
    w = OUTLINE["w"]
    h = OUTLINE["h"]
    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]

    for start, end in zip(corners, corners[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetStart(pt_mm(*start))
        seg.SetEnd(pt_mm(*end))
        board.Add(seg)


def clear_existing_footprints(board: pcbnew.BOARD) -> None:
    for footprint in list(board.GetFootprints()):
        board.Remove(footprint)


def load_footprint(footprint_id: str):
    if ":" not in footprint_id:
        raise ValueError(f"Invalid footprint id: {footprint_id}")
    lib, name = footprint_id.split(":", 1)
    lib_path = Path(f"D:/Program Files/KiCad/9.0/share/kicad/footprints/{lib}.pretty")
    if not lib_path.exists():
        lib_path = Path(f"C:/Program Files/KiCad/9.0/share/kicad/footprints/{lib}.pretty")
    if not lib_path.exists():
        raise RuntimeError(f"Footprint library not found: {lib}")

    lib_path_str = str(lib_path)
    try:
        plugin = pcbnew.GetPluginForPath(lib_path_str)
        module = plugin.FootprintLoad(lib_path_str, name, False)
    except Exception as exc:
        raise RuntimeError(f"Failed to load footprint: {footprint_id}") from exc
    if module is None:
        raise RuntimeError(f"Footprint load returned null: {footprint_id}")
    if module is None:
        raise RuntimeError(f"Failed to load footprint {footprint_id}")
    return module


def place_components(board: pcbnew.BOARD) -> None:
    for item in PLACEMENTS:
        try:
            module = load_footprint(item["footprint"])
        except Exception as exc:
            raise RuntimeError(f"Failed loading {item['ref']} footprint {item['footprint']}") from exc
        module.SetReference(item["ref"])
        module.SetValue(item["value"])
        module.SetPosition(pt_mm(item["x"], item["y"]))
        module.SetOrientation(pcbnew.EDA_ANGLE(item["rot"], pcbnew.DEGREES_T))
        board.Add(module)

        if item["layer"] == "B.Cu" and not module.IsFlipped():
            module.Flip(module.GetPosition(), False)


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD_PATH))
    set_rules(board)
    reset_outline(board)
    clear_existing_footprints(board)
    place_components(board)
    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"Saved Rev-B PCB bootstrap: {BOARD_PATH}")


if __name__ == "__main__":
    main()