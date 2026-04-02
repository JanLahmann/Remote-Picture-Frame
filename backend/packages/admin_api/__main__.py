"""IBM Cloud Function: admin_api

HTTP API for the admin web interface. Provides CRUD operations on photo
metadata, visibility toggling (moderation), and settings management.

Authenticated via an admin token (separate from the display device token).

Routes (via ?action= query parameter):
  GET  ?action=list&page=1&limit=20       — list all photos (paginated, incl hidden)
  GET  ?action=get&id=<doc_id>            — get single photo metadata
  POST ?action=update&id=<doc_id>         — update photo metadata (caption, description, tags)
  POST ?action=visibility&id=<doc_id>     — toggle visibility (show/hide)
  POST ?action=delete&id=<doc_id>         — delete a photo (metadata + OneDrive file)
  GET  ?action=stats                      — upload statistics
  GET  ?action=settings                   — get current display settings
  POST ?action=settings                   — update display settings
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared import config
from shared.metadata import (
    list_photos, get_photo, update_photo, delete_photo,
    ensure_database, _get_client as get_cloudant_client, _db_name,
)
from shared.onedrive import upload_file, get_file_content, list_folder

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Content-Type": "application/json",
}


def main(params: dict) -> dict:
    """Entry point for the IBM Cloud Function."""
    config.init(params)

    method = params.get("__ow_method", "get")
    if method == "options":
        return {"statusCode": 204, "headers": CORS_HEADERS}

    # Authenticate with admin token
    auth_header = params.get("__ow_headers", {}).get("authorization", "")
    admin_token = config.get("ADMIN_TOKEN", "") or config.get("DEVICE_TOKEN", "")
    if admin_token and auth_header != f"Bearer {admin_token}":
        return {"statusCode": 401, "headers": CORS_HEADERS, "body": {"error": "Unauthorized"}}

    action = params.get("action", "list")

    handlers = {
        "list": _handle_list,
        "get": _handle_get,
        "update": _handle_update,
        "visibility": _handle_visibility,
        "delete": _handle_delete,
        "stats": _handle_stats,
        "settings": _handle_settings_get if method == "get" else _handle_settings_update,
        "faces_setup": _handle_faces_setup,
        "faces_list": _handle_faces_list,
        "faces_add_person": _handle_faces_add_person,
        "faces_delete_person": _handle_faces_delete_person,
        "faces_add_sample": _handle_faces_add_sample,
        "faces_train": _handle_faces_train,
        "faces_status": _handle_faces_status,
    }

    handler = handlers.get(action)
    if not handler:
        return {"statusCode": 400, "headers": CORS_HEADERS, "body": {"error": f"Unknown action: {action}"}}

    try:
        return handler(params)
    except Exception as e:
        return {"statusCode": 500, "headers": CORS_HEADERS, "body": {"error": str(e)}}


def _handle_list(params: dict) -> dict:
    """List all photos (including hidden), paginated."""
    limit = min(int(params.get("limit", "50")), 200)

    photos = list_photos(visible_only=False, limit=limit)

    items = []
    for photo in photos:
        items.append({
            "id": photo["_id"],
            "filename": photo.get("filename", ""),
            "caption": photo.get("caption", ""),
            "description": photo.get("description", ""),
            "date_taken": photo.get("date_taken"),
            "location": photo.get("location"),
            "uploaded_by": photo.get("uploaded_by", ""),
            "uploaded_at": photo.get("uploaded_at", ""),
            "upload_channel": photo.get("upload_channel", ""),
            "visible": photo.get("visible", True),
            "tags": photo.get("tags", []),
            "thumbnail_url": photo.get("thumbnail_url", ""),
        })

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": {"photos": items, "count": len(items)},
    }


def _handle_get(params: dict) -> dict:
    """Get a single photo's full metadata."""
    doc_id = params.get("id")
    if not doc_id:
        return {"statusCode": 400, "headers": CORS_HEADERS, "body": {"error": "Missing 'id'"}}

    photo = get_photo(doc_id)
    return {"statusCode": 200, "headers": CORS_HEADERS, "body": photo}


