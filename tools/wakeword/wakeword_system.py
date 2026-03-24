from __future__ import annotations


class WakewordSystem:
    def __init__(self) -> None:
        self.state = "IDLE"

    def start(self) -> None:
        self.state = "ACTIVE"

    def stop(self) -> None:
        self.state = "IDLE"


wakeword_system = WakewordSystem()
