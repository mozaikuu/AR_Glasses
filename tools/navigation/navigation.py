from __future__ import annotations


def plan_route(start: str, destination: str) -> list[str]:
    return [
        f"Start from {start or 'current position'}",
        "Walk forward",
        f"Arrive at {destination}",
    ]
