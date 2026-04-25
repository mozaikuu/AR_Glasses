from __future__ import annotations

import os
from pathlib import Path

import pcbnew


BOARD_PATH = Path(__file__).resolve().parents[1] / "espglasses.kicad_pcb"

# First-pass board outline for frame arm-style prototype (mm)
OUTLINE = {
    "x": 0.0,
    "y": 0.0,
    "w": 170.0,
    "h": 45.0,
}

# Deterministic component floorplan, grouped by function.
PLACEMENTS = [
    # Core RF module kept to the right to leave antenna keepout toward board edge.
    {
        "ref": "U1",
        "value": "ESP32_DEV_BOARD_PIN_BREAKOUT",
        "footprint": "RF_Module:ESP32-WROOM-32",
        "x": 136.0,
        "y": 22.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
    # Left-side I/O and power connectors
    {
        "ref": "J1",
        "value": "BATTERY_1S",
        "footprint": "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
        "x": 12.0,
        "y": 34.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
    {
        "ref": "J2",
        "value": "OLED_SH1106_I2C",
        "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
        "x": 30.0,
        "y": 34.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
    {
        "ref": "J3",
        "value": "TOUCH_INPUTS",
        "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        "x": 48.0,
        "y": 34.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
    {
        "ref": "J4",
        "value": "AUDIO_OUT_MONO",
        "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        "x": 66.0,
        "y": 34.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
    {
        "ref": "J5",
        "value": "UART_BOOT_DEBUG",
        "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
        "x": 86.0,
        "y": 34.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
    {
        "ref": "J6",
        "value": "LED_STATUS",
        "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        "x": 106.0,
        "y": 34.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
    # Audio passives near analog output area
    {
        "ref": "R2",
        "value": "10k",
        "footprint": "Resistor_SMD:R_0603_1608Metric",
        "x": 70.0,
        "y": 20.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
    {
        "ref": "R3",
        "value": "10k",
        "footprint": "Resistor_SMD:R_0603_1608Metric",
        "x": 74.0,
        "y": 20.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
    # Power decoupling near module supply
    {
        "ref": "C1",
        "value": "10uF",
        "footprint": "Capacitor_SMD:C_0603_1608Metric",
        "x": 118.0,
        "y": 28.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
    {
        "ref": "C2",
        "value": "100nF",
        "footprint": "Capacitor_SMD:C_0603_1608Metric",
        "x": 122.0,
        "y": 28.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
    # Status LED cluster
    {
        "ref": "R1",
        "value": "1k",
        "footprint": "Resistor_SMD:R_0603_1608Metric",
        "x": 112.0,
        "y": 20.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
    {
        "ref": "D1",
        "value": "GREEN",
        "footprint": "LED_SMD:LED_0603_1608Metric",
        "x": 116.0,
        "y": 20.0,
        "rot": 0.0,
        "layer": "F.Cu",
    },
]


def pt_mm(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def clear_outline(board: pcbnew.BOARD) -> None:
    for drawing in list(board.GetDrawings()):
        if drawing.GetLayer() == pcbnew.Edge_Cuts:
            board.Remove(drawing)


def add_outline(board: pcbnew.BOARD, x: float, y: float, w: float, h: float) -> None:
    corners = [
        (x, y),
        (x + w, y),
        (x + w, y + h),
        (x, y + h),
        (x, y),
    ]
    for start, end in zip(corners, corners[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetStart(pt_mm(*start))
        seg.SetEnd(pt_mm(*end))
        board.Add(seg)


def remove_existing_footprints(board: pcbnew.BOARD, refs: set[str]) -> None:
    for footprint in list(board.GetFootprints()):
        if footprint.GetReference() in refs:
            board.Remove(footprint)


def load_footprint(footprint_id: str):
    if ":" not in footprint_id:
        raise ValueError(f"Footprint '{footprint_id}' must be in 'Library:Name' format")
    lib, name = footprint_id.split(":", 1)

    # Try library nickname first (works when fp-lib-table is loaded).
    try:
        module = pcbnew.FootprintLoad(lib, name)
        if module is not None:
            return module
    except Exception:
        # Some KiCad Python runtimes return a null plugin when nickname tables are unavailable.
        module = None

    # Fallback to KiCad install footprint path when nickname resolution is unavailable.
    search_roots = []
    env_fp_dir = os.environ.get("KICAD9_FOOTPRINT_DIR")
    if env_fp_dir:
        search_roots.append(Path(env_fp_dir))
    search_roots.append(Path("D:/Program Files/KiCad/9.0/share/kicad/footprints"))
    search_roots.append(Path("C:/Program Files/KiCad/9.0/share/kicad/footprints"))

    for root in search_roots:
        lib_path = root / f"{lib}.pretty"
        if lib_path.exists():
            module = pcbnew.FootprintLoad(str(lib_path), name)
            if module is not None:
                return module

    if module is None:
        raise RuntimeError(f"Failed to load footprint {footprint_id}")
    return module


def place_components(board: pcbnew.BOARD) -> None:
    refs = {item["ref"] for item in PLACEMENTS}
    remove_existing_footprints(board, refs)

    for item in PLACEMENTS:
        module = load_footprint(item["footprint"])
        module.SetReference(item["ref"])
        module.SetValue(item["value"])
        module.SetPosition(pt_mm(item["x"], item["y"]))
        module.SetOrientation(pcbnew.EDA_ANGLE(item["rot"], pcbnew.DEGREES_T))
        board.Add(module)

        if item["layer"] == "B.Cu" and not module.IsFlipped():
            module.Flip(module.GetPosition(), False)


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD_PATH))

    clear_outline(board)
    add_outline(board, OUTLINE["x"], OUTLINE["y"], OUTLINE["w"], OUTLINE["h"])
    place_components(board)

    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"Saved board: {BOARD_PATH}")


if __name__ == "__main__":
    main()
