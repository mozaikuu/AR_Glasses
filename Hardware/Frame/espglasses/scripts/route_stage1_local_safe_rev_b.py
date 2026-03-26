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


def add_seg(board: pcbnew.BOARD, net_code: int, width_mm: float, a: tuple[float, float], b: tuple[float, float]) -> None:
    tr = pcbnew.PCB_TRACK(board)
    tr.SetLayer(pcbnew.F_Cu)
    tr.SetNetCode(net_code)
    tr.SetWidth(pcbnew.FromMM(width_mm))
    tr.SetStart(mm(a[0], a[1]))
    tr.SetEnd(mm(b[0], b[1]))
    board.Add(tr)


def route(board: pcbnew.BOARD, s: pcbnew.PAD, d: pcbnew.PAD, width_mm: float) -> None:
    if s.GetNetCode() != d.GetNetCode():
        raise RuntimeError(f"Net mismatch {s.GetNetname()} vs {d.GetNetname()}")
    ps = s.GetPosition()
    pd = d.GetPosition()
    a = (pcbnew.ToMM(ps.x), pcbnew.ToMM(ps.y))
    b = (pcbnew.ToMM(pd.x), pcbnew.ToMM(pd.y))
    add_seg(board, s.GetNetCode(), width_mm, a, b)


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD_PATH))

    # Very local, low-risk routes only.
    pairs = [
        ("U6", "2", "C1", "1", 0.30),
        ("U6", "2", "C2", "1", 0.30),
        ("U5", "3", "C3", "1", 0.30),
        ("U1", "8", "R1", "1", 0.25),
        ("R1", "2", "D1", "2", 0.25),
        ("R2", "2", "TP5", "1", 0.25),
        ("R3", "2", "TP6", "1", 0.25),
    ]

    for sref, spad, dref, dpad, w in pairs:
        s = pad(board, sref, spad)
        d = pad(board, dref, dpad)
        route(board, s, d, w)
        print(f"Routed {s.GetNetname()}: {sref}.{spad} -> {dref}.{dpad}")

    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"Saved board: {BOARD_PATH}")


if __name__ == "__main__":
    main()
