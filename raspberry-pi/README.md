# FamilyFrame - Raspberry Pi USB Gadget Setup

The RPi emulates a USB drive that plugs into grandma's Samsung TV. The TV's
built-in media player shows photos as a slideshow. The RPi syncs photos from
OneDrive in the background over WiFi.

## Hardware

- **Raspberry Pi Zero 2 W** (~€20) — recommended (small, cheap, USB OTG built-in)
- 16 GB+ microSD card
- USB data cable (micro-USB to USB-A) — connects RPi to TV's USB port
- WiFi network at grandma's house

Alternative: RPi 4 also works (USB-C port supports OTG), but is overkill and
more expensive.

**Important:** The TV's USB port powers the RPi — no separate power supply needed.
Use the **USB** port on the Pi Zero 2 W (not the PWR port). On RPi 4, the USB-C
port serves both power and data.

## How it works

```
OneDrive ──WiFi──→ RPi Zero 2 W ──USB──→ Samsung TV
(family uploads)   (syncs photos,         (built-in USB
                    sorts by person,       media player,
                    emulates USB drive)    grandma's remote)
```

1. Family uploads photos to a shared OneDrive folder
2. RPi syncs photos every 5 minutes via rclone
3. Azure Face API identifies people in photos (optional)
4. Photos are sorted into person/event folders on a virtual USB drive
5. TV sees the USB drive and shows photos via its built-in media player

## Installation

1. Flash **Raspberry Pi OS Lite (Bookworm, 64-bit)** to the SD card using
   Raspberry Pi Imager. Enable SSH and configure WiFi during flashing.

2. Boot the Pi and SSH in:
   ```bash
   ssh pi@raspberrypi.local
   ```

3. Clone the repo and run the setup script:
   ```bash
   git clone https://github.com/JanLahmann/Remote-Picture-Frame.git
   cd Remote-Picture-Frame/raspberry-pi
   sudo ./setup.sh
   ```

4. Configure rclone for OneDrive:
   ```bash
   rclone config
   # Create a remote named "onedrive", type "onedrive"
   # Follow the OAuth flow (may need a browser on another machine)
   ```

5. Test the connection:
   ```bash
   rclone ls onedrive:/FamilyFrame/photos/ --max-depth 1
   ```

6. Copy the sync script:
   ```bash
   sudo cp sync.py /opt/familyframe/
   sudo chown pi:pi /opt/familyframe/sync.py
   ```

7. (Optional) Configure face recognition:
   ```bash
   sudo nano /etc/familyframe/config.env
   # Set AZURE_FACE_KEY and AZURE_FACE_ENDPOINT
   ```

8. Reboot and plug into TV:
   ```bash
   sudo reboot
   ```
   Connect the RPi's USB data port to the TV's USB port.

## Folder structure on TV

```
USB Drive (FAMILYFRAME)
├── Alle Fotos/              ← all photos
├── Anna/                    ← photos with Anna (face recognition)
├── Thomas/                  ← photos with Thomas
├── Urlaub Kroatien/         ← event folder (created by family in OneDrive)
```

## Maintenance

| Task | Command |
|------|---------|
| View sync logs | `cat /var/log/familyframe/sync.log` |
| Manual sync | `sudo systemctl start familyframe-sync` |
| USB gadget status | `journalctl -u familyframe-usb` |
| Take drive back for writing | `sudo /opt/familyframe/usb-gadget-stop.sh` |
| Re-expose drive to TV | `sudo /opt/familyframe/usb-gadget-start.sh` |
| Change sync interval | `sudo systemctl edit familyframe-sync.timer` |
| Edit config | `sudo nano /etc/familyframe/config.env` |
| Restart sync timer | `sudo systemctl restart familyframe-sync.timer` |

## Configuration

Edit `/etc/familyframe/config.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `RCLONE_REMOTE` | `onedrive` | rclone remote name |
| `ONEDRIVE_FOLDER` | `/FamilyFrame/photos` | Folder to sync from |
| `AZURE_FACE_KEY` | (empty) | Azure Face API key (optional) |
| `AZURE_FACE_ENDPOINT` | (empty) | Azure Face API endpoint (optional) |
| `MAX_PHOTO_DIMENSION` | `1920` | Resize photos to this max dimension (0 = disabled) |

## Troubleshooting

**TV doesn't see the USB drive:**
- Ensure you're using the correct USB port (data, not power-only)
- Check: `lsmod | grep g_mass_storage` — module should be loaded
- Try: `sudo /opt/familyframe/usb-gadget-stop.sh && sudo /opt/familyframe/usb-gadget-start.sh`

**Photos not syncing:**
- Check WiFi: `ping -c 1 google.com`
- Check rclone: `rclone ls onedrive:/FamilyFrame/photos/ --max-depth 1`
- Check logs: `cat /var/log/familyframe/sync.log`

**TV shows old photos:**
- Sync happens every 5 minutes. The TV may cache the USB contents — try
  navigating out and back into the USB source on the TV.

**RPi not powering on:**
- Some older TVs provide insufficient USB power for RPi Zero 2 W. Use an
  external power supply via the PWR port and a data-only cable for the USB port.
