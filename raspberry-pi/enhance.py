#!/usr/bin/env python3
"""
FamilyFrame Photo Enhancement (Path B)

Enhances photos before placing them on the USB drive:
- Burns captions, date, and location into the photo as a semi-transparent overlay
- Adds a "Neu" badge to photos less than 7 days old
- Generates special folders: "Neue Fotos" (last 7 days), "Heute vor..." (on this day)
- Smart filename ordering so TV sorts newest first
- Ensures baseline JPEG output (Panasonic TVs don't support progressive JPEG)

Target TV: Panasonic TX-40FSW404 (1920x1080, JPEG baseline only, USB FAT32)

Usage:
  Called by sync.py after downloading photos, before copying to USB image.
  Can also be run standalone for testing:
    python3 enhance.py /path/to/source.jpg /path/to/output.jpg --caption "Urlaub" --date "2026-07-15"
"""

import logging
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont, ExifTags
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

log = logging.getLogger("familyframe-sync")

# --- Configuration ---
TV_WIDTH = 1920
TV_HEIGHT = 1080
JPEG_QUALITY = 85
NEW_PHOTO_DAYS = 7

# Badge colors
BADGE_NEW_BG = (78, 204, 163, 200)       # green, semi-transparent
BADGE_NEW_TEXT = (0, 0, 0, 255)           # black
OVERLAY_BG = (0, 0, 0, 140)              # black, semi-transparent
OVERLAY_TEXT = (255, 255, 255, 230)       # white


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font, falling back to default if no TrueType font is found."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _extract_exif_date(img: Image.Image) -> Optional[datetime]:
    """Extract date taken from EXIF data."""
    try:
        exif = img._getexif()
        if not exif:
            return None
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, "")
            if tag == "DateTimeOriginal":
                return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def enhance_photo(
    source_path: Path,
    dest_path: Path,
    caption: str = "",
    date_taken: Optional[str] = None,
    location: str = "",
    uploaded_by: str = "",
    is_new: bool = False,
) -> bool:
    """Enhance a photo with overlay text and badges, save as baseline JPEG.

    Args:
        source_path: Path to the original photo
        dest_path: Path to save the enhanced photo
        caption: Caption text to overlay
        date_taken: ISO date string (e.g. "2026-07-15T14:30:00Z")
        location: Location name (e.g. "Warnemuende")
        uploaded_by: Name of the uploader
        is_new: Whether to add a "Neu" badge

    Returns:
        True if enhancement succeeded, False otherwise.
    """
    if not HAS_PIL:
        log.warning("Pillow not installed — skipping photo enhancement")
        return False

    try:
        img = Image.open(source_path)

        # Convert to RGB if necessary (handles RGBA, palette, etc.)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Auto-rotate based on EXIF orientation
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Try to get date from EXIF if not provided
        if not date_taken:
            exif_date = _extract_exif_date(img)
            if exif_date:
                date_taken = exif_date.isoformat()

        width, height = img.size

        # Create an overlay layer (RGBA for transparency)
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # --- Caption / metadata overlay at bottom ---
        meta_parts = []
        if caption:
            meta_parts.append(caption)
        if date_taken:
            try:
                dt = datetime.fromisoformat(date_taken.replace("Z", "+00:00"))
                meta_parts.append(dt.strftime("%d. %B %Y"))
            except ValueError:
                pass
        if location:
            meta_parts.append(location)
        if uploaded_by:
            meta_parts.append(f"von {uploaded_by}")

        if meta_parts:
            # Font size relative to image height
            font_size = max(16, height // 30)
            font = _get_font(font_size)

            text = "  ·  ".join(meta_parts)

            # Measure text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Draw semi-transparent background bar at bottom
            padding = font_size // 2
            bar_height = text_height + padding * 2
            bar_y = height - bar_height

            draw.rectangle(
                [(0, bar_y), (width, height)],
                fill=OVERLAY_BG,
            )

            # Center text horizontally
            text_x = (width - text_width) // 2
            text_y = bar_y + padding

            draw.text((text_x, text_y), text, font=font, fill=OVERLAY_TEXT)

        # --- "Neu" badge in top-right corner ---
        if is_new:
            badge_font_size = max(14, height // 25)
            badge_font = _get_font(badge_font_size)
            badge_text = "Neu"

            bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
            badge_w = bbox[2] - bbox[0]
            badge_h = bbox[3] - bbox[1]

            badge_padding = badge_font_size // 3
            badge_x = width - badge_w - badge_padding * 4
            badge_y = badge_padding

            # Draw rounded-ish badge background
            draw.rounded_rectangle(
                [
                    (badge_x, badge_y),
                    (badge_x + badge_w + badge_padding * 2, badge_y + badge_h + badge_padding * 2),
                ],
                radius=badge_padding,
                fill=BADGE_NEW_BG,
            )

            draw.text(
                (badge_x + badge_padding, badge_y + badge_padding),
                badge_text,
                font=badge_font,
                fill=BADGE_NEW_TEXT,
            )

        # Composite overlay onto image
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)
        img = img.convert("RGB")

        # Save as baseline JPEG (not progressive — Panasonic TV compatibility)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(
            dest_path,
            "JPEG",
            quality=JPEG_QUALITY,
            progressive=False,
            optimize=True,
        )

        return True

    except Exception as e:
        log.error(f"Failed to enhance {source_path}: {e}")
        return False


