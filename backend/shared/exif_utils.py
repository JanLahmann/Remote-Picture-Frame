"""EXIF data extraction and embedding for image files.

Extracts date taken, GPS coordinates, camera info, and orientation
from JPEG/PNG/HEIC image files using Pillow.

Also supports embedding FamilyFrame metadata (caption, uploader, etc.)
into EXIF before uploading to OneDrive, so the RPi can read it during sync.
"""

import io
import json
from datetime import datetime
from typing import Optional

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


# EXIF tag IDs
TAG_IMAGE_DESCRIPTION = 270
TAG_ARTIST = 315
TAG_USER_COMMENT = 37510
TAG_EXIF_IFD = 34665


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


def embed_metadata(
    image_bytes: bytes,
    caption: str = "",
    uploaded_by: str = "",
    description: str = "",
    location_name: str = "",
) -> bytes:
    """Embed FamilyFrame metadata into JPEG EXIF fields.

    Writes metadata into standard EXIF tags so it survives cloud storage
    round-trips (OneDrive → rclone → RPi). The RPi reads these during sync
    and passes them to enhance_photo() for burning into the image overlay.

    Fields used:
        - ImageDescription (tag 270): caption text
        - Artist (tag 315): uploader name
        - UserComment (tag 37510): JSON blob with all fields

    Args:
        image_bytes: Original JPEG bytes
        caption: Caption text (e.g. "Urlaub an der Ostsee")
        uploaded_by: Uploader name (e.g. "Anna")
        description: Optional description
        location_name: Optional place name (e.g. "Warnemuende")

    Returns:
        Modified JPEG bytes with embedded EXIF, or original bytes on error.
    """
    if not caption and not uploaded_by and not description and not location_name:
        return image_bytes

    try:
        import piexif
    except ImportError:
        # piexif not available — try Pillow-only approach
        return _embed_metadata_pillow(
            image_bytes, caption, uploaded_by, description, location_name
        )

    try:
        exif_dict = piexif.load(image_bytes)
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

    # Write standard EXIF fields
    if caption:
        exif_dict["0th"][TAG_IMAGE_DESCRIPTION] = caption.encode("utf-8")
    if uploaded_by:
        exif_dict["0th"][TAG_ARTIST] = uploaded_by.encode("utf-8")

    # Write JSON blob into UserComment for structured access on RPi
    meta_json = json.dumps(
        {
            "caption": caption,
            "uploaded_by": uploaded_by,
            "description": description,
            "location": location_name,
            "source": "familyframe-web",
        },
        ensure_ascii=False,
    )
    # UserComment requires a charset prefix (8 bytes)
    user_comment = b"UNICODE\x00" + meta_json.encode("utf-8")
    exif_dict["Exif"][TAG_USER_COMMENT] = user_comment

    try:
        exif_bytes = piexif.dump(exif_dict)
        # Insert EXIF into image
        output = io.BytesIO()
        piexif.insert(exif_bytes, image_bytes, output)
        return output.getvalue()
    except Exception:
        return image_bytes


def _embed_metadata_pillow(
    image_bytes: bytes,
    caption: str,
    uploaded_by: str,
    description: str,
    location_name: str,
) -> bytes:
    """Fallback: embed metadata by re-saving with Pillow and PngInfo/EXIF.

    Pillow's EXIF write support is limited, so we write what we can
    (ImageDescription, Artist) via the info dict approach, and store the
    full JSON in a text chunk for PNG or fall back gracefully for JPEG.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # For JPEG, Pillow can preserve existing EXIF and we can modify it
        exif = img.getexif()
        if caption:
            exif[TAG_IMAGE_DESCRIPTION] = caption
        if uploaded_by:
            exif[TAG_ARTIST] = uploaded_by

        # Write JSON into UserComment via Exif IFD
        meta_json = json.dumps(
            {
                "caption": caption,
                "uploaded_by": uploaded_by,
                "description": description,
                "location": location_name,
                "source": "familyframe-web",
            },
            ensure_ascii=False,
        )
        exif_ifd = exif.get_ifd(TAG_EXIF_IFD)
        exif_ifd[TAG_USER_COMMENT] = b"UNICODE\x00" + meta_json.encode("utf-8")

        output = io.BytesIO()
        img.save(output, format=img.format or "JPEG", exif=exif.tobytes(), quality=95)
        return output.getvalue()
    except Exception:
        return image_bytes


def read_familyframe_metadata(image_bytes: bytes) -> dict:
    """Read FamilyFrame metadata from EXIF UserComment.

    Returns dict with keys: caption, uploaded_by, description, location.
    Returns empty values if no FamilyFrame metadata is found.
    """
    result = {"caption": "", "uploaded_by": "", "description": "", "location": ""}

    try:
        img = Image.open(io.BytesIO(image_bytes))
        exif_data = img._getexif()
        if not exif_data:
            return result
    except Exception:
        return result

    # Try UserComment (JSON blob) first — most complete
    user_comment = exif_data.get(TAG_USER_COMMENT)
    if user_comment:
        try:
            # Strip charset prefix (first 8 bytes)
            if isinstance(user_comment, bytes) and len(user_comment) > 8:
                json_str = user_comment[8:].decode("utf-8")
                meta = json.loads(json_str)
                if meta.get("source") == "familyframe-web":
                    result["caption"] = meta.get("caption", "")
                    result["uploaded_by"] = meta.get("uploaded_by", "")
                    result["description"] = meta.get("description", "")
                    result["location"] = meta.get("location", "")
                    return result
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    # Fall back to standard EXIF fields
    decoded = {}
    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id, tag_id)
        decoded[tag_name] = value

    if decoded.get("ImageDescription"):
        result["caption"] = str(decoded["ImageDescription"]).strip()
    if decoded.get("Artist"):
        result["uploaded_by"] = str(decoded["Artist"]).strip()

    return result


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
