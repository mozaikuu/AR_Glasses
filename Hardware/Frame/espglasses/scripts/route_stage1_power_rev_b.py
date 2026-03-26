from __future__ import annotations

from pathlib import Path

import pcbnew


BOARD_PATH = Path(__file__).resolve().parents[1] / "espglasses.kicad_pcb"


def mm(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def pad(board: pcbnew.BOARD, ref: str, pad_no: str) -> pcbnew.PAD:
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        raise RuntimeError(f"Footprint not found: {ref}")
    p = fp.FindPadByNumber(pad_no)
    if p is None:
        raise RuntimeError(f"Pad not found: {ref}.{pad_no}")
    return p


def add_segment(
    board: pcbnew.BOARD,
    net_code: int,
    width_mm: float,
    a: tuple[float, float],
    b: tuple[float, float],
) -> None:
    tr = pcbnew.PCB_TRACK(board)
    tr.SetLayer(pcbnew.F_Cu)
    tr.SetNetCode(net_code)
    tr.SetWidth(pcbnew.FromMM(width_mm))
    tr.SetStart(mm(a[0], a[1]))
    tr.SetEnd(mm(b[0], b[1]))
    board.Add(tr)


def route_with_waypoints(
    board: pcbnew.BOARD,
    src: pcbnew.PAD,
    dst: pcbnew.PAD,
    width_mm: float,
    waypoints: list[tuple[float, float]],
) -> None:
    if src.GetNetCode() != dst.GetNetCode():
        raise RuntimeError(
            f"Net mismatch: {src.GetNetname()} vs {dst.GetNetname()}"
        )

    points = []
    ps = src.GetPosition()
    pd = dst.GetPosition()
    points.append((pcbnew.ToMM(ps.x), pcbnew.ToMM(ps.y)))
    points.extend(waypoints)
    points.append((pcbnew.ToMM(pd.x), pcbnew.ToMM(pd.y)))

    for a, b in zip(points, points[1:]):
        add_segment(board, src.GetNetCode(), width_mm, a, b)


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD_PATH))

    routes = [
        # VBUS trunk
        ("J5", "A4", "J6", "1", 0.35, [(14.0, 22.55), (14.0, 23.70)]),
        ("J6", "1", "U5", "1", 0.35, []),
        ("U5", "1", "U8", "1", 0.35, [(42.0, 23.095), (42.0, 23.50)]),
        # Battery and charger/regulator path
        ("J1", "1", "U5", "2", 0.35, [(24.0, 39.15), (24.0, 24.365)]),
        ("U5", "3", "U6", "1", 0.35, [(36.0, 25.635), (36.0, 22.70)]),
        ("U5", "3", "C3", "1", 0.30, [(31.0, 25.635), (31.0, 33.0)]),
        # +3V3_DIG distribution
        ("U6", "2", "C1", "1", 0.30, [(44.5, 25.0), (44.5, 33.0)]),
        ("U6", "2", "C2", "1", 0.30, [(48.0, 25.0), (48.0, 33.0)]),
        ("U6", "2", "U8", "9", 0.30, [(55.0, 25.0), (55.0, 29.0), (69.0, 29.0)]),
        ("U8", "9", "U1", "2", 0.30, [(100.0, 29.0), (100.0, 34.01)]),
        # Ground backbone
        ("J6", "5", "U5", "4", 0.35, []),
        ("U5", "4", "U6", "3", 0.35, []),
        ("U6", "3", "U8", "10", 0.35, [(55.0, 27.30), (55.0, 27.45)]),
        ("J1", "2", "J6", "5", 0.35, [(20.0, 39.15), (20.0, 26.30)]),
        ("U8", "10", "U1", "1", 0.35, [(69.5, 32.74)]),
    ]

    for sref, spad, dref, dpad, width, wps in routes:
        s = pad(board, sref, spad)
        d = pad(board, dref, dpad)
        route_with_waypoints(board, s, d, width, wps)
        print(f"Routed {s.GetNetname()}: {sref}.{spad} -> {dref}.{dpad}")

    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"Saved board: {BOARD_PATH}")


if __name__ == "__main__":
    main()
