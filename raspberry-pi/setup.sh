#!/usr/bin/env bash
#
# FamilyFrame - Raspberry Pi USB Gadget Setup
#
# Configures a Raspberry Pi Zero 2 W (or Pi 4) to emulate a USB mass storage
# device. The TV sees it as a normal USB drive containing photos.
# The RPi syncs photos from OneDrive in the background via rclone.
#
# Compatible: RPi Zero 2 W, RPi 4 (USB-C port only), RPi Zero W
# Requires: Raspberry Pi OS (Bookworm, 64-bit Lite recommended)
#
# Usage:
#   chmod +x setup.sh
#   sudo ./setup.sh [--image-size 4G]
#
# After setup:
#   1. Configure rclone: rclone config (add OneDrive remote named "onedrive")
#   2. Optionally set Azure Face API key in /etc/familyframe/config.env
#   3. Reboot: sudo reboot
#   4. Plug USB data port into TV

set -euo pipefail

IMAGE_SIZE="4G"
FRAME_USER="${SUDO_USER:-pi}"
FRAME_DIR="/opt/familyframe"
IMAGE_FILE="$FRAME_DIR/usbdisk.img"
MOUNT_POINT="$FRAME_DIR/mnt"
PHOTOS_DIR="$MOUNT_POINT/Alle Fotos"
CONFIG_DIR="/etc/familyframe"
LOG_DIR="/var/log/familyframe"
STAGING_DIR="$FRAME_DIR/staging"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --image-size)
            IMAGE_SIZE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: sudo $0 [--image-size 4G]"
            exit 1
            ;;
    esac
done

if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root (sudo)."
    exit 1
fi

echo "=== FamilyFrame RPi USB Gadget Setup ==="
echo "USB disk image size: $IMAGE_SIZE"
echo "User: $FRAME_USER"
echo ""

# --- 1. System updates and dependencies ---
echo ">>> [1/8] Installing dependencies..."
apt-get update -qq
apt-get install -y -qq \
    rclone \
    python3 \
    python3-pip \
    python3-requests \
    dosfstools \
    exfatprogs

# --- 2. Create directory structure ---
echo ">>> [2/8] Creating directories..."
mkdir -p "$FRAME_DIR"
mkdir -p "$MOUNT_POINT"
mkdir -p "$STAGING_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"

# --- 3. Create FAT32 USB disk image ---
echo ">>> [3/8] Creating USB disk image ($IMAGE_SIZE)..."
if [ ! -f "$IMAGE_FILE" ]; then
    # Create a file of the specified size
    fallocate -l "$IMAGE_SIZE" "$IMAGE_FILE"

    # Format as FAT32 (most compatible with TVs)
    mkfs.vfat -F 32 -n "FAMILYFRAME" "$IMAGE_FILE"

    echo "    Created new disk image: $IMAGE_FILE"
else
    echo "    Disk image already exists, skipping creation."
fi

# --- 4. Set up loopback mount ---
echo ">>> [4/8] Configuring loopback mount..."

# Create fstab entry for the loopback mount
if ! grep -q "$IMAGE_FILE" /etc/fstab; then
    echo "$IMAGE_FILE $MOUNT_POINT vfat loop,rw,umask=000,uid=$(id -u "$FRAME_USER"),gid=$(id -g "$FRAME_USER") 0 0" >> /etc/fstab
fi

# Mount now
if ! mountpoint -q "$MOUNT_POINT"; then
    mount "$MOUNT_POINT"
fi

# Create default folder structure
mkdir -p "$PHOTOS_DIR"

echo "    Mounted $IMAGE_FILE at $MOUNT_POINT"

# --- 5. Enable USB gadget mode ---
echo ">>> [5/8] Enabling USB gadget mode..."

# Enable dwc2 overlay in config.txt
CONFIG_TXT="/boot/firmware/config.txt"
if [ ! -f "$CONFIG_TXT" ]; then
    CONFIG_TXT="/boot/config.txt"
fi

if ! grep -q "^dtoverlay=dwc2" "$CONFIG_TXT"; then
    echo "dtoverlay=dwc2" >> "$CONFIG_TXT"
    echo "    Added dwc2 overlay to $CONFIG_TXT"
fi

# Load dwc2 module on boot
if ! grep -q "^dwc2" /etc/modules; then
    echo "dwc2" >> /etc/modules
    echo "    Added dwc2 to /etc/modules"
fi

# Note: we do NOT load g_mass_storage at boot via /etc/modules
# because we need to unmount the image first. The systemd service handles this.

# --- 6. Create USB gadget management scripts ---
echo ">>> [6/8] Creating USB gadget management scripts..."

# Script to expose USB drive to TV (read-only)
cat > "$FRAME_DIR/usb-gadget-start.sh" << 'GADGET_START'
#!/usr/bin/env bash
# Expose the disk image as a USB mass storage device to the TV
# The image must NOT be loop-mounted while exposed via USB gadget

IMAGE_FILE="/opt/familyframe/usbdisk.img"
MOUNT_POINT="/opt/familyframe/mnt"

# Unmount the loopback mount first (TV needs exclusive access)
if mountpoint -q "$MOUNT_POINT"; then
    umount "$MOUNT_POINT" 2>/dev/null || true
fi

# Load the USB mass storage gadget module
# ro=1: read-only from TV side (RPi manages content)
# stall=0: prevents stalling on some TVs
# removable=1: allows TV to detect disconnect/reconnect
modprobe g_mass_storage file="$IMAGE_FILE" stall=0 ro=1 removable=1

echo "USB gadget started: TV can now see the drive"
GADGET_START
chmod +x "$FRAME_DIR/usb-gadget-start.sh"

