#!/usr/bin/env python3
"""
FamilyFrame Photo Sync

Syncs photos from OneDrive (via rclone) to the local USB disk image.
Handles the USB gadget lifecycle: stop gadget → mount image → sync → unmount → restart gadget.

Run manually:  python3 sync.py
Run via systemd: sudo systemctl start familyframe-sync
"""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from face_recognition import FaceRecognizer

try:
    from enhance import enhance_photo, generate_special_folders, HAS_PIL
    HAS_ENHANCE = HAS_PIL
except ImportError:
    HAS_ENHANCE = False


def read_photo_metadata(file_path: Path) -> dict:
    """Read FamilyFrame metadata from EXIF UserComment embedded by the upload API.

    Returns dict with keys: caption, uploaded_by, description, location.
    Returns empty values for photos uploaded directly to OneDrive (no metadata).
    """
    result = {"caption": "", "uploaded_by": "", "description": "", "location": ""}
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
    except ImportError:
        return result

    TAG_USER_COMMENT = 37510

    try:
        img = Image.open(file_path)
        exif_data = img._getexif()
        if not exif_data:
            return result
    except Exception:
        return result

    # Try UserComment (JSON blob from upload API)
    user_comment = exif_data.get(TAG_USER_COMMENT)
    if user_comment:
        try:
            import json as _json
            if isinstance(user_comment, bytes) and len(user_comment) > 8:
                json_str = user_comment[8:].decode("utf-8")
                meta = _json.loads(json_str)
                if meta.get("source") == "familyframe-web":
                    result["caption"] = meta.get("caption", "")
                    result["uploaded_by"] = meta.get("uploaded_by", "")
                    result["description"] = meta.get("description", "")
                    result["location"] = meta.get("location", "")
                    return result
        except Exception:
            pass

    # Fall back to standard EXIF fields
    decoded = {}
    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id, tag_id)
        decoded[tag_name] = value

    if decoded.get("ImageDescription"):
        result["caption"] = str(decoded["ImageDescription"]).strip()
    if decoded.get("Artist"):
        result["uploaded_by"] = str(decoded["Artist"]).strip()

    return result

# --- Configuration ---
FRAME_DIR = Path("/opt/familyframe")
MOUNT_POINT = FRAME_DIR / "mnt"
STAGING_DIR = FRAME_DIR / "staging"
STATE_FILE = FRAME_DIR / "sync_state.json"
CONFIG_FILE = Path("/etc/familyframe/config.env")
GADGET_START = FRAME_DIR / "usb-gadget-start.sh"
GADGET_STOP = FRAME_DIR / "usb-gadget-stop.sh"

ALL_PHOTOS_DIR = "Alle Fotos"

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("familyframe-sync")


def load_config() -> dict:
    """Load configuration from /etc/familyframe/config.env."""
    config = {
        "RCLONE_REMOTE": "onedrive",
        "ONEDRIVE_FOLDER": "/FamilyFrame/photos",
        "AZURE_FACE_KEY": "",
        "AZURE_FACE_ENDPOINT": "",
        "MAX_PHOTO_DIMENSION": "1920",
        "ENHANCE_PHOTOS": "false",
    }
    if CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                config[key.strip()] = value.strip()
    return config


def create_face_recognizer(config: dict) -> Optional[FaceRecognizer]:
    """Create a FaceRecognizer if Azure Face API is configured."""
    key = config.get("AZURE_FACE_KEY", "")
    endpoint = config.get("AZURE_FACE_ENDPOINT", "")
    if key and endpoint:
        log.info("Face recognition enabled (Azure Face API)")
        return FaceRecognizer(endpoint, key)
    log.info("Face recognition disabled (no Azure Face API key configured)")
    return None


def load_state() -> dict:
    """Load sync state (tracks which photos have been processed)."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"synced_files": {}, "last_sync": None}


def save_state(state: dict):
    """Save sync state to disk."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    log.debug(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def stop_usb_gadget():
    """Disconnect USB drive from TV and mount image for writing."""
    log.info("Stopping USB gadget (disconnecting from TV)...")
    run_cmd(["sudo", str(GADGET_STOP)], check=False)
    # Give the filesystem a moment to settle
    time.sleep(1)


def start_usb_gadget():
    """Unmount image and re-expose as USB drive to TV."""
    log.info("Starting USB gadget (re-connecting to TV)...")
    # Ensure any writes are flushed
    run_cmd(["sync"])
    run_cmd(["sudo", str(GADGET_START)], check=False)


