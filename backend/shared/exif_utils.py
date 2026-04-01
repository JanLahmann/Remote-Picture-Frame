"""EXIF data extraction from image files.

Extracts date taken, GPS coordinates, camera info, and orientation
from JPEG/PNG/HEIC image files using Pillow.
"""

import io
from datetime import datetime
from typing import Optional

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def extract_exif(image_bytes: bytes) -> dict:
    """Extract useful EXIF data from image bytes.

    Returns dict with keys:
        - date_taken: ISO timestamp string or None
        - location: {"lat": float, "lon": float} or None
        - camera: "Make Model" string or None
        - orientation: int (1-8) or None
    """
    result = {
        "date_taken": None,
        "location": None,
        "camera": None,
        "orientation": None,
    }

    try:
        img = Image.open(io.BytesIO(image_bytes))
        exif_data = img._getexif()
        if not exif_data:
            return result
    except Exception:
        return result

    decoded = {}
    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id, tag_id)
        decoded[tag_name] = value

    # Date taken
    result["date_taken"] = _parse_exif_date(
        decoded.get("DateTimeOriginal") or decoded.get("DateTime")
    )

    # GPS coordinates
    gps_info = decoded.get("GPSInfo")
    if gps_info:
        result["location"] = _parse_gps(gps_info)

    # Camera
    make = decoded.get("Make", "").strip()
    model = decoded.get("Model", "").strip()
    if make or model:
        if make and model and model.startswith(make):
            result["camera"] = model
        elif make and model:
            result["camera"] = f"{make} {model}"
        else:
            result["camera"] = make or model

    # Orientation
    result["orientation"] = decoded.get("Orientation")

    return result


def _parse_exif_date(date_str) -> Optional[str]:
    """Parse EXIF date string to ISO format."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        return dt.isoformat() + "Z"
    except ValueError:
        return None


def _parse_gps(gps_info: dict) -> Optional[dict]:
    """Parse EXIF GPS info to lat/lon dict."""
    try:
        gps_decoded = {}
        for tag_id, value in gps_info.items():
            tag_name = GPSTAGS.get(tag_id, tag_id)
            gps_decoded[tag_name] = value

        lat = _dms_to_decimal(
            gps_decoded.get("GPSLatitude"),
            gps_decoded.get("GPSLatitudeRef", "N"),
        )
        lon = _dms_to_decimal(
            gps_decoded.get("GPSLongitude"),
            gps_decoded.get("GPSLongitudeRef", "E"),
        )

        if lat is not None and lon is not None:
            return {"lat": round(lat, 6), "lon": round(lon, 6)}
    except Exception:
        pass
    return None


def _dms_to_decimal(dms, ref: str) -> Optional[float]:
    """Convert degrees/minutes/seconds to decimal degrees."""
    if not dms:
        return None
    try:
        degrees = float(dms[0])
        minutes = float(dms[1])
        seconds = float(dms[2])
        decimal = degrees + minutes / 60 + seconds / 3600
        if ref in ("S", "W"):
            decimal = -decimal
        return decimal
    except (IndexError, TypeError, ValueError):
        return None


def generate_thumbnail(image_bytes: bytes, max_size: int = 800) -> bytes:
    """Generate a JPEG thumbnail from image bytes.

    Args:
        image_bytes: Original image data
        max_size: Maximum width or height in pixels

    Returns:
        JPEG bytes of the thumbnail
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Handle EXIF orientation
    try:
        exif = img._getexif()
        if exif:
            orientation = exif.get(274)  # 274 = Orientation tag
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
    except Exception:
        pass

    # Convert to RGB if needed (e.g. RGBA PNGs)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.thumbnail((max_size, max_size), Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()