# Script to take USB drive back for writing (RPi side)
cat > "$FRAME_DIR/usb-gadget-stop.sh" << 'GADGET_STOP'
#!/usr/bin/env bash
# Take back the disk image for writing (disconnect from TV temporarily)

MOUNT_POINT="/opt/familyframe/mnt"

# Remove the USB gadget module
modprobe -r g_mass_storage 2>/dev/null || true

# Brief pause for clean disconnect
sleep 1

# Re-mount for writing
if ! mountpoint -q "$MOUNT_POINT"; then
    mount "$MOUNT_POINT"
fi

echo "USB gadget stopped: RPi can now write to the drive"
GADGET_STOP
chmod +x "$FRAME_DIR/usb-gadget-stop.sh"

# --- 7. Create systemd services ---
echo ">>> [7/8] Creating systemd services..."

# Service: USB gadget on boot (expose drive to TV)
cat > /etc/systemd/system/familyframe-usb.service << 'SERVICE_USB'
[Unit]
Description=FamilyFrame USB Gadget
After=local-fs.target
DefaultDependencies=no

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/opt/familyframe/usb-gadget-start.sh
ExecStop=/opt/familyframe/usb-gadget-stop.sh

[Install]
WantedBy=multi-user.target
SERVICE_USB

# Service: photo sync timer (runs sync.py periodically)
cat > /etc/systemd/system/familyframe-sync.service << SERVICE_SYNC
[Unit]
Description=FamilyFrame Photo Sync
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$FRAME_USER
ExecStart=/usr/bin/python3 $FRAME_DIR/sync.py
Environment=HOME=/home/$FRAME_USER
StandardOutput=append:$LOG_DIR/sync.log
StandardError=append:$LOG_DIR/sync.log
SERVICE_SYNC

cat > /etc/systemd/system/familyframe-sync.timer << 'TIMER'
[Unit]
Description=FamilyFrame Photo Sync Timer

[Timer]
OnBootSec=60
OnUnitActiveSec=300
RandomizedDelaySec=30

[Install]
WantedBy=timers.target
TIMER

# --- 8. Create configuration file ---
echo ">>> [8/8] Creating configuration..."

if [ ! -f "$CONFIG_DIR/config.env" ]; then
    cat > "$CONFIG_DIR/config.env" << 'CONFIG'
# FamilyFrame Configuration
# Edit this file to configure the photo sync

# OneDrive remote name (as configured in rclone)
RCLONE_REMOTE=onedrive

# OneDrive folder path to sync from
ONEDRIVE_FOLDER=/FamilyFrame/photos

# Azure Face API (optional — leave empty to disable face recognition)
AZURE_FACE_KEY=
AZURE_FACE_ENDPOINT=

# Sync interval is controlled by the systemd timer (default: 5 minutes)
# Edit /etc/systemd/system/familyframe-sync.timer to change

# Maximum photo dimension (resize larger photos to save space on USB image)
# Set to 0 to disable resizing
MAX_PHOTO_DIMENSION=1920
CONFIG
    echo "    Created config at $CONFIG_DIR/config.env"
else
    echo "    Config already exists, skipping."
fi

# Set permissions
chown -R "$FRAME_USER:$FRAME_USER" "$FRAME_DIR"
chown -R "$FRAME_USER:$FRAME_USER" "$LOG_DIR"
chmod 600 "$CONFIG_DIR/config.env"

# Enable services
systemctl daemon-reload
systemctl enable familyframe-usb.service
systemctl enable familyframe-sync.timer

# --- 9. Optimize for 24/7 operation ---
echo ">>> Optimizing for continuous operation..."

# Reduce SD card writes (tmpfs for logs)
if ! grep -q "tmpfs /tmp" /etc/fstab; then
    echo "tmpfs /tmp tmpfs defaults,noatime,nosuid,size=100m 0 0" >> /etc/fstab
fi

# Enable hardware watchdog
if ! grep -q "RuntimeWatchdogSec" /etc/systemd/system.conf; then
    echo "RuntimeWatchdogSec=15" >> /etc/systemd/system.conf
fi

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo ""
echo "  1. Configure rclone for OneDrive:"
echo "     rclone config"
echo "     (Create a remote named 'onedrive' with type 'onedrive')"
echo ""
echo "  2. Test rclone connection:"
echo "     rclone ls onedrive:/FamilyFrame/photos/ --max-depth 1"
echo ""
echo "  3. (Optional) Configure face recognition:"
echo "     sudo nano /etc/familyframe/config.env"
echo "     Set AZURE_FACE_KEY and AZURE_FACE_ENDPOINT"
echo ""
echo "  4. Copy sync.py to $FRAME_DIR:"
echo "     sudo cp sync.py $FRAME_DIR/"
echo "     sudo chown $FRAME_USER:$FRAME_USER $FRAME_DIR/sync.py"
echo ""
echo "  5. Reboot and plug USB data port into TV:"
echo "     sudo reboot"
echo ""
echo "  RPi Zero 2 W: use the USB port labeled 'USB' (not 'PWR')"
echo "  RPi 4: use the USB-C port (the power port doubles as OTG)"
echo ""
echo "Useful commands:"
echo "  journalctl -u familyframe-usb    # USB gadget status"
echo "  journalctl -u familyframe-sync   # Sync logs"
echo "  cat /var/log/familyframe/sync.log # Sync history"
echo "  sudo systemctl start familyframe-sync  # Manual sync"
echo "  sudo $FRAME_DIR/usb-gadget-stop.sh     # Take drive back for writing"
echo "  sudo $FRAME_DIR/usb-gadget-start.sh    # Re-expose drive to TV"