def _handle_update(params: dict) -> dict:
    """Update photo metadata fields."""
    doc_id = params.get("id")
    if not doc_id:
        return {"statusCode": 400, "headers": CORS_HEADERS, "body": {"error": "Missing 'id'"}}

    body = _parse_body(params)
    allowed_fields = {"caption", "description", "tags", "date_taken", "location", "uploaded_by", "album", "favorite", "people"}
    updates = {k: v for k, v in body.items() if k in allowed_fields}

    if not updates:
        return {"statusCode": 400, "headers": CORS_HEADERS, "body": {"error": "No valid fields to update"}}

    doc = update_photo(doc_id, updates)
    return {"statusCode": 200, "headers": CORS_HEADERS, "body": {"status": "updated", "id": doc_id}}


def _handle_visibility(params: dict) -> dict:
    """Toggle photo visibility (moderation)."""
    doc_id = params.get("id")
    if not doc_id:
        return {"statusCode": 400, "headers": CORS_HEADERS, "body": {"error": "Missing 'id'"}}

    photo = get_photo(doc_id)
    new_visible = not photo.get("visible", True)
    update_photo(doc_id, {"visible": new_visible})

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": {"status": "updated", "id": doc_id, "visible": new_visible},
    }


def _handle_delete(params: dict) -> dict:
    """Delete a photo (metadata only — OneDrive file is kept as backup)."""
    doc_id = params.get("id")
    if not doc_id:
        return {"statusCode": 400, "headers": CORS_HEADERS, "body": {"error": "Missing 'id'"}}

    delete_photo(doc_id)
    return {"statusCode": 200, "headers": CORS_HEADERS, "body": {"status": "deleted", "id": doc_id}}


def _handle_stats(params: dict) -> dict:
    """Return upload statistics."""
    client = get_cloudant_client()
    db = _db_name()

    # Total photos
    total_result = client.post_view(
        db=db, ddoc="photos", view="by_uploaded_at", limit=0, include_docs=False,
    ).get_result()
    total = total_result.get("total_rows", 0)

    # By upload channel
    by_channel = {}
    try:
        find_result = client.post_find(
            db=db,
            selector={"uploaded_at": {"$exists": True}},
            fields=["upload_channel"],
            limit=5000,
        ).get_result()
        for doc in find_result.get("docs", []):
            ch = doc.get("upload_channel", "unknown")
            by_channel[ch] = by_channel.get(ch, 0) + 1
    except Exception:
        pass

    # By uploader
    by_uploader = {}
    try:
        result = client.post_view(
            db=db, ddoc="photos", view="by_uploader",
            group=True, reduce=True,
        ).get_result()
        for row in result.get("rows", []):
            by_uploader[row["key"]] = row["value"]
    except Exception:
        # View might not have reduce — fall back to manual counting
        try:
            find_result = client.post_find(
                db=db,
                selector={"uploaded_at": {"$exists": True}},
                fields=["uploaded_by"],
                limit=5000,
            ).get_result()
            for doc in find_result.get("docs", []):
                name = doc.get("uploaded_by", "Unbekannt")
                by_uploader[name] = by_uploader.get(name, 0) + 1
        except Exception:
            pass

    # Visible vs hidden
    visible_result = client.post_view(
        db=db, ddoc="photos", view="visible_photos", limit=0, include_docs=False,
    ).get_result()
    visible = visible_result.get("total_rows", 0)

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": {
            "total_photos": total,
            "visible_photos": visible,
            "hidden_photos": total - visible,
            "by_channel": by_channel,
            "by_uploader": by_uploader,
        },
    }


