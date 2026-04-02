"""Microsoft Graph API helpers for OneDrive access.

Uses MSAL (Microsoft Authentication Library) for app-only authentication
and the Graph API for file operations and webhook subscriptions.
"""

import io
import time
from typing import Optional

import msal
import requests

from . import config

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

_token_cache: dict = {"access_token": None, "expires_at": 0}


def _get_access_token() -> str:
    """Get a valid access token, refreshing if needed."""
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["access_token"]

    app = msal.ConfidentialClientApplication(
        client_id=config.get("GRAPH_CLIENT_ID"),
        client_credential=config.get("GRAPH_CLIENT_SECRET"),
        authority=f"https://login.microsoftonline.com/{config.get('GRAPH_TENANT_ID')}",
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

    if "access_token" not in result:
        raise RuntimeError(f"Failed to acquire Graph token: {result.get('error_description')}")

    _token_cache["access_token"] = result["access_token"]
    _token_cache["expires_at"] = now + result.get("expires_in", 3600)
    return result["access_token"]


def _headers() -> dict:
    return {"Authorization": f"Bearer {_get_access_token()}"}


def _user_drive_url() -> str:
    """Base URL for the OneDrive user's drive."""
    user_id = config.get("ONEDRIVE_USER_ID")
    return f"{GRAPH_BASE}/users/{user_id}/drive"


def get_file_metadata(item_id: str) -> dict:
    """Get file metadata (name, size, timestamps, etc.) from OneDrive."""
    url = f"{_user_drive_url()}/items/{item_id}"
    resp = requests.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_file_content(item_id: str) -> bytes:
    """Download file content from OneDrive."""
    url = f"{_user_drive_url()}/items/{item_id}/content"
    resp = requests.get(url, headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.content


def get_file_thumbnail_url(item_id: str, size: str = "c800x800") -> Optional[str]:
    """Get a thumbnail URL for a file. Returns None if not available."""
    url = f"{_user_drive_url()}/items/{item_id}/thumbnails/0/{size}"
    resp = requests.get(url, headers=_headers(), timeout=15)
    if resp.status_code == 200:
        return resp.json().get("url")
    return None


def upload_file(folder_path: str, filename: str, content: bytes, content_type: str = "image/jpeg") -> dict:
    """Upload a file to OneDrive."""
    encoded_path = folder_path.replace(" ", "%20")
    url = f"{_user_drive_url()}/root:{encoded_path}/{filename}:/content"
    resp = requests.put(
        url,
        headers={**_headers(), "Content-Type": content_type},
        data=content,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def list_folder(folder_path: str, delta_link: Optional[str] = None) -> dict:
    """List files in a OneDrive folder, with optional delta sync.

    Returns dict with 'items' (list of file metadata) and 'delta_link' for next sync.
    """
    if delta_link:
        url = delta_link
    else:
        encoded_path = folder_path.replace(" ", "%20")
        url = f"{_user_drive_url()}/root:{encoded_path}:/delta"

    items = []
    while url:
        resp = requests.get(url, headers=_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return {
        "items": items,
        "delta_link": data.get("@odata.deltaLink"),
    }


def create_subscription(
    resource: str,
    notification_url: str,
    expiration_minutes: int = 4230,  # ~2.9 days, max for OneDrive
) -> dict:
    """Create a Graph API webhook subscription for change notifications.

    Args:
        resource: The resource to watch, e.g. "/users/{id}/drive/root"
        notification_url: HTTPS URL to receive notifications
        expiration_minutes: Subscription lifetime in minutes
    """
    from datetime import datetime, timedelta, timezone

    expiration = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)

    url = f"{GRAPH_BASE}/subscriptions"
    payload = {
        "changeType": "created,updated",
        "notificationUrl": notification_url,
        "resource": resource,
        "expirationDateTime": expiration.isoformat(),
        "clientState": config.get("DEVICE_TOKEN"),
    }
    resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def renew_subscription(subscription_id: str, expiration_minutes: int = 4230) -> dict:
    """Renew an existing webhook subscription."""
    from datetime import datetime, timedelta, timezone

    expiration = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)

    url = f"{GRAPH_BASE}/subscriptions/{subscription_id}"
    payload = {"expirationDateTime": expiration.isoformat()}
    resp = requests.patch(url, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_download_url(item_id: str) -> Optional[str]:
    """Get a short-lived download URL for a file (for direct display)."""
    metadata = get_file_metadata(item_id)
    return metadata.get("@microsoft.graph.downloadUrl")


def move_file(item_id: str, target_folder_path: str) -> dict:
    """Move a file to a different folder in OneDrive.

    Creates the target folder if it doesn't exist.
    """
    # Ensure target folder exists (create if needed)
    encoded_path = target_folder_path.replace(" ", "%20")
    folder_url = f"{_user_drive_url()}/root:{encoded_path}"
    resp = requests.get(folder_url, headers=_headers(), timeout=15)

    if resp.status_code == 404:
        # Create the folder
        parent_path = "/".join(target_folder_path.rstrip("/").split("/")[:-1])
        folder_name = target_folder_path.rstrip("/").split("/")[-1]
        encoded_parent = parent_path.replace(" ", "%20")
        create_url = f"{_user_drive_url()}/root:{encoded_parent}:/children"
        create_payload = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        }
        create_resp = requests.post(
            create_url, headers=_headers(), json=create_payload, timeout=15,
        )
        # 409 = folder already exists (race condition), that's fine
        if create_resp.status_code not in (200, 201, 409):
            create_resp.raise_for_status()
        # Re-fetch folder to get its ID
        resp = requests.get(folder_url, headers=_headers(), timeout=15)
        resp.raise_for_status()

    folder_data = resp.json()
    folder_id = folder_data["id"]

    # Move the file
    move_url = f"{_user_drive_url()}/items/{item_id}"
    move_payload = {"parentReference": {"id": folder_id}}
    move_resp = requests.patch(
        move_url, headers=_headers(), json=move_payload, timeout=30,
    )
    move_resp.raise_for_status()
    return move_resp.json()
