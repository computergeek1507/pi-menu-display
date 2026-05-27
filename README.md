# Pi Menu Display

Dual-HDMI menu display system for Raspberry Pi 4/5. Designed for restaurants — show different menu images on two screens, upload new menus over the network, and display monthly specials with fade-in overlays.

## Features

- **Dual HDMI output** — different image on each screen (e.g., Shack Menu on HDMI-1, Tea Menu on HDMI-2)
- **Web admin UI** — upload, preview, and delete menu images from any browser on the network
- **SMB file share** — drag and drop images from Windows/Mac/Linux via `\\<pi-ip>\MenuImages`
- **Monthly specials** — per-screen overlays that fade in periodically (name files `january.jpg`, `february.png`, etc.)
- **Live refresh** — displays update automatically when images are changed, no manual restart needed
- **Auto-start on boot** — systemd services with crash recovery

## Quick Start

### On the Raspberry Pi

```bash
git clone https://github.com/computergeek1507/pi-menu-display.git
cd pi-menu-display
chmod +x install.sh scripts/*.sh
./install.sh
sudo reboot
```

After reboot, both screens will display menus automatically.

### Access Points

| Service | URL |
|---------|-----|
| Admin UI | `http://<pi-ip>:8080/admin` |
| Screen 1 | `http://<pi-ip>:8080/display/screen1` |
| Screen 2 | `http://<pi-ip>:8080/display/screen2` |
| File Share | `\\<pi-ip>\MenuImages` |

## How It Works

A FastAPI server runs on the Pi and serves fullscreen display pages to two Chromium kiosk windows (one per HDMI output). The same server provides the admin web UI for uploading images. A filesystem watcher detects changes (from the web UI or SMB share) and pushes live updates to the displays via Server-Sent Events.

## File Structure

```
images/
├── screen1/              # Menu images for HDMI-1
├── screen2/              # Menu images for HDMI-2
└── specials/
    ├── screen1/          # Monthly specials for HDMI-1 (e.g., may.jpg)
    └── screen2/          # Monthly specials for HDMI-2
```

## Configuration

Edit `config.yaml` to customize:

```yaml
screens:
  screen1:
    name: "Shack Menu"
    rotation_interval: 0     # seconds between images (0 = static)
  screen2:
    name: "Tea Menu"
    rotation_interval: 0

specials:
  interval_minutes: 15       # how often the special fades in
  display_duration_seconds: 30
  fade_duration_seconds: 2
  max_opacity: 0.85
```

## Monthly Specials

Drop an image named for the current month into the specials folder for each screen:

- `images/specials/screen1/january.jpg`
- `images/specials/screen2/january.png`

The overlay fades in every 15 minutes (configurable), stays visible for 30 seconds, then fades out. If no image exists for the current month, nothing happens.

## Testing Locally (Windows/Mac/Linux)

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn server.app:app --host 127.0.0.1 --port 8888
```

Open `http://127.0.0.1:8888/admin` in your browser.

## Service Management

```bash
# Check status
sudo systemctl status pi-menu-server pi-menu-screen1 pi-menu-screen2

# Restart everything
sudo systemctl restart pi-menu-server

# View logs
journalctl -u pi-menu-server -f

# Health check
./scripts/health-check.sh
```

## Requirements

- Raspberry Pi 4 or 5
- Raspberry Pi OS (Bookworm)
- Two HDMI displays
- Network connection (for uploads)
