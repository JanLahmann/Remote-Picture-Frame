"""IBM Cloud Function: process_new_photo

Triggered by Microsoft Graph API webhook when new files are added to the
OneDrive /FamilyFrame/photos/ folder. Extracts EXIF data, generates a
thumbnail, and creates a metadata record in Cloudant.

Also handles the Graph API subscription validation handshake.
"""

import sys
import os

# Add parent paths for shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared import config
from shared.onedrive import get_file_metadata, get_file_content, get_file_thumbnail_url, move_file
from shared.metadata import create_photo_metadata, find_by_onedrive_id, ensure_database
from shared.exif_utils import extract_exif
from shared.geocoding import reverse_geocode

# Image file extensions we process
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".bmp", ".tiff"}


def main(params: dict) -> dict:
    """Entry point for the IBM Cloud Function.

    Handles two cases:
    1. Graph API subscription validation (GET with validationToken)
    2. Change notification (POST with notification payload)
    """
    config.init(params)

    # --- Subscription validation handshake ---
    validation_token = params.get("validationToken")
    if validation_token:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/plain"},
            "body": validation_token,
        }

    # --- Process change notifications ---
    notifications = params.get("value", [])
    if not notifications:
        return {"statusCode": 202, "body": {"status": "no notifications"}}

    # Verify client state (simple auth check)
    expected_state = config.get("DEVICE_TOKEN")
    results = []

    for notification in notifications:
        client_state = notification.get("clientState")
        if expected_state and client_state != expected_state:
            continue

        resource_data = notification.get("resourceData", {})
        item_id = resource_data.get("id")
        if not item_id:
            continue

        try:
            result = _process_item(item_id)
            if result:
                results.append(result)
        except Exception as e:
            results.append({"item_id": item_id, "error": str(e)})

    return {"statusCode": 200, "body": {"processed": len(results), "results": results}}


def _process_item(item_id: str) -> dict | None:
    """Process a single OneDrive item (file)."""
    # Get file metadata from OneDrive
    file_meta = get_file_metadata(item_id)
    filename = file_meta.get("name", "")

    # Check if it's an image file
    ext = os.path.splitext(filename)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        return None

    # Check if we already processed this file
    existing = find_by_onedrive_id(item_id)
    if existing:
        return {"item_id": item_id, "status": "already_processed"}

    # Download the file to extract EXIF data
    content = get_file_content(item_id)
    exif_data = extract_exif(content)

    # Reverse geocode GPS coordinates to place name
    location = exif_data.get("location")
    if location and location.get("lat") and location.get("lon"):
        place_name = reverse_geocode(location["lat"], location["lon"])
        if place_name:
            location["name"] = place_name

    # Get thumbnail URL from OneDrive (Graph API generates thumbnails)
    thumbnail_url = get_file_thumbnail_url(item_id) or ""

    # Extract uploader info from OneDrive metadata
    uploaded_by = ""
    created_by = file_meta.get("createdBy", {})
    user_info = created_by.get("user", {})
    uploaded_by = user_info.get("displayName", "")

    # Use OneDrive file description as caption if available
    caption = file_meta.get("description", "")

    # Auto-sort: move photo into uploader's subfolder if it's in the root photos folder
    parent_ref = file_meta.get("parentReference", {})
    parent_path = parent_ref.get("path", "")
    photos_folder = config.get("ONEDRIVE_FOLDER_PATH", "/FamilyFrame/photos")

    # Only move if photo is directly in the root photos folder (not already in a subfolder)
    if uploaded_by and parent_path.endswith(photos_folder.rstrip("/")):
        try:
            target_folder = f"{photos_folder.rstrip('/')}/{uploaded_by}"
            move_file(item_id, target_folder)
        except Exception:
            pass  # If move fails, photo stays in root — still gets processed

    # Create metadata record in Cloudant
    ensure_database()
    doc = create_photo_metadata(
        onedrive_item_id=item_id,
        filename=filename,
        caption=caption,
        date_taken=exif_data.get("date_taken"),
        location=location,
        uploaded_by=uploaded_by,
        upload_channel="onedrive",
        thumbnail_url=thumbnail_url,
    )

    return {"item_id": item_id, "doc_id": doc["_id"], "status": "created"}
