"""Azure Face API integration for identifying people in photos.

Uses Azure AI Face service (free tier: 30K transactions/month) to:
1. Detect faces in uploaded photos
2. Identify detected faces against a trained Person Group
3. Return a list of recognized family member names

Setup:
- Create an Azure Face resource (free F0 tier)
- Create a Person Group and add persons with sample face images via admin API
- The Person Group must be trained before identification works

Docs: https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/how-to/identity-detect-faces
"""

import requests
from typing import Optional

from . import config

# Minimum confidence threshold for a positive identification
CONFIDENCE_THRESHOLD = 0.6

PERSON_GROUP_ID = "familyframe-family"


def _endpoint() -> str:
    return config.get("AZURE_FACE_ENDPOINT", "").rstrip("/")


def _headers() -> dict:
    return {
        "Ocp-Apim-Subscription-Key": config.get("AZURE_FACE_KEY", ""),
        "Content-Type": "application/json",
    }


def _octet_headers() -> dict:
    return {
        "Ocp-Apim-Subscription-Key": config.get("AZURE_FACE_KEY", ""),
        "Content-Type": "application/octet-stream",
    }


# --- Person Group Management (used by admin API) ---


def create_person_group(name: str = "FamilyFrame Familie") -> dict:
    """Create the person group (one-time setup)."""
    url = f"{_endpoint()}/face/v1.0/persongroups/{PERSON_GROUP_ID}"
    resp = requests.put(
        url,
        headers=_headers(),
        json={"name": name, "recognitionModel": "recognition_04"},
        timeout=15,
    )
    if resp.status_code == 409:
        return {"status": "already_exists"}
    resp.raise_for_status()
    return {"status": "created"}


def add_person(name: str) -> str:
    """Add a person to the group. Returns the person ID."""
    url = f"{_endpoint()}/face/v1.0/persongroups/{PERSON_GROUP_ID}/persons"
    resp = requests.post(url, headers=_headers(), json={"name": name}, timeout=15)
    resp.raise_for_status()
    return resp.json()["personId"]


def list_persons() -> list[dict]:
    """List all persons in the group. Returns [{personId, name, persistedFaceIds}]."""
    url = f"{_endpoint()}/face/v1.0/persongroups/{PERSON_GROUP_ID}/persons"
    resp = requests.get(url, headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def delete_person(person_id: str) -> None:
    """Remove a person from the group."""
    url = f"{_endpoint()}/face/v1.0/persongroups/{PERSON_GROUP_ID}/persons/{person_id}"
    resp = requests.delete(url, headers=_headers(), timeout=15)
    resp.raise_for_status()


def add_face_to_person(person_id: str, image_bytes: bytes) -> str:
    """Add a sample face image to a person. Returns the persisted face ID.

    Each person needs 3-6 varied sample images for good accuracy.
    """
    url = (
        f"{_endpoint()}/face/v1.0/persongroups/{PERSON_GROUP_ID}"
        f"/persons/{person_id}/persistedFaces?detectionModel=detection_03"
    )
    resp = requests.post(url, headers=_octet_headers(), data=image_bytes, timeout=30)
    resp.raise_for_status()
    return resp.json()["persistedFaceId"]


def train_person_group() -> dict:
    """Start training the person group. Must be called after adding/removing faces.

    Training is asynchronous — call get_training_status() to check progress.
    """
    url = f"{_endpoint()}/face/v1.0/persongroups/{PERSON_GROUP_ID}/train"
    resp = requests.post(url, headers=_headers(), timeout=15)
    resp.raise_for_status()
    return {"status": "training_started"}


def get_training_status() -> dict:
    """Check the training status of the person group."""
    url = f"{_endpoint()}/face/v1.0/persongroups/{PERSON_GROUP_ID}"
    resp = requests.get(url, headers=_headers(), params={"returnRecognitionModel": True}, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    train_url = f"{_endpoint()}/face/v1.0/persongroups/{PERSON_GROUP_ID}/training"
    train_resp = requests.get(train_url, headers=_headers(), timeout=15)
    if train_resp.status_code == 200:
        training = train_resp.json()
        data["trainingStatus"] = training.get("status", "unknown")
        data["trainingMessage"] = training.get("message", "")
    else:
        data["trainingStatus"] = "not_started"

    return data


# --- Face Detection & Identification (used during photo processing) ---


def detect_faces(image_bytes: bytes) -> list[dict]:
    """Detect faces in an image. Returns list of face dicts with faceId."""
    url = (
        f"{_endpoint()}/face/v1.0/detect"
        f"?returnFaceId=true&recognitionModel=recognition_04&detectionModel=detection_03"
    )
    resp = requests.post(url, headers=_octet_headers(), data=image_bytes, timeout=30)
    resp.raise_for_status()
    return resp.json()


def identify_faces(face_ids: list[str]) -> list[dict]:
    """Identify faces against the person group.

    Returns list of {faceId, candidates: [{personId, confidence}]}.
    """
    if not face_ids:
        return []

    url = f"{_endpoint()}/face/v1.0/identify"
    resp = requests.post(
        url,
        headers=_headers(),
        json={
            "personGroupId": PERSON_GROUP_ID,
            "faceIds": face_ids,
            "maxNumOfCandidatesReturned": 1,
            "confidenceThreshold": CONFIDENCE_THRESHOLD,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def recognize_people(image_bytes: bytes) -> list[str]:
    """Full pipeline: detect faces in image, identify them, return list of names.

    This is the main function called during photo processing.
    Returns a list of recognized family member names (may be empty).
    """
    # Check if Face API is configured
    if not _endpoint() or not config.get("AZURE_FACE_KEY", ""):
        return []

    try:
        # Step 1: Detect faces
        faces = detect_faces(image_bytes)
        if not faces:
            return []

        face_ids = [f["faceId"] for f in faces if "faceId" in f]
        if not face_ids:
            return []

        # Step 2: Identify faces
        results = identify_faces(face_ids)

        # Step 3: Resolve person IDs to names
        identified_person_ids = set()
        for result in results:
            candidates = result.get("candidates", [])
            if candidates:
                identified_person_ids.add(candidates[0]["personId"])

        if not identified_person_ids:
            return []

        # Get names for identified persons
        persons = list_persons()
        person_map = {p["personId"]: p["name"] for p in persons}

        names = sorted(
            person_map[pid]
            for pid in identified_person_ids
            if pid in person_map
        )
        return names

    except Exception as e:
        # Face recognition is best-effort — don't fail the photo upload
        print(f"Face recognition failed: {e}")
        return []
