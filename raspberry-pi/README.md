# FamilyFrame - Raspberry Pi Kiosk Setup

## Hardware

- Raspberry Pi 4 (4 GB) or Raspberry Pi 5
- Official 7" touchscreen or any HDMI display
- 16 GB+ microSD card
- Official power supply (5V/3A USB-C)

## Installation

1. Flash **Raspberry Pi OS (Bookworm, 64-bit)** to the SD card using Raspberry Pi Imager
2. Enable SSH and configure WiFi during flashing
3. Boot the Pi and SSH in: `ssh pi@raspberrypi.local`
4. Clone the repo and run the setup script:

```bash
git clone https://github.com/JanLahmann/Remote-Picture-Frame.git
cd Remote-Picture-Frame/raspberry-pi
sudo ./setup.sh https://your-familyframe-url.example.com
sudo reboot
```

## Maintenance

- **Change URL**: Edit `/home/pi/kiosk.sh`, then `sudo systemctl restart familyframe-kiosk`
- **Exit kiosk**: Press `Alt+F4` or SSH in
- **View logs**: `journalctl -u familyframe-kiosk -f`
- **Restart**: `sudo systemctl restart familyframe-kiosk`
- **Disable kiosk**: `sudo systemctl disable familyframe-kiosk`
