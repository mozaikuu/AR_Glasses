import math


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def parse_lat_lng(raw_value: str) -> tuple[float, float] | None:
    """Parse 'lat,lng' query value into float coordinates."""
    if not raw_value or "," not in raw_value:
        return None

    pieces = [part.strip() for part in raw_value.split(",", maxsplit=1)]
    if len(pieces) != 2:
        return None

    try:
        lat = float(pieces[0])
        lng = float(pieces[1])
    except ValueError:
        return None

    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None

    return lat, lng
