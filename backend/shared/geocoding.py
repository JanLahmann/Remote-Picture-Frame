"""Reverse geocoding using OpenStreetMap Nominatim (free, no API key).

Converts GPS coordinates to human-readable place names.
Respects Nominatim's usage policy: max 1 request/second, with User-Agent.
"""

import time
from typing import Optional

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "FamilyFrame/1.0 (digitaler-bilderrahmen)"

# Simple in-memory cache to avoid repeated lookups for nearby coordinates
_cache: dict[str, str] = {}
_last_request_time: float = 0


def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """Convert lat/lon to a place name string.

    Returns a short, human-readable location like "Warnemuende, Rostock"
    or None if geocoding fails.

    Coordinates are rounded to 3 decimal places (~111m precision) for caching.
    """
    # Round for caching (3 decimals = ~111m accuracy, good enough for a photo)
    cache_key = f"{lat:.3f},{lon:.3f}"

    if cache_key in _cache:
        return _cache[cache_key]

    # Rate limiting: max 1 request per second (Nominatim policy)
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)

    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={
                "lat": lat,
                "lon": lon,
                "format": "json",
                "zoom": 14,  # City/town level
                "addressdetails": 1,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        _last_request_time = time.time()

        if resp.status_code != 200:
            return None

        data = resp.json()
        address = data.get("address", {})
        name = _format_place_name(address)

        if name:
            _cache[cache_key] = name

        return name

    except Exception:
        return None


def _format_place_name(address: dict) -> Optional[str]:
    """Format a Nominatim address into a short, readable string.

    Priority: suburb/village → city/town → state → country.
    Examples:
        - "Warnemuende, Rostock"
        - "Kreuzberg, Berlin"
        - "Schwabing, Muenchen"
        - "Sylt, Schleswig-Holstein"
    """
    parts = []

    # Most specific: suburb, village, or hamlet
    local = (
        address.get("suburb")
        or address.get("village")
        or address.get("hamlet")
        or address.get("neighbourhood")
        or address.get("town")
    )
    if local:
        parts.append(local)

    # City level
    city = (
        address.get("city")
        or address.get("municipality")
    )
    if city and city != local:
        parts.append(city)

    # If we have nothing yet, try state + country
    if not parts:
        state = address.get("state")
        country = address.get("country")
        if state:
            parts.append(state)
        if country:
            parts.append(country)

    return ", ".join(parts) if parts else None