def rclone_list_files(config: dict) -> list[dict]:
    """List all image files in the OneDrive folder using rclone lsjson."""
    remote = config["RCLONE_REMOTE"]
    folder = config["ONEDRIVE_FOLDER"]
    remote_path = f"{remote}:{folder}"

    result = run_cmd(
        ["rclone", "lsjson", remote_path, "--recursive", "--files-only"],
        check=False,
    )

    if result.returncode != 0:
        log.error(f"rclone lsjson failed: {result.stderr}")
        return []

    try:
        files = json.loads(result.stdout)
    except json.JSONDecodeError:
        log.error("Failed to parse rclone lsjson output")
        return []

    # Filter to image files only
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic"}
    return [
        f for f in files
        if Path(f["Name"]).suffix.lower() in image_extensions
    ]


def rclone_download_file(config: dict, relative_path: str, dest: Path):
    """Download a single file from OneDrive via rclone."""
    remote = config["RCLONE_REMOTE"]
    folder = config["ONEDRIVE_FOLDER"]
    source = f"{remote}:{folder}/{relative_path}"

    dest.parent.mkdir(parents=True, exist_ok=True)

    result = run_cmd(
        ["rclone", "copyto", source, str(dest)],
        check=False,
    )

    if result.returncode != 0:
        log.error(f"Failed to download {relative_path}: {result.stderr}")
        return False
    return True


def recognize_and_copy_to_person_folders(
    recognizer: Optional[FaceRecognizer],
    staging_file: Path,
    filename: str,
    state_entry: dict,
):
    """Run face recognition on a photo and copy it into person-named folders.

    A photo with Anna and Thomas in it gets copied to both /Anna/ and /Thomas/.
    Results are cached in state_entry["people"] to avoid re-processing.
    """
    if recognizer is None:
        return

    try:
        image_bytes = staging_file.read_bytes()
        people = recognizer.recognize(image_bytes)
    except Exception as e:
        log.warning(f"Face recognition failed for {filename}: {e}")
        return

    state_entry["people"] = people

    if not people:
        log.debug(f"No faces recognized in {filename}")
        return

    log.info(f"Recognized in {filename}: {', '.join(people)}")

    for person_name in people:
        # Sanitize folder name (remove problematic characters for FAT32)
        safe_name = person_name.replace("/", "_").replace("\\", "_").strip()
        person_dir = MOUNT_POINT / safe_name
        person_dir.mkdir(parents=True, exist_ok=True)

        person_file = person_dir / filename
        if not person_file.exists():
            shutil.copy2(str(staging_file), str(person_file))


def remove_from_person_folders(filename: str, people: list[str]):
    """Remove a photo from all person folders it was sorted into."""
    for person_name in people:
        safe_name = person_name.replace("/", "_").replace("\\", "_").strip()
        person_file = MOUNT_POINT / safe_name / filename
        if person_file.exists():
            person_file.unlink()
            log.info(f"Removed {filename} from {safe_name}/")


