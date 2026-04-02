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
from shared.metadata import create_photo_metadata, get_photo, update_photo, ensure_database
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
    """Process a single incoming WhatsApp message.

    Handles two message types:
    - image: Download, process, upload to OneDrive, send confirmation
    - location: Attach location to the sender's most recent photo
    """
    msg_type = message.get("type", "")

    # Get sender info
    sender_wa_id = message.get("from", "")
    sender_name = ""
    for contact in contacts:
        if contact.get("wa_id") == sender_wa_id:
            profile = contact.get("profile", {})
            sender_name = profile.get("name", "")
            break

    if msg_type == "image":
        return _process_image(message, sender_wa_id, sender_name)
    elif msg_type == "location":
        return _process_location(message, sender_wa_id, sender_name)
    else:
        return None


def _process_image(message: dict, sender_wa_id: str, sender_name: str) -> dict | None:
    """Process an incoming image message."""
    image_info = message.get("image", {})
    media_id = image_info.get("id")
    if not media_id:
        return None

    caption = image_info.get("caption", "")

    # Download the image from Meta's servers
    image_bytes = _download_media(media_id)
    if not image_bytes:
        _send_reply(sender_wa_id, "Fehler: Foto konnte nicht heruntergeladen werden. Bitte nochmal versuchen.")
        return {"error": "Failed to download media", "media_id": media_id}

    # Try to extract EXIF data (WhatsApp strips most/all EXIF data,
    # so date_taken, GPS, and camera info will usually be empty)
    exif_data = extract_exif(image_bytes)

    # WhatsApp strips EXIF date — use current time as date_taken
    from datetime import datetime, timezone
    date_taken = exif_data.get("date_taken") or datetime.now(timezone.utc).isoformat()

    # Reverse geocode if GPS data present (unlikely from WhatsApp)
    location = exif_data.get("location")
    if location and location.get("lat") and location.get("lon"):
        place_name = reverse_geocode(location["lat"], location["lon"])
        if place_name:
            location["name"] = place_name

    # Recognize people in the photo
    from shared.face_recognition import recognize_people
    people = recognize_people(image_bytes)

    # Generate filename
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
        date_taken=date_taken,
        location=location,
        uploaded_by=uploader,
        upload_channel="whatsapp",
        thumbnail_url=thumbnail_url,
        people=people,
    )

    # Remember this photo as the sender's latest (for location follow-up)
    _save_last_photo_id(sender_wa_id, doc["_id"])

    # Send confirmation reply
    _send_confirmation(sender_wa_id, sender_name, caption, people, location)

    return {"doc_id": doc["_id"], "filename": filename, "from": sender_name}


def _process_location(message: dict, sender_wa_id: str, sender_name: str) -> dict | None:
    """Process a location message — attach it to the sender's most recent photo."""
    loc_info = message.get("location", {})
    lat = loc_info.get("latitude")
    lon = loc_info.get("longitude")
    loc_name = loc_info.get("name", "") or loc_info.get("address", "")

    if lat is None or lon is None:
        return None

    # Reverse geocode for a friendly name
    if not loc_name:
        place = reverse_geocode(lat, lon)
        if place:
            loc_name = place

    location = {"lat": lat, "lon": lon}
    if loc_name:
        location["name"] = loc_name

    # Find the sender's most recent photo and update it
    last_photo_id = _get_last_photo_id(sender_wa_id)
    if not last_photo_id:
        _send_reply(sender_wa_id, "Schicke erst ein Foto, dann den Standort dazu.")
        return None

    try:
        update_photo(last_photo_id, {"location": location})
        # Clear the stored reference so the same location isn't applied twice
        _clear_last_photo_id(sender_wa_id)

        reply = f"Standort hinzugefuegt: {loc_name or f'{lat:.4f}, {lon:.4f}'}"
        _send_reply(sender_wa_id, reply)
        return {"photo_id": last_photo_id, "location": location}
    except Exception as e:
        _send_reply(sender_wa_id, "Fehler beim Speichern des Standorts.")
        return {"error": str(e)}


def _save_last_photo_id(wa_id: str, photo_doc_id: str) -> None:
    """Store the last uploaded photo ID for a WhatsApp user in Cloudant."""
    from shared.metadata import _get_client as get_client, _db_name
    client = get_client()
    db = _db_name()
    doc_id = f"_local/wa_last_photo_{wa_id}"

    doc = {"_id": doc_id, "photo_id": photo_doc_id}
    try:
        existing = client.get_document(db=db, doc_id=doc_id).get_result()
        doc["_rev"] = existing["_rev"]
    except Exception:
        pass

    try:
        client.put_document(db=db, doc_id=doc_id, document=doc).get_result()
    except Exception:
        pass


def _get_last_photo_id(wa_id: str) -> str | None:
    """Retrieve the last uploaded photo ID for a WhatsApp user."""
    from shared.metadata import _get_client as get_client, _db_name
    try:
        client = get_client()
        doc = client.get_document(db=_db_name(), doc_id=f"_local/wa_last_photo_{wa_id}").get_result()
        return doc.get("photo_id")
    except Exception:
        return None


def _clear_last_photo_id(wa_id: str) -> None:
    """Remove the stored last photo reference after location is attached."""
    from shared.metadata import _get_client as get_client, _db_name
    try:
        client = get_client()
        db = _db_name()
        doc_id = f"_local/wa_last_photo_{wa_id}"
        doc = client.get_document(db=db, doc_id=doc_id).get_result()
        client.delete_document(db=db, doc_id=doc_id, rev=doc["_rev"]).get_result()
    except Exception:
        pass


def _send_confirmation(
    recipient_wa_id: str,
    sender_name: str,
    caption: str,
    people: list[str],
    location: dict | None,
) -> None:
    """Send a friendly confirmation reply after a photo was processed."""
    lines = ["Danke, dein Foto ist auf Omas Bilderrahmen!"]

    if caption:
        lines.append(f'Bildunterschrift: "{caption}"')

    if people:
        lines.append(f"Erkannt: {', '.join(people)}")

    if location and location.get("name"):
        lines.append(f"Ort: {location['name']}")
    elif location and location.get("lat"):
        lines.append(f"Ort: {location['lat']:.2f}, {location['lon']:.2f}")
    else:
        # WhatsApp strips GPS from photos — ask user to share location separately
        lines.append("")
        lines.append("Moechtest du den Ort hinzufuegen? "
                      "Schicke einfach deinen Standort "
                      "(Bueroklammer > Standort > Standort senden).")

    _send_reply(recipient_wa_id, "\n".join(lines))


def _send_reply(recipient_wa_id: str, text: str) -> None:
    """Send a text message reply via WhatsApp Cloud API."""
    access_token = config.get("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = config.get("WHATSAPP_PHONE_NUMBER_ID")
    api_version = config.get("WHATSAPP_API_VERSION", "v21.0")

    if not access_token or not phone_number_id:
        return

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    try:
        http_requests.post(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to": recipient_wa_id,
                "type": "text",
                "text": {"body": text},
            },
            timeout=10,
        )
    except Exception:
        pass  # Best effort — don't fail the upload if reply fails


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