def generate_smart_filename(index: int, total: int, original_name: str) -> str:
    """Generate a filename that sorts newest-first on the TV.

    TV media players sort by filename (alphabetically). We prefix with a
    zero-padded index so the sort order is controlled by us.

    Args:
        index: Sort position (0 = first/newest)
        total: Total number of photos
        original_name: Original filename (used as suffix for uniqueness)
    """
    # Pad to 5 digits — supports up to 99,999 photos
    stem = Path(original_name).stem
    # Keep a short version of the original name for readability
    short_name = re.sub(r"[^a-zA-Z0-9]", "_", stem)[:20]
    return f"{index:05d}_{short_name}.jpg"


def generate_special_folders(
    mount_point: Path,
    synced_files: dict,
):
    """Generate special folders on the USB drive.

    - "Neue Fotos": Photos from the last 7 days
    - "Heute vor...": Photos from today's date in previous years

    Args:
        mount_point: Root of the USB drive mount
        synced_files: State dict of synced files (from sync_state.json)
    """
    if not HAS_PIL:
        log.warning("Pillow not installed — skipping special folder generation")
        return

    now = datetime.now()
    today_md = now.strftime("%m-%d")
    cutoff_new = now - timedelta(days=NEW_PHOTO_DAYS)

    neue_dir = mount_point / "Neue Fotos"
    heute_dir = mount_point / "Heute vor..."

    # Clean existing special folders (regenerated each sync)
    for special_dir in [neue_dir, heute_dir]:
        if special_dir.exists():
            for f in special_dir.iterdir():
                if f.is_file():
                    f.unlink()

    neue_count = 0
    heute_count = 0

    for rel_path, info in synced_files.items():
        usb_path_str = info.get("usb_path", "")
        if not usb_path_str:
            continue

        source = mount_point / usb_path_str
        if not source.exists():
            continue

        # Determine photo date from mod_time
        mod_time_str = info.get("mod_time", "")
        try:
            # rclone mod_time format: "2026-07-15T14:30:00.000000000Z"
            mod_time = datetime.fromisoformat(
                mod_time_str.replace("Z", "+00:00").split(".")[0]
            )
        except (ValueError, IndexError):
            continue

        filename = Path(rel_path).name

        # "Neue Fotos" — last 7 days
        if mod_time.replace(tzinfo=None) > cutoff_new:
            neue_dir.mkdir(parents=True, exist_ok=True)
            dest = neue_dir / filename
            if not dest.exists():
                try:
                    os.link(str(source), str(dest))
                except OSError:
                    # Hard links not supported on FAT32 — fall back to copy
                    import shutil
                    shutil.copy2(str(source), str(dest))
                neue_count += 1

        # "Heute vor..." — same month-day in a previous year
        photo_md = mod_time.strftime("%m-%d")
        if photo_md == today_md and mod_time.year < now.year:
            heute_dir.mkdir(parents=True, exist_ok=True)
            years_ago = now.year - mod_time.year
            prefix = f"Vor_{years_ago}_Jahren_"
            dest = heute_dir / f"{prefix}{filename}"
            if not dest.exists():
                try:
                    os.link(str(source), str(dest))
                except OSError:
                    import shutil
                    shutil.copy2(str(source), str(dest))
                heute_count += 1

    # Clean up empty special folders
    for special_dir in [neue_dir, heute_dir]:
        if special_dir.exists() and not any(special_dir.iterdir()):
            special_dir.rmdir()

    if neue_count:
        log.info(f"'Neue Fotos' folder: {neue_count} photos")
    if heute_count:
        log.info(f"'Heute vor...' folder: {heute_count} photos")


# --- CLI for testing ---
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enhance a photo with overlay")
    parser.add_argument("source", help="Source photo path")
    parser.add_argument("dest", help="Destination path")
    parser.add_argument("--caption", default="", help="Caption text")
    parser.add_argument("--date", default="", help="Date taken (ISO format)")
    parser.add_argument("--location", default="", help="Location name")
    parser.add_argument("--uploaded-by", default="", help="Uploader name")
    parser.add_argument("--new", action="store_true", help="Add 'Neu' badge")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    ok = enhance_photo(
        Path(args.source),
        Path(args.dest),
        caption=args.caption,
        date_taken=args.date,
        location=args.location,
        uploaded_by=args.uploaded_by,
        is_new=args.new,
    )
    print(f"Enhancement {'succeeded' if ok else 'failed'}")
