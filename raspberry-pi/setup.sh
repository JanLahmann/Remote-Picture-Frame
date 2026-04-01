#!/usr/bin/env bash
#
# Raspberry Pi Kiosk Mode Setup for FamilyFrame
#
# Run this script on a fresh Raspberry Pi OS (Bookworm) installation.
# It configures the Pi to boot directly into a fullscreen Chromium browser
# showing the FamilyFrame PWA.
#
# Usage:
#   chmod +x setup.sh
#   sudo ./setup.sh https://your-familyframe-url.example.com
#

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: sudo $0 <FAMILYFRAME_URL>"
    echo "Example: sudo $0 https://familyframe.example.com"
    exit 1
fi

FRAME_URL="$1"
KIOSK_USER="${2:-pi}"

echo "=== FamilyFrame Raspberry Pi Kiosk Setup ==="
echo "URL: $FRAME_URL"
echo "User: $KIOSK_USER"
echo ""

# --- 1. System updates ---
echo ">>> Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# --- 2. Install required packages ---
echo ">>> Installing Chromium and dependencies..."
apt-get install -y -qq \
    chromium-browser \
    xdotool \
    unclutter \
    xserver-xorg \
    x11-xserver-utils \
    xinit

# --- 3. Disable screen blanking and power management ---
echo ">>> Disabling screen blanking..."
mkdir -p /etc/X11/xorg.conf.d
cat > /etc/X11/xorg.conf.d/10-blanking.conf << 'XCONF'
Section "ServerFlags"
    Option "BlankTime" "0"
    Option "StandbyTime" "0"
    Option "SuspendTime" "0"
    Option "OffTime" "0"
EndSection
XCONF

# --- 4. Create kiosk startup script ---
echo ">>> Creating kiosk startup script..."
KIOSK_SCRIPT="/home/$KIOSK_USER/kiosk.sh"
cat > "$KIOSK_SCRIPT" << KIOSK
#!/usr/bin/env bash
# FamilyFrame Kiosk Mode

# Disable screen saver and power management
xset s off
xset s noblank
xset -dpms

# Hide mouse cursor after 3 seconds of inactivity
unclutter -idle 3 -root &

# Wait for network
sleep 5

# Start Chromium in kiosk mode
chromium-browser \\
    --kiosk \\
    --noerrdialogs \\
    --disable-translate \\
    --no-first-run \\
    --fast \\
    --fast-start \\
    --disable-infobars \\
    --disable-features=TranslateUI \\
    --disk-cache-size=524288000 \\
    --password-store=basic \\
    --disable-pinch \\
    --overscroll-history-navigation=0 \\
    --disable-session-crashed-bubble \\
    --start-fullscreen \\
    "$FRAME_URL"
KIOSK
chmod +x "$KIOSK_SCRIPT"
chown "$KIOSK_USER:$KIOSK_USER" "$KIOSK_SCRIPT"

# --- 5. Create systemd service for auto-start ---
echo ">>> Creating systemd service..."
cat > /etc/systemd/system/familyframe-kiosk.service << SERVICE
[Unit]
Description=FamilyFrame Kiosk
Wants=graphical.target
After=graphical.target

[Service]
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$KIOSK_USER/.Xauthority
Type=simple
User=$KIOSK_USER
ExecStartPre=/usr/bin/xinit /bin/true -- :0 -nolisten tcp
ExecStart=/home/$KIOSK_USER/kiosk.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical.target
SERVICE

# --- 6. Auto-login and auto-start X ---
echo ">>> Configuring auto-login..."
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf << AUTOLOGIN
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $KIOSK_USER --noclear %I \$TERM
AUTOLOGIN

# Add xinit to .bashrc for auto-start (only on tty1)
BASHRC="/home/$KIOSK_USER/.bashrc"
if ! grep -q "familyframe" "$BASHRC" 2>/dev/null; then
    cat >> "$BASHRC" << 'BASHRC_ENTRY'

# FamilyFrame: auto-start kiosk on tty1
if [ "$(tty)" = "/dev/tty1" ]; then
    exec startx /home/$USER/kiosk.sh -- -nocursor
fi
BASHRC_ENTRY
fi

# --- 7. Optimize for 24/7 operation ---
echo ">>> Optimizing for continuous operation..."

# Reduce SD card writes
cat >> /etc/fstab << 'FSTAB' || true
tmpfs /tmp tmpfs defaults,noatime,nosuid,size=100m 0 0
tmpfs /var/log tmpfs defaults,noatime,nosuid,mode=0755,size=50m 0 0
FSTAB

# Enable hardware watchdog (auto-reboot if system hangs)
if ! grep -q "watchdog" /etc/systemd/system.conf; then
    echo "RuntimeWatchdogSec=15" >> /etc/systemd/system.conf
fi

# --- 8. Enable the service ---
echo ">>> Enabling kiosk service..."
systemctl daemon-reload
systemctl enable familyframe-kiosk.service

echo ""
echo "=== Setup complete! ==="
echo ""
echo "The Raspberry Pi will boot directly into FamilyFrame kiosk mode."
echo "URL: $FRAME_URL"
echo ""
echo "To change the URL later, edit: $KIOSK_SCRIPT"
echo "To temporarily exit kiosk: press Alt+F4 or SSH in"
echo ""
echo "Reboot now to start: sudo reboot"
