from __future__ import annotations

from pathlib import Path

import pcbnew


BOARD_PATH = Path(__file__).resolve().parents[1] / "espglasses.kicad_pcb"

# First routing batch: power decoupling + I2C + status LED chain.
ROUTES = [
    ("U1", "8", "R1", "1", "LED_STAT", 0.25),
    ("R1", "2", "D1", "2", "LED_A", 0.25),
    ("U1", "32", "J2", "3", "I2C_SCL", 0.25),
    ("U1", "34", "J2", "4", "I2C_SDA", 0.25),
    ("U1", "2", "C1", "1", "+3V3_DIG", 0.30),
    ("U1", "2", "C2", "1", "+3V3_DIG", 0.30),
]


def _pad_center_mm(pad: pcbnew.PAD) -> tuple[float, float]:
    p = pad.GetPosition()
    return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)


def _fp(board: pcbnew.BOARD, ref: str) -> pcbnew.FOOTPRINT:
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        raise RuntimeError(f"Footprint not found: {ref}")
    return fp


def _pad(board: pcbnew.BOARD, ref: str, pad_no: str) -> pcbnew.PAD:
    fp = _fp(board, ref)
    pad = fp.FindPadByNumber(pad_no)
    if pad is None:
        raise RuntimeError(f"Pad not found: {ref}.{pad_no}")
    return pad


def _add_segment(
    board: pcbnew.BOARD,
    net_code: int,
    width_mm: float,
    start_mm: tuple[float, float],
    end_mm: tuple[float, float],
) -> None:
    tr = pcbnew.PCB_TRACK(board)
    tr.SetLayer(pcbnew.F_Cu)
    tr.SetNetCode(net_code)
    tr.SetWidth(pcbnew.FromMM(width_mm))
    tr.SetStart(
        pcbnew.VECTOR2I(pcbnew.FromMM(start_mm[0]), pcbnew.FromMM(start_mm[1]))
    )
    tr.SetEnd(
        pcbnew.VECTOR2I(pcbnew.FromMM(end_mm[0]), pcbnew.FromMM(end_mm[1]))
    )
    board.Add(tr)


def _route_manhattan(
    board: pcbnew.BOARD,
    pad_a: pcbnew.PAD,
    pad_b: pcbnew.PAD,
    width_mm: float,
) -> None:
    a = _pad_center_mm(pad_a)
    b = _pad_center_mm(pad_b)
    # Route horizontal then vertical to keep deterministic paths.
    mid = (b[0], a[1])
    net_code = pad_a.GetNetCode()
    _add_segment(board, net_code, width_mm, a, mid)
    _add_segment(board, net_code, width_mm, mid, b)


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD_PATH))

    for src_ref, src_pad, dst_ref, dst_pad, net_name, width_mm in ROUTES:
        a = _pad(board, src_ref, src_pad)
        b = _pad(board, dst_ref, dst_pad)

        if a.GetNetname() != net_name or b.GetNetname() != net_name:
            raise RuntimeError(
                f"Net mismatch for {src_ref}.{src_pad}->{dst_ref}.{dst_pad}: "
                f"got {a.GetNetname()} and {b.GetNetname()}, expected {net_name}"
            )

        _route_manhattan(board, a, b, width_mm)
        print(f"Routed {net_name}: {src_ref}.{src_pad} -> {dst_ref}.{dst_pad}")

    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"Saved routed board: {BOARD_PATH}")


if __name__ == "__main__":
    main()
