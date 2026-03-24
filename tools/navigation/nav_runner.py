from __future__ import annotations


class NavRunner:
    def __init__(self, steps: list[str]) -> None:
        self._steps = steps
        self._index = 0

    def next(self) -> str:
        if not self._steps:
            return "No route"
        step = self._steps[min(self._index, len(self._steps) - 1)]
        self._index = min(self._index + 1, len(self._steps) - 1)
        return step