def sync_photos(
    config: dict,
    state: dict,
    recognizer: Optional[FaceRecognizer] = None,
) -> bool:
    """
    Main sync logic:
    1. List remote files
    2. Download new/changed files to staging
    3. Run face recognition → sort into person folders
    4. Copy to USB image (into appropriate folders)
    5. Remove deleted files from USB image
    Returns True if any changes were made.
    """
    log.info("Starting photo sync...")
    remote_files = rclone_list_files(config)

    if not remote_files:
        log.info("No remote files found (or rclone error). Skipping sync.")
        return False

    # Build a map of remote files: relative_path → {size, mod_time}
    remote_map = {}
    for f in remote_files:
        rel_path = f["Path"]
        remote_map[rel_path] = {
            "size": f.get("Size", 0),
            "mod_time": f.get("ModTime", ""),
        }

    synced = state.get("synced_files", {})
    changes_made = False

    # --- Download new or changed files ---
    for rel_path, info in remote_map.items():
        file_key = rel_path
        prev = synced.get(file_key)

        # Skip if already synced and unchanged
        if prev and prev.get("size") == info["size"] and prev.get("mod_time") == info["mod_time"]:
            continue

        log.info(f"Downloading: {rel_path}")
        staging_file = STAGING_DIR / rel_path

        if rclone_download_file(config, rel_path, staging_file):
            # Check if photo enhancement is enabled
            do_enhance = (
                HAS_ENHANCE
                and config.get("ENHANCE_PHOTOS", "false").lower() == "true"
            )

            # Determine if photo is "new" (< 7 days)
            is_new_photo = False
            try:
                mod_dt = datetime.fromisoformat(
                    info["mod_time"].replace("Z", "+00:00").split(".")[0]
                )
                is_new_photo = (datetime.now(mod_dt.tzinfo) - mod_dt).days < 7
            except (ValueError, IndexError):
                pass

            # Read caption/uploader metadata from EXIF (embedded by upload API)
            photo_meta = read_photo_metadata(staging_file) if do_enhance else {}

            # Determine target path on USB image
            # Files in subdirectories keep their folder structure
            # Files in root go to "Alle Fotos/"
            parts = Path(rel_path).parts
            if len(parts) == 1:
                # Root file → Alle Fotos/
                usb_dest = MOUNT_POINT / ALL_PHOTOS_DIR / parts[0]
            else:
                # Subfolder → keep structure, also copy to Alle Fotos/
                usb_dest = MOUNT_POINT / rel_path
                usb_all = MOUNT_POINT / ALL_PHOTOS_DIR / Path(rel_path).name

                # Avoid name collisions in Alle Fotos
                if usb_all.exists() and usb_all != usb_dest:
                    stem = usb_all.stem
                    suffix = usb_all.suffix
                    folder_name = parts[0]
                    usb_all = MOUNT_POINT / ALL_PHOTOS_DIR / f"{stem}_{folder_name}{suffix}"

                usb_all.parent.mkdir(parents=True, exist_ok=True)
                if do_enhance:
                    enhance_photo(
                        staging_file, usb_all,
                        caption=photo_meta.get("caption", ""),
                        date_taken=info.get("mod_time", ""),
                        location=photo_meta.get("location", ""),
                        uploaded_by=photo_meta.get("uploaded_by", ""),
                        is_new=is_new_photo,
                    )
                else:
                    shutil.copy2(str(staging_file), str(usb_all))

            usb_dest.parent.mkdir(parents=True, exist_ok=True)
            if do_enhance:
                enhance_photo(
                    staging_file, usb_dest,
                    caption=photo_meta.get("caption", ""),
                    date_taken=info.get("mod_time", ""),
                    location=photo_meta.get("location", ""),
                    uploaded_by=photo_meta.get("uploaded_by", ""),
                    is_new=is_new_photo,
                )
            else:
                shutil.copy2(str(staging_file), str(usb_dest))

            # Build state entry
            state_entry = {
                "size": info["size"],
                "mod_time": info["mod_time"],
                "usb_path": str(usb_dest.relative_to(MOUNT_POINT)),
                "people": [],
            }

            # Run face recognition and copy to person folders
            recognize_and_copy_to_person_folders(
                recognizer, staging_file, Path(rel_path).name, state_entry
            )

            synced[file_key] = state_entry
            changes_made = True

            # Clean up staging file
            staging_file.unlink(missing_ok=True)

    # --- Remove deleted files ---
    deleted_keys = [k for k in synced if k not in remote_map]
    for key in deleted_keys:
        info = synced[key]

        # Remove from main location
        usb_path = MOUNT_POINT / info.get("usb_path", "")
        if usb_path.exists():
            log.info(f"Removing deleted photo: {usb_path}")
            usb_path.unlink()

        # Remove from Alle Fotos
        filename = Path(key).name
        all_photos_file = MOUNT_POINT / ALL_PHOTOS_DIR / filename
        if all_photos_file.exists():
            all_photos_file.unlink()

        # Remove from person folders
        people = info.get("people", [])
        if people:
            remove_from_person_folders(filename, people)

        del synced[key]
        changes_made = True

    # --- Clean up empty directories ---
    if changes_made:
        for dirpath, dirnames, filenames in os.walk(str(MOUNT_POINT), topdown=False):
            dp = Path(dirpath)
            if dp == MOUNT_POINT:
                continue
            if not any(dp.iterdir()):
                dp.rmdir()
                log.info(f"Removed empty directory: {dp}")

    # --- Generate special folders (always regenerated) ---
    do_enhance = (
        HAS_ENHANCE
        and config.get("ENHANCE_PHOTOS", "false").lower() == "true"
    )
    if do_enhance:
        generate_special_folders(MOUNT_POINT, synced)

    state["synced_files"] = synced
    state["last_sync"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    save_state(state)

    if changes_made:
        log.info("Sync complete — changes detected.")
    else:
        log.info("Sync complete — no changes.")

    return changes_made


def main():
    config = load_config()
    state = load_state()

    # Check if rclone is configured
    result = run_cmd(["rclone", "listremotes"], check=False)
    remote_name = config["RCLONE_REMOTE"] + ":"
    if remote_name not in result.stdout:
        log.error(
            f"rclone remote '{config['RCLONE_REMOTE']}' not configured. "
            f"Run 'rclone config' to set it up."
        )
        sys.exit(1)

    # Initialize face recognition (if configured)
    recognizer = create_face_recognizer(config)

    # Stop USB gadget → mount image → sync → restart gadget
    stop_usb_gadget()

    try:
        changes = sync_photos(config, state, recognizer)
    except Exception as e:
        log.error(f"Sync failed: {e}", exc_info=True)
        changes = False
    finally:
        # Always re-expose the USB drive to the TV
        start_usb_gadget()

    if changes:
        log.info("TV should pick up new photos shortly.")


if __name__ == "__main__":
    main()
