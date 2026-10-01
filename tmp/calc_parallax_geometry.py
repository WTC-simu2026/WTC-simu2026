from __future__ import annotations

from math import asin, atan2, cos, degrees, radians, sin, sqrt, tan


R = 6_371_008.8


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(radians, a)
    lat2, lon2 = map(radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(h))


def bearing(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(radians, a)
    lat2, lon2 = map(radians, b)
    dlon = lon2 - lon1
    y = sin(dlon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    return (degrees(atan2(y, x)) + 360) % 360


# Published/reference points (WGS84/NAD83 differences are negligible here).
CASTLE_CLINTON = (40.70347, -74.01678)
DOWNTOWN_ATHLETIC_CLUB = (40.70618, -74.01568)
WHITEHALL_BUILDING = (40.705587, -74.016023)
SOUTH_POOL = (40.7109875, -74.0131384)


for name, point in (
    ("Downtown Athletic Club", DOWNTOWN_ATHLETIC_CLUB),
    ("Whitehall Building", WHITEHALL_BUILDING),
):
    print(f"{name} -> WTC2/South Pool: {haversine(point, SOUTH_POOL):.1f} m")
    print(f"Castle Clinton -> {name}: {haversine(CASTLE_CLINTON, point):.1f} m")
    print(f"Bearing Castle Clinton -> {name}: {bearing(CASTLE_CLINTON, point):.2f} deg")

camera_to_tower = haversine(CASTLE_CLINTON, SOUTH_POOL)
camera_to_dac = haversine(CASTLE_CLINTON, DOWNTOWN_ATHLETIC_CLUB)
fraction = camera_to_dac / camera_to_tower
print(f"Castle Clinton -> WTC2/South Pool: {camera_to_tower:.1f} m")
print(f"Bearing Castle Clinton -> WTC2/South Pool: {bearing(CASTLE_CLINTON, SOUTH_POOL):.2f} deg")
angle = bearing(CASTLE_CLINTON, SOUTH_POOL) - bearing(CASTLE_CLINTON, DOWNTOWN_ATHLETIC_CLUB)
print(f"Angular separation DAC / WTC2 from Castle Clinton: {angle:.2f} deg")
print(f"Equivalent lateral offset at WTC2 range: {tan(radians(angle)) * camera_to_tower:.1f} m")
print(f"DAC distance fraction along camera-target range: {fraction:.4f}")
for aircraft_altitude in (275, 300, 325):
    los_altitude = 2 + fraction * (aircraft_altitude - 2)
    print(f"LOS height at DAC for aircraft altitude {aircraft_altitude} m: {los_altitude:.1f} m")
