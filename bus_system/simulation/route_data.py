from typing import TypedDict


class RouteStop(TypedDict):
    index: int
    name: str


ROUTE_NAME = "NMU Bus Route #1"

# Approximate OpenStreetMap-aligned corridor from Mansoura city center to New Mansoura University.
ROUTE_POINTS: list[tuple[float, float]] = [
    (31.0409, 31.3785),
    (31.0534, 31.3607),
    (31.0708, 31.3336),
    (31.0928, 31.3002),
    (31.1183, 31.2615),
    (31.1445, 31.2225),
    (31.1720, 31.1838),
    (31.2018, 31.1469),
    (31.2301, 31.1120),
    (31.2576, 31.0815),
    (31.2849, 31.0526),
    (31.3112, 31.0241),
    (31.3368, 30.9964),
    (31.3612, 30.9696),
    (31.3851, 30.9441),
    (31.4089, 30.9194),
    (31.4314, 30.8950),
    (31.4513, 30.8752),
    (31.4684, 30.8570),
    (31.4849, 30.8404),
]

VIRTUAL_STOPS: list[RouteStop] = [
    {"index": 0, "name": "Mansoura Central Terminal"},
    {"index": 4, "name": "Talkha Transfer Point"},
    {"index": 8, "name": "Highway Service Stop"},
    {"index": 12, "name": "New Mansoura Gate 1"},
    {"index": 16, "name": "NMU Residential Area"},
    {"index": 19, "name": "NMU Main Campus"},
]

DAILY_SCHEDULE = {
    "route_start": "07:15",
    "leave_mansoura": "07:45",
}

DRIVER_INFO = {
    "name": "Captain Mahmoud Eid",
    "phone": "01028606576",
    "license": "NMU-BUS-DR-014",
}
