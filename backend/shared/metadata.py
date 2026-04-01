"""IBM Cloudant helpers for photo metadata storage.

Uses the ibmcloudant SDK for CRUD operations on photo metadata documents.
"""

from datetime import datetime, timezone
from typing import Optional
import uuid

from ibmcloudant.cloudant_v1 import CloudantV1, Document
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from . import config

_client: Optional[CloudantV1] = None


def _get_client() -> CloudantV1:
    """Get or create a Cloudant client instance."""
    global _client
    if _client is None:
        authenticator = IAMAuthenticator(config.get("CLOUDANT_APIKEY"))
        _client = CloudantV1(authenticator=authenticator)
        _client.set_service_url(config.get("CLOUDANT_URL"))
    return _client


def _db_name() -> str:
    return config.get("CLOUDANT_DB_NAME", "familyframe")


def ensure_database():
    """Create the database and design documents if they don't exist."""
    client = _get_client()
    db = _db_name()

    # Create database
    try:
        client.put_database(db=db).get_result()
    except Exception:
        pass  # Already exists

    # Create design document with useful views
    views = {
        "by_uploaded_at": {
            "map": "function(doc) { if (doc.uploaded_at) { emit(doc.uploaded_at, null); } }",
        },
        "by_date_taken": {
            "map": "function(doc) { if (doc.date_taken) { emit(doc.date_taken, null); } }",
        },
        "by_uploader": {
            "map": "function(doc) { if (doc.uploaded_by) { emit(doc.uploaded_by, null); } }",
        },
        "visible_photos": {
            "map": "function(doc) { if (doc.visible !== false) { emit(doc.uploaded_at, null); } }",
        },
    }

    ddoc = Document(
        id="_design/photos",
        views={k: {"map": v["map"]} for k, v in views.items()},
    )

    try:
        # Try to get existing design doc to preserve _rev
        existing = client.get_document(db=db, doc_id="_design/photos").get_result()
        ddoc.rev = existing.get("_rev")
    except Exception:
        pass

    try:
        client.put_document(db=db, doc_id="_design/photos", document=ddoc.__dict__).get_result()
    except Exception:
        pass


def create_photo_metadata(
    onedrive_item_id: str,
    filename: str,
    caption: str = "",
    description: str = "",
    date_taken: Optional[str] = None,
    location: Optional[dict] = None,
    uploaded_by: str = "",
    upload_channel: str = "onedrive",
    thumbnail_url: str = "",
) -> dict:
    """Create a new photo metadata document in Cloudant."""
    client = _get_client()
    doc_id = str(uuid.uuid4())

    doc = {
        "_id": doc_id,
        "onedrive_item_id": onedrive_item_id,
        "filename": filename,
        "caption": caption,
        "description": description,
        "date_taken": date_taken,
        "location": location,
        "uploaded_by": uploaded_by,
        "upload_channel": upload_channel,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "visible": True,
        "tags": [],
        "thumbnail_url": thumbnail_url,
    }

    result = client.post_document(db=_db_name(), document=doc).get_result()
    doc["_id"] = result["id"]
    doc["_rev"] = result["rev"]
    return doc


def get_photo(doc_id: str) -> dict:
    """Get a single photo metadata document."""
    client = _get_client()
    return client.get_document(db=_db_name(), doc_id=doc_id).get_result()


def update_photo(doc_id: str, updates: dict) -> dict:
    """Update fields on a photo metadata document."""
    client = _get_client()
    doc = client.get_document(db=_db_name(), doc_id=doc_id).get_result()
    doc.update(updates)
    result = client.post_document(db=_db_name(), document=doc).get_result()
    doc["_rev"] = result["rev"]
    return doc


def delete_photo(doc_id: str):
    """Delete a photo metadata document."""
    client = _get_client()
    doc = client.get_document(db=_db_name(), doc_id=doc_id).get_result()
    client.delete_document(db=_db_name(), doc_id=doc_id, rev=doc["_rev"]).get_result()


def list_photos(
    since: Optional[str] = None,
    visible_only: bool = True,
    limit: int = 200,
) -> list[dict]:
    """List photo metadata, optionally filtered by upload date.

    Args:
        since: ISO timestamp — only return photos uploaded after this time
        visible_only: If True, only return visible photos
        limit: Maximum number of photos to return
    """
    client = _get_client()
    db = _db_name()
    view = "visible_photos" if visible_only else "by_uploaded_at"

    params = {
        "db": db,
        "ddoc": "photos",
        "view": view,
        "include_docs": True,
        "limit": limit,
        "descending": True,
    }

    if since:
        params["end_key"] = f'"{since}"'

    result = client.post_view(**params).get_result()
    return [row["doc"] for row in result.get("rows", [])]


def find_by_onedrive_id(onedrive_item_id: str) -> Optional[dict]:
    """Find a photo metadata document by its OneDrive item ID."""
    client = _get_client()
    result = client.post_find(
        db=_db_name(),
        selector={"onedrive_item_id": {"$eq": onedrive_item_id}},
        limit=1,
    ).get_result()
    docs = result.get("docs", [])
    return docs[0] if docs else None
