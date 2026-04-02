"""IBM Cloud Function: upload_api

HTTP endpoint for the web upload page. Receives photos via multipart form
POST, uploads them to OneDrive, and creates metadata records in Cloudant.

Protected by a shared family PIN code.
"""

import sys
import os
import base64
import json
import hashlib
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared import config
from shared.onedrive import upload_file, get_file_thumbnail_url
from shared.metadata import create_photo_metadata, ensure_database
from shared.exif_utils import extract_exif
from shared.geocoding import reverse_geocode

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json",
}

# Supported image MIME types
IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/heic", "image/heif",
    "image/bmp", "image/tiff",
}


def main(params: dict) -> dict:
    """Entry point for the IBM Cloud Function."""
    config.init(params)

    # Handle CORS preflight
    method = params.get("__ow_method", "post")
    if method == "options":
        return {"statusCode": 204, "headers": CORS_HEADERS}

    if method != "post":
        return {
            "statusCode": 405,
            "headers": CORS_HEADERS,
            "body": {"error": "Method not allowed"},
        }

    # Parse the request body
    body = params.get("__ow_body", "")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            # Might be base64-encoded (IBM Cloud Functions encodes binary bodies)
            try:
                decoded = base64.b64decode(body)
                body = json.loads(decoded)
            except Exception:
                return {
                    "statusCode": 400,
                    "headers": CORS_HEADERS,
                    "body": {"error": "Invalid request body"},
                }

    # Verify family PIN
    expected_pin = config.get("UPLOAD_PIN", "")
    provided_pin = body.get("pin", "")
    if expected_pin and provided_pin != expected_pin:
        return {
            "statusCode": 403,
            "headers": CORS_HEADERS,
            "body": {"error": "Falscher PIN"},
        }

    # Extract fields
    photos = body.get("photos", [])
    caption = body.get("caption", "").strip()
    description = body.get("description", "").strip()
    uploader_name = body.get("name", "").strip()

    if not photos:
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": {"error": "Keine Fotos empfangen"},
        }

    ensure_database()
    results = []
    folder_path = config.get("ONEDRIVE_FOLDER_PATH", "/FamilyFrame/photos")

    for photo in photos:
        try:
            result = _process_upload(
                photo_data=photo,
                folder_path=folder_path,
                caption=caption,
                description=description,
                uploader_name=uploader_name,
            )
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "filename": photo.get("filename", "unknown")})

    success_count = sum(1 for r in results if "error" not in r)

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": {
            "message": f"{success_count} Foto(s) hochgeladen",
            "results": results,
        },
    }


def _process_upload(
    photo_data: dict,
    folder_path: str,
    caption: str,
    description: str,
    uploader_name: str,
) -> dict:
    """Process a single photo upload."""
    filename = photo_data.get("filename", "photo.jpg")
    content_type = photo_data.get("content_type", "image/jpeg")
    data_b64 = photo_data.get("data", "")

    # Validate content type
    if content_type not in IMAGE_TYPES:
        raise ValueError(f"Nicht unterstuetztes Format: {content_type}")

    # Decode base64 image data
    image_bytes = base64.b64decode(data_b64)

    # Generate unique filename to avoid collisions
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    name_hash = hashlib.md5(image_bytes[:1024]).hexdigest()[:6]
    ext = os.path.splitext(filename)[1] or ".jpg"
    unique_filename = f"{timestamp}_{name_hash}{ext}"

    # Extract EXIF data
    exif_data = extract_exif(image_bytes)

    # Reverse geocode GPS coordinates
    location = exif_data.get("location")
    if location and location.get("lat") and location.get("lon"):
        place_name = reverse_geocode(location["lat"], location["lon"])
        if place_name:
            location["name"] = place_name

    # Upload to OneDrive
    od_result = upload_file(folder_path, unique_filename, image_bytes, content_type)
    item_id = od_result.get("id", "")

    # Get thumbnail URL
    thumbnail_url = ""
    if item_id:
        thumbnail_url = get_file_thumbnail_url(item_id) or ""

    # Create metadata record
    doc = create_photo_metadata(
        onedrive_item_id=item_id,
        filename=unique_filename,
        caption=caption,
        description=description,
        date_taken=exif_data.get("date_taken"),
        location=location,
        uploaded_by=uploader_name,
        upload_channel="web",
        thumbnail_url=thumbnail_url,
    )

    return {
        "doc_id": doc["_id"],
        "filename": unique_filename,
        "status": "uploaded",
    }
