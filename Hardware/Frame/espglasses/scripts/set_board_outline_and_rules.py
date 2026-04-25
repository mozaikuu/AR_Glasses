from __future__ import annotations

from pathlib import Path

import pcbnew


BOARD_PATH = Path(__file__).resolve().parents[1] / "espglasses.kicad_pcb"

OUTLINE_X = 0.0
OUTLINE_Y = 0.0
OUTLINE_W = 180.0
OUTLINE_H = 50.0


def pt_mm(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD_PATH))

    # Rev-A practical rules for mixed dev-board + 0603 prototype routing.
    ds = board.GetDesignSettings()
    # KiCad SWIG API naming differs by version/build; support attribute-based fallback.
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

    # Replace Edge.Cuts with a deterministic rectangular outline.
    for drawing in list(board.GetDrawings()):
        if drawing.GetLayer() == pcbnew.Edge_Cuts:
            board.Remove(drawing)

    corners = [
        (OUTLINE_X, OUTLINE_Y),
        (OUTLINE_X + OUTLINE_W, OUTLINE_Y),
        (OUTLINE_X + OUTLINE_W, OUTLINE_Y + OUTLINE_H),
        (OUTLINE_X, OUTLINE_Y + OUTLINE_H),
        (OUTLINE_X, OUTLINE_Y),
    ]

    for start, end in zip(corners, corners[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetStart(pt_mm(*start))
        seg.SetEnd(pt_mm(*end))
        board.Add(seg)

    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"Saved board rules+outline: {BOARD_PATH}")


if __name__ == "__main__":
    main()
