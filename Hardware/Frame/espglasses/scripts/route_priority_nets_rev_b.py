from __future__ import annotations

from pathlib import Path

import pcbnew


BOARD_PATH = Path(__file__).resolve().parents[1] / "espglasses.kicad_pcb"
ROUTE_ENABLED = False


# Assign core nets so routing has deterministic net ownership.
NET_ASSIGNMENTS = [
    # USB-C power entry
    ("J5", "A1", "GND"),
    ("J5", "B1", "GND"),
    ("J5", "A12", "GND"),
    ("J5", "B12", "GND"),
    ("J5", "A4", "VBUS_5V"),
    ("J5", "B4", "VBUS_5V"),
    ("J5", "A9", "VBUS_5V"),
    ("J5", "B9", "VBUS_5V"),
    # Micro-USB programming
    ("J6", "1", "VBUS_5V"),
    ("J6", "2", "USB_PROG_D-"),
    ("J6", "3", "USB_PROG_D+"),
    ("J6", "5", "GND"),
    ("J6", "6", "GND"),
    # Power tree
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
    # MCU + debug/program
    ("U1", "1", "GND"),
    ("U1", "2", "+3V3_DIG"),
    ("U1", "4", "IO0"),
    ("U1", "6", "EN"),
    ("U1", "8", "LED_STAT"),
    ("U1", "10", "UART_TX_DBG"),
    ("U1", "12", "UART_RX_DBG"),
    ("U1", "32", "I2C_SCL"),
    ("U1", "34", "I2C_SDA"),
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
    ("R4", "1", "+3V3_DIG"),
    ("R4", "2", "EN"),
    ("R5", "1", "+3V3_DIG"),
    ("R5", "2", "IO0"),
    ("TP1", "1", "UART_TX_DBG"),
    ("TP2", "1", "UART_RX_DBG"),
    ("TP3", "1", "EN"),
    ("TP4", "1", "IO0"),
    # Status LED + basic buses
    ("R1", "1", "LED_STAT"),
    ("R1", "2", "LED_A"),
    ("D1", "1", "GND"),
    ("D1", "2", "LED_A"),
    ("R2", "1", "+3V3_DIG"),
    ("R2", "2", "I2C_SCL"),
    ("R3", "1", "+3V3_DIG"),
    ("R3", "2", "I2C_SDA"),
    ("TP5", "1", "I2C_SCL"),
    ("TP6", "1", "I2C_SDA"),
]


# First routing pass: power + programming + bring-up nets.
ROUTES = [
    ("J5", "A4", "U5", "1", "VBUS_5V", 0.40),
    ("J6", "1", "U8", "1", "VBUS_5V", 0.35),
    ("U5", "3", "U6", "1", "VSYS", 0.40),
    ("U6", "2", "U1", "2", "+3V3_DIG", 0.35),
    ("J6", "2", "U8", "4", "USB_PROG_D-", 0.25),
    ("J6", "3", "U8", "3", "USB_PROG_D+", 0.25),
    ("U8", "6", "U1", "10", "UART_TX_DBG", 0.25),
    ("U8", "5", "U1", "12", "UART_RX_DBG", 0.25),
    ("U8", "7", "U1", "6", "EN", 0.25),
    ("U8", "8", "U1", "4", "IO0", 0.25),
    ("U1", "8", "R1", "1", "LED_STAT", 0.25),
    ("R1", "2", "D1", "2", "LED_A", 0.25),
]


def _ensure_net(board: pcbnew.BOARD, net_name: str) -> pcbnew.NETINFO_ITEM:
    net = board.FindNet(net_name)
    if net is None:
        net = pcbnew.NETINFO_ITEM(board, net_name)
        board.Add(net)
    return net


def _fp(board: pcbnew.BOARD, ref: str) -> pcbnew.FOOTPRINT:
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        raise RuntimeError(f"Footprint not found: {ref}")
    return fp


def _pads_by_number(fp: pcbnew.FOOTPRINT, pad_no: str) -> list[pcbnew.PAD]:
    pads = [p for p in fp.Pads() if p.GetName() == pad_no]
    if not pads:
        raise RuntimeError(f"Pad not found: {fp.GetReference()}.{pad_no}")
    return pads


def _set_net_for_pad_number(
    board: pcbnew.BOARD,
    ref: str,
    pad_no: str,
    net_name: str,
) -> None:
    net = _ensure_net(board, net_name)
    fp = _fp(board, ref)
    for pad in _pads_by_number(fp, pad_no):
        pad.SetNet(net)


def _first_pad(board: pcbnew.BOARD, ref: str, pad_no: str) -> pcbnew.PAD:
    return _pads_by_number(_fp(board, ref), pad_no)[0]


def _pad_center_mm(pad: pcbnew.PAD) -> tuple[float, float]:
    p = pad.GetPosition()
    return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)


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
    tr.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(start_mm[0]), pcbnew.FromMM(start_mm[1])))
    tr.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(end_mm[0]), pcbnew.FromMM(end_mm[1])))
    board.Add(tr)


def _route_manhattan(
    board: pcbnew.BOARD,
    pad_a: pcbnew.PAD,
    pad_b: pcbnew.PAD,
    width_mm: float,
) -> None:
    a = _pad_center_mm(pad_a)
    b = _pad_center_mm(pad_b)
    if abs(a[0] - b[0]) < 0.01 or abs(a[1] - b[1]) < 0.01:
        _add_segment(board, pad_a.GetNetCode(), width_mm, a, b)
        return
    mid = (b[0], a[1])
    _add_segment(board, pad_a.GetNetCode(), width_mm, a, mid)
    _add_segment(board, pad_a.GetNetCode(), width_mm, mid, b)


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD_PATH))

    for ref, pad_no, net_name in NET_ASSIGNMENTS:
        _set_net_for_pad_number(board, ref, pad_no, net_name)

    if ROUTE_ENABLED:
        for src_ref, src_pad, dst_ref, dst_pad, net_name, width_mm in ROUTES:
            a = _first_pad(board, src_ref, src_pad)
            b = _first_pad(board, dst_ref, dst_pad)
            if a.GetNetname() != net_name or b.GetNetname() != net_name:
                raise RuntimeError(
                    f"Net mismatch for {src_ref}.{src_pad}->{dst_ref}.{dst_pad}: "
                    f"{a.GetNetname()} / {b.GetNetname()} expected {net_name}"
                )
            _route_manhattan(board, a, b, width_mm)
            print(f"Routed {net_name}: {src_ref}.{src_pad} -> {dst_ref}.{dst_pad}")
    else:
        print("Routing skipped (ROUTE_ENABLED=False). Nets assigned only.")

    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"Saved routed board: {BOARD_PATH}")


if __name__ == "__main__":
    main()
