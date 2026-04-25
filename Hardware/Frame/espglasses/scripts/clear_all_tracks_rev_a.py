from __future__ import annotations

from pathlib import Path

import pcbnew


BOARD_PATH = Path(__file__).resolve().parents[1] / "espglasses.kicad_pcb"


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD_PATH))

    removed = 0
    for tr in list(board.GetTracks()):
        board.Remove(tr)
        removed += 1

    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"Removed {removed} tracks/vias")
    print(f"Saved board: {BOARD_PATH}")


if __name__ == "__main__":
    main()
