from __future__ import annotations

from pathlib import Path

import pcbnew


BOARD_PATH = Path(__file__).resolve().parents[1] / "espglasses.kicad_pcb"


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD_PATH))

    r1 = board.FindFootprintByReference("R1")
    d1 = board.FindFootprintByReference("D1")
    if r1 is None or d1 is None:
        raise RuntimeError("Missing R1 or D1 footprint")

    r1_p2 = r1.FindPadByNumber("2")
    d1_p2 = d1.FindPadByNumber("2")
    if r1_p2 is None or d1_p2 is None:
        raise RuntimeError("Missing R1.2 or D1.2 pad")

    if r1_p2.GetNetname() != "LED_A" or d1_p2.GetNetname() != "LED_A":
        raise RuntimeError(
            f"Net mismatch: R1.2={r1_p2.GetNetname()} D1.2={d1_p2.GetNetname()}"
        )

    tr = pcbnew.PCB_TRACK(board)
    tr.SetLayer(pcbnew.F_Cu)
    tr.SetNetCode(r1_p2.GetNetCode())
    tr.SetWidth(pcbnew.FromMM(0.25))
    tr.SetStart(r1_p2.GetPosition())
    tr.SetEnd(d1_p2.GetPosition())
    board.Add(tr)

    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print("Routed LED_A: R1.2 -> D1.2")
    print(f"Saved board: {BOARD_PATH}")


if __name__ == "__main__":
    main()
