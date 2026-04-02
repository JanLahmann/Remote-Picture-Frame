"""IBM Cloud Function: whatsapp_webhook

Receives incoming WhatsApp messages via Meta WhatsApp Cloud API webhooks.
When a family member sends a photo, it downloads the image, uploads it to
OneDrive, and creates a metadata record in Cloudant.

Handles two request types:
1. GET: Webhook verification (Meta sends a challenge token)
2. POST: Incoming message notification
"""

import sys
import os
import hashlib
import hmac
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import requests as http_requests

from shared import config
from shared.onedrive import upload_file, get_file_thumbnail_url
from shared.metadata import create_photo_metadata, ensure_database
from shared.exif_utils import extract_exif
from shared.geocoding import reverse_geocode


CORS_HEADERS = {
    "Content-Type": "application/json",
}


def main(params: dict) -> dict:
    """Entry point for the IBM Cloud Function."""
    config.init(params)

    method = params.get("__ow_method", "get")

    if method == "get":
        return _handle_verification(params)
    elif method == "post":
        return _handle_notification(params)
    else:
        return {"statusCode": 405, "headers": CORS_HEADERS, "body": {"error": "Method not allowed"}}


def _handle_verification(params: dict) -> dict:
    """Handle Meta webhook verification (GET request).

    Meta sends:
      ?hub.mode=subscribe
      &hub.verify_token=<our_verify_token>
      &hub.challenge=<challenge_string>

    We must respond with the challenge string if the verify token matches.
    """
    mode = params.get("hub.mode", "")
    token = params.get("hub.verify_token", "")
    challenge = params.get("hub.challenge", "")

    verify_token = config.get("WHATSAPP_VERIFY_TOKEN")

    if mode == "subscribe" and token == verify_token:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/plain"},
            "body": challenge,
        }

    return {
        "statusCode": 403,
        "headers": CORS_HEADERS,
        "body": {"error": "Verification failed"},
    }


def _handle_notification(params: dict) -> dict:
    """Handle incoming WhatsApp message notifications (POST request)."""
    # Verify webhook signature
    signature = params.get("__ow_headers", {}).get("x-hub-signature-256", "")
    raw_body = params.get("__ow_body", "")
    if not _verify_signature(raw_body, signature):
        return {"statusCode": 401, "headers": CORS_HEADERS, "body": {"error": "Invalid signature"}}

    # Parse the notification body
    body = raw_body if isinstance(raw_body, dict) else {}
    if isinstance(raw_body, str):
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            import base64
            try:
                body = json.loads(base64.b64decode(raw_body))
            except Exception:
                return {"statusCode": 400, "headers": CORS_HEADERS, "body": {"error": "Invalid body"}}

    # Process each entry
    results = []
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])

            for message in messages:
                result = _process_message(message, contacts)
                if result:
                    results.append(result)

    return {"statusCode": 200, "headers": CORS_HEADERS, "body": {"processed": len(results)}}


def _process_message(message: dict, contacts: list) -> dict | None:
    """Process a single incoming WhatsApp message."""
    msg_type = message.get("type", "")

    # We only care about image messages
    if msg_type != "image":
        return None

    image_info = message.get("image", {})
    media_id = image_info.get("id")
    if not media_id:
        return None

    # Get sender info
    sender_wa_id = message.get("from", "")
    sender_name = ""
    for contact in contacts:
        if contact.get("wa_id") == sender_wa_id:
            profile = contact.get("profile", {})
            sender_name = profile.get("name", "")
            break

    # Caption from the image message
    caption = image_info.get("caption", "")

    # Download the image from Meta's servers
    image_bytes = _download_media(media_id)
    if not image_bytes:
        return {"error": "Failed to download media", "media_id": media_id}

    # Extract EXIF data
    exif_data = extract_exif(image_bytes)

    # Reverse geocode if GPS data present
    location = exif_data.get("location")
    if location and location.get("lat") and location.get("lon"):
        place_name = reverse_geocode(location["lat"], location["lon"])
        if place_name:
            location["name"] = place_name

    # Generate filename
    from datetime import datetime, timezone
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    name_hash = hashlib.md5(image_bytes[:1024]).hexdigest()[:6]
    filename = f"wa_{timestamp}_{name_hash}.jpg"

    # Upload to OneDrive (into uploader's subfolder)
    base_folder = config.get("ONEDRIVE_FOLDER_PATH", "/FamilyFrame/photos")
    uploader = sender_name or sender_wa_id
    folder_path = f"{base_folder.rstrip('/')}/{uploader}" if uploader else base_folder
    od_result = upload_file(folder_path, filename, image_bytes, "image/jpeg")
    item_id = od_result.get("id", "")

    # Get thumbnail URL
    thumbnail_url = ""
    if item_id:
        thumbnail_url = get_file_thumbnail_url(item_id) or ""

    # Create metadata record
    ensure_database()
    doc = create_photo_metadata(
        onedrive_item_id=item_id,
        filename=filename,
        caption=caption,
        date_taken=exif_data.get("date_taken"),
        location=location,
        uploaded_by=sender_name or sender_wa_id,
        upload_channel="whatsapp",
        thumbnail_url=thumbnail_url,
    )

    return {"doc_id": doc["_id"], "filename": filename, "from": sender_name}


def _download_media(media_id: str) -> bytes | None:
    """Download media from Meta's WhatsApp Cloud API.

    Two-step process:
    1. GET the media URL from the media ID
    2. GET the actual media content from the URL
    """
    access_token = config.get("WHATSAPP_ACCESS_TOKEN")
    api_version = config.get("WHATSAPP_API_VERSION", "v21.0")

    # Step 1: Get the media URL
    url = f"https://graph.facebook.com/{api_version}/{media_id}"
    resp = http_requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    if resp.status_code != 200:
        return None

    media_url = resp.json().get("url")
    if not media_url:
        return None

    # Step 2: Download the actual image
    resp = http_requests.get(
        media_url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=60,
    )
    if resp.status_code != 200:
        return None

    return resp.content


def _verify_signature(raw_body: str, signature_header: str) -> bool:
    """Verify the X-Hub-Signature-256 header from Meta.

    Returns True if the signature is valid or if no app secret is configured
    (for development).
    """
    app_secret = config.get("WHATSAPP_APP_SECRET")
    if not app_secret:
        return True  # Skip verification in development

    if not signature_header:
        return False

    # signature_header format: "sha256=<hex_digest>"
    if not signature_header.startswith("sha256="):
        return False

    expected_sig = signature_header[7:]

    body_bytes = raw_body.encode("utf-8") if isinstance(raw_body, str) else raw_body
    computed_sig = hmac.new(
        app_secret.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed_sig, expected_sig)
