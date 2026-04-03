"""Azure Face API client for identifying people in photos.

Standalone module for RPi — reads config from /etc/familyframe/config.env.
Uses Azure AI Face service (free tier: 30K transactions/month).

The person group must already be set up and trained via the admin interface
before identification works.
"""

import logging
import requests

log = logging.getLogger("familyframe-sync")

CONFIDENCE_THRESHOLD = 0.6
PERSON_GROUP_ID = "familyframe-family"


class FaceRecognizer:
    """Azure Face API client for identifying family members in photos."""

    def __init__(self, endpoint: str, key: str):
        self.endpoint = endpoint.rstrip("/")
        self.key = key
        self._person_cache: dict[str, str] | None = None

    def _headers(self) -> dict:
        return {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": "application/json",
        }

    def _octet_headers(self) -> dict:
        return {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": "application/octet-stream",
        }

    def _get_person_map(self) -> dict[str, str]:
        """Get personId → name mapping. Cached to avoid repeated API calls."""
        if self._person_cache is not None:
            return self._person_cache

        url = f"{self.endpoint}/face/v1.0/persongroups/{PERSON_GROUP_ID}/persons"
        resp = requests.get(url, headers=self._headers(), timeout=15)
        resp.raise_for_status()

        self._person_cache = {
            p["personId"]: p["name"] for p in resp.json()
        }
        return self._person_cache

    def detect_faces(self, image_bytes: bytes) -> list[str]:
        """Detect faces in image. Returns list of faceIds."""
        url = (
            f"{self.endpoint}/face/v1.0/detect"
            f"?returnFaceId=true&recognitionModel=recognition_04"
            f"&detectionModel=detection_03"
        )
        resp = requests.post(
            url, headers=self._octet_headers(), data=image_bytes, timeout=30
        )
        resp.raise_for_status()
        return [f["faceId"] for f in resp.json() if "faceId" in f]

    def identify_faces(self, face_ids: list[str]) -> list[str]:
        """Identify faces against the person group. Returns list of personIds."""
        if not face_ids:
            return []

        url = f"{self.endpoint}/face/v1.0/identify"
        resp = requests.post(
            url,
            headers=self._headers(),
            json={
                "personGroupId": PERSON_GROUP_ID,
                "faceIds": face_ids,
                "maxNumOfCandidatesReturned": 1,
                "confidenceThreshold": CONFIDENCE_THRESHOLD,
            },
            timeout=30,
        )
        resp.raise_for_status()

        person_ids = []
        for result in resp.json():
            candidates = result.get("candidates", [])
            if candidates:
                person_ids.append(candidates[0]["personId"])
        return person_ids

    def recognize(self, image_bytes: bytes) -> list[str]:
        """Full pipeline: detect → identify → return list of names.

        Returns a sorted list of recognized family member names (may be empty).
        This is the main method to call for each photo.
        """
        try:
            face_ids = self.detect_faces(image_bytes)
            if not face_ids:
                return []

            person_ids = self.identify_faces(face_ids)
            if not person_ids:
                return []

            person_map = self._get_person_map()
            names = sorted(
                person_map[pid]
                for pid in set(person_ids)
                if pid in person_map
            )
            return names

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                log.error("Azure Face API: invalid key or endpoint")
            elif e.response is not None and e.response.status_code == 404:
                log.warning(
                    "Azure Face API: person group not found. "
                    "Set up face recognition via the admin interface first."
                )
            else:
                log.error(f"Azure Face API error: {e}")
            return []
        except Exception as e:
            log.warning(f"Face recognition failed (non-critical): {e}")
            return []