def _handle_settings_get(params: dict) -> dict:
    """Get current display settings from OneDrive."""
    from shared.onedrive import list_folder as od_list_folder, get_file_content as od_get_content

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
        "family_members": [],
        "birthdays": [],
        "albums": [],
    }

    try:
        folder_path = config.get("ONEDRIVE_FOLDER_PATH", "/FamilyFrame/photos").replace("/photos", "/config")
        folder = od_list_folder(folder_path)
        for item in folder.get("items", []):
            if item.get("name") == "settings.json":
                content = od_get_content(item["id"])
                user_settings = json.loads(content)
                defaults.update(user_settings)
                break
    except Exception:
        pass

    return {"statusCode": 200, "headers": CORS_HEADERS, "body": defaults}


def _handle_settings_update(params: dict) -> dict:
    """Update display settings in OneDrive."""
    body = _parse_body(params)
    if not body:
        return {"statusCode": 400, "headers": CORS_HEADERS, "body": {"error": "Empty body"}}

    settings_json = json.dumps(body, indent=2, ensure_ascii=False).encode("utf-8")
    config_path = config.get("ONEDRIVE_FOLDER_PATH", "/FamilyFrame/photos").replace("/photos", "/config")

    upload_file(config_path, "settings.json", settings_json, "application/json")

    return {"statusCode": 200, "headers": CORS_HEADERS, "body": {"status": "saved"}}


# --- Face Recognition Management ---

def _handle_faces_setup(params: dict) -> dict:
    """Create the person group (one-time setup)."""
    from shared.face_recognition import create_person_group
    result = create_person_group()
    return {"statusCode": 200, "headers": CORS_HEADERS, "body": result}


def _handle_faces_list(params: dict) -> dict:
    """List all persons in the face recognition group."""
    from shared.face_recognition import list_persons
    persons = list_persons()
    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": {"persons": persons},
    }


def _handle_faces_add_person(params: dict) -> dict:
    """Add a new person to the face recognition group."""
    body = _parse_body(params)
    name = body.get("name", "").strip()
    if not name:
        return {"statusCode": 400, "headers": CORS_HEADERS, "body": {"error": "Missing 'name'"}}

    from shared.face_recognition import add_person
    person_id = add_person(name)
    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": {"personId": person_id, "name": name},
    }


def _handle_faces_delete_person(params: dict) -> dict:
    """Remove a person from the face recognition group."""
    person_id = params.get("person_id")
    if not person_id:
        return {"statusCode": 400, "headers": CORS_HEADERS, "body": {"error": "Missing 'person_id'"}}

    from shared.face_recognition import delete_person
    delete_person(person_id)
    return {"statusCode": 200, "headers": CORS_HEADERS, "body": {"status": "deleted"}}


def _handle_faces_add_sample(params: dict) -> dict:
    """Add a sample face image to a person for training."""
    import base64
    person_id = params.get("person_id")
    if not person_id:
        return {"statusCode": 400, "headers": CORS_HEADERS, "body": {"error": "Missing 'person_id'"}}

    body = _parse_body(params)
    image_b64 = body.get("image", "")
    if not image_b64:
        return {"statusCode": 400, "headers": CORS_HEADERS, "body": {"error": "Missing 'image' (base64)"}}

    image_bytes = base64.b64decode(image_b64)

    from shared.face_recognition import add_face_to_person
    face_id = add_face_to_person(person_id, image_bytes)
    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": {"persistedFaceId": face_id},
    }


def _handle_faces_train(params: dict) -> dict:
    """Start training the face recognition model."""
    from shared.face_recognition import train_person_group
    result = train_person_group()
    return {"statusCode": 200, "headers": CORS_HEADERS, "body": result}


def _handle_faces_status(params: dict) -> dict:
    """Check face recognition training status."""
    from shared.face_recognition import get_training_status
    status = get_training_status()
    return {"statusCode": 200, "headers": CORS_HEADERS, "body": status}


def _parse_body(params: dict) -> dict:
    """Parse the request body from IBM Cloud Function params."""
    import base64
    body = params.get("__ow_body", "")
    if isinstance(body, dict):
        return body
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            try:
                return json.loads(base64.b64decode(body))
            except Exception:
                return {}
    return {}
