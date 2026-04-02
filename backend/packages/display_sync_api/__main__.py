"""IBM Cloud Function: display_sync_api

HTTP API for the display PWA to sync photos and metadata.
Supports delta sync (only return photos since a given timestamp).
Authenticated via a device token.

Endpoints (via query params):
  ?action=sync&since=<ISO_TIMESTAMP>  — list photos (delta sync)
  ?action=photo&id=<DOC_ID>           — get single photo metadata + download URL
  ?action=settings                     — get display settings
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared import config
from shared.onedrive import get_download_url, get_file_thumbnail_url
from shared.metadata import list_photos, get_photo

# CORS headers for PWA access
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",  # Restrict to your domain in production
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Content-Type": "application/json",
}


def main(params: dict) -> dict:
    """Entry point for the IBM Cloud Function."""
    config.init(params)

    # Handle CORS preflight
    http_method = params.get("__ow_method", "get")
    if http_method == "options":
        return {"statusCode": 204, "headers": CORS_HEADERS}

    # Authenticate
    auth_header = params.get("__ow_headers", {}).get("authorization", "")
    expected_token = config.get("DEVICE_TOKEN")
    if expected_token and auth_header != f"Bearer {expected_token}":
        return {
            "statusCode": 401,
            "headers": CORS_HEADERS,
            "body": {"error": "Unauthorized"},
        }

    action = params.get("action", "sync")

    if action == "sync":
        return _handle_sync(params)
    elif action == "photo":
        return _handle_photo(params)
    elif action == "uploaders":
        return _handle_uploaders(params)
    elif action == "settings":
        return _handle_settings(params)
    else:
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": {"error": f"Unknown action: {action}"},
        }


def _handle_sync(params: dict) -> dict:
    """Return list of photos, optionally filtered by timestamp or uploader."""
    since = params.get("since")
    limit = min(int(params.get("limit", "200")), 500)
    uploader = params.get("uploader", "")

    photos = list_photos(since=since, visible_only=True, limit=limit)

    # Filter by uploader if requested
    if uploader:
        photos = [p for p in photos if p.get("uploaded_by", "") == uploader]

    # Enrich with download URLs
    items = []
    for photo in photos:
        item = {
            "id": photo["_id"],
            "filename": photo.get("filename", ""),
            "caption": photo.get("caption", ""),
            "description": photo.get("description", ""),
            "date_taken": photo.get("date_taken"),
            "location": photo.get("location"),
            "uploaded_by": photo.get("uploaded_by", ""),
            "uploaded_at": photo.get("uploaded_at", ""),
            "thumbnail_url": photo.get("thumbnail_url", ""),
            "tags": photo.get("tags", []),
        }

        # Get fresh download URL from OneDrive
        onedrive_id = photo.get("onedrive_item_id")
        if onedrive_id:
            try:
                item["download_url"] = get_download_url(onedrive_id)
            except Exception:
                item["download_url"] = None

        items.append(item)

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": {
            "photos": items,
            "count": len(items),
            "synced_at": _now_iso(),
        },
    }


def _handle_photo(params: dict) -> dict:
    """Return a single photo's metadata and fresh download URL."""
    doc_id = params.get("id")
    if not doc_id:
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": {"error": "Missing 'id' parameter"},
        }

    try:
        photo = get_photo(doc_id)
    except Exception:
        return {
            "statusCode": 404,
            "headers": CORS_HEADERS,
            "body": {"error": "Photo not found"},
        }

    # Get fresh download URL
    onedrive_id = photo.get("onedrive_item_id")
    download_url = None
    if onedrive_id:
        try:
            download_url = get_download_url(onedrive_id)
        except Exception:
            pass

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": {
            "id": photo["_id"],
            "filename": photo.get("filename", ""),
            "caption": photo.get("caption", ""),
            "description": photo.get("description", ""),
            "date_taken": photo.get("date_taken"),
            "location": photo.get("location"),
            "uploaded_by": photo.get("uploaded_by", ""),
            "uploaded_at": photo.get("uploaded_at", ""),
            "download_url": download_url,
            "thumbnail_url": photo.get("thumbnail_url", ""),
            "tags": photo.get("tags", []),
        },
    }


def _handle_uploaders(params: dict) -> dict:
    """Return a list of unique uploader names."""
    photos = list_photos(visible_only=True, limit=9999)
    uploaders = sorted(set(p.get("uploaded_by", "") for p in photos if p.get("uploaded_by")))

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": {"uploaders": uploaders},
    }


def _handle_settings(params: dict) -> dict:
    """Return display settings from OneDrive config file.

    Falls back to defaults if the settings file doesn't exist.
    """
    from shared.onedrive import list_folder

    defaults = {
        "slideshow_interval": 30,
        "transition": "fade",
        "transition_duration": 1.5,
        "order": "random",
        "show_overlay": True,
        "overlay_duration": 5,
        "night_mode": {
            "enabled": True,
            "dim_start": "22:00",
            "dim_end": "07:00",
            "brightness": 0.1,
        },
        "sync_interval": 5,
    }

    # Try to load settings from OneDrive
    try:
        import json
        from shared.onedrive import get_file_content

        folder_path = config.get("ONEDRIVE_FOLDER_PATH", "/FamilyFrame/photos")
        config_path = folder_path.replace("/photos", "/config")

        folder = list_folder(config_path)
        for item in folder.get("items", []):
            if item.get("name") == "settings.json":
                content = get_file_content(item["id"])
                user_settings = json.loads(content)
                defaults.update(user_settings)
                break
    except Exception:
        pass  # Use defaults if settings file not found

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": defaults,
    }


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
