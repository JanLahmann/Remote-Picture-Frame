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
from pathlib import Path

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
    }
    if CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                config[key.strip()] = value.strip()
    return config


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


def sync_photos(config: dict, state: dict) -> bool:
    """
    Main sync logic:
    1. List remote files
    2. Download new/changed files to staging
    3. Copy to USB image (into appropriate folders)
    4. Remove deleted files from USB image
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
                shutil.copy2(str(staging_file), str(usb_all))

            usb_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(staging_file), str(usb_dest))

            # Update state
            synced[file_key] = {
                "size": info["size"],
                "mod_time": info["mod_time"],
                "usb_path": str(usb_dest.relative_to(MOUNT_POINT)),
            }
            changes_made = True

            # Clean up staging file
            staging_file.unlink(missing_ok=True)

    # --- Remove deleted files ---
    deleted_keys = [k for k in synced if k not in remote_map]
    for key in deleted_keys:
        info = synced[key]
        usb_path = MOUNT_POINT / info.get("usb_path", "")
        if usb_path.exists():
            log.info(f"Removing deleted photo: {usb_path}")
            usb_path.unlink()
        # Also remove from Alle Fotos
        filename = Path(key).name
        all_photos_file = MOUNT_POINT / ALL_PHOTOS_DIR / filename
        if all_photos_file.exists():
            all_photos_file.unlink()
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

    # Stop USB gadget → mount image → sync → restart gadget
    stop_usb_gadget()

    try:
        changes = sync_photos(config, state)
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
