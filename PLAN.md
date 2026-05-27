# Pi Menu Display - Implementation Plan

## Context
Build a Raspberry Pi (4/5) app that displays menu images on two HDMI outputs for a restaurant. Staff can update menus by uploading images via a web UI or dragging files into a network share. Monthly special images (named by month) periodically fade in as overlays, per-screen.

## Architecture: Chromium Kiosk + FastAPI

Two fullscreen Chromium windows (one per HDMI) each load a page from a local FastAPI server. CSS handles fade transitions. The same server provides the admin upload UI. A filesystem watcher pushes refresh events via SSE when images change (from web upload or SMB).

**Why this approach:**
- CSS transitions handle fades natively — no custom rendering code
- Single Python process serves displays + admin UI + live refresh
- Chromium kiosk is the most proven dual-display approach on Pi (X11, `--window-position` per monitor)
- Debuggable: open the same URLs from any device on the network

## Directory Structure

```
pi-menu-display/
├── install.sh                     # One-shot setup (X11, Samba, systemd, venv)
├── config.yaml                    # Timing, paths, overlay settings
├── requirements.txt               # FastAPI, uvicorn, watchdog, Pillow, etc.
├── server/
│   ├── app.py                     # FastAPI entry point, lifespan, routes
│   ├── routes/
│   │   ├── display.py             # Display page + specials API
│   │   ├── admin.py               # Upload/manage web UI
│   │   └── events.py              # SSE endpoint for live refresh
│   └── services/
│       ├── config.py              # Loads config.yaml
│       └── watcher.py             # watchdog filesystem observer + debounce
├── templates/
│   ├── display.html               # Fullscreen image + overlay container
│   └── admin.html                 # Upload/management UI
├── static/
│   ├── css/
│   │   ├── display.css            # Fullscreen layout, fade animations
│   │   └── admin.css
│   └── js/
│       ├── display.js             # SSE listener, overlay timer, auto-refresh
│       └── admin.js               # Upload forms, drag-drop, preview
├── images/                        # Runtime storage (also the SMB share root)
│   ├── screen1/                   # HDMI-1 images (Shack Menu)
│   ├── screen2/                   # HDMI-2 images (Tea Menu)
│   └── specials/                  # Monthly specials, per-screen
│       ├── screen1/               # e.g., may.jpg for Shack Menu
│       └── screen2/               # e.g., may.jpg for Tea Menu
├── scripts/
│   ├── launch-display.sh          # Launches Chromium kiosk on a specific monitor
│   └── health-check.sh            # Checks all services are running
├── systemd/
│   ├── pi-menu-server.service     # FastAPI server
│   ├── pi-menu-screen1.service    # Chromium on HDMI-1
│   └── pi-menu-screen2.service    # Chromium on HDMI-2
└── smb/
    └── pi-menu-share.conf         # Samba config snippet
```

## Key Design Decisions

### Display: X11, not Wayland
Pi OS Bookworm defaults to Wayland, but dual-display Chromium window placement is unreliable under Wayland/labwc. The install script switches to X11 (`raspi-config nonint do_wayland W1`), which has proven `--window-position` support.

### Dual monitors
`xrandr` configures two outputs side-by-side. Two Chromium instances launch with `--window-position=0,0` and `--window-position=1920,0`, each with a separate `--user-data-dir` to prevent window conflicts.

### Monthly specials overlay (per-screen)
- Server endpoint `/api/specials/{screen_id}/current` returns the image for the current month per screen
- Looks for `january.*`, `february.*`, etc. case-insensitively in `images/specials/{screen_id}/`
- JavaScript timer shows the overlay every N minutes (configurable, default 15)
- CSS `opacity` transition handles fade in/out (configurable duration, default 2s)
- Overlay stays visible for a configurable duration (default 30s), then fades out
- If no image exists for the current month, the overlay never triggers

### Live refresh via SSE
- `watchdog` library monitors the `images/` directory tree
- On file changes, events are broadcast to all connected SSE subscribers
- Debouncing (2s cooldown) handles SMB's multi-event writes
- Browser reloads the image with a cache-busting param on refresh

### SMB share
- Samba exposes `images/` as `\\<pi-ip>\MenuImages` with guest access (no password, appropriate for restaurant LAN)
- `force user = pi` avoids permission issues
- Folders visible: `screen1/`, `screen2/`, `specials/screen1/`, `specials/screen2/`

### Config (`config.yaml`)
- Screen names (Shack Menu, Tea Menu), image directories, rotation interval (0 = static, >0 = slideshow)
- Specials: interval (minutes), display duration (seconds), fade duration, opacity
- Upload limits and allowed extensions
- Server host/port

## Python Dependencies
fastapi, uvicorn[standard], sse-starlette, python-multipart, jinja2, pyyaml, watchdog, pillow

## Deployment
1. Copy `pi-menu-display/` to `/home/pi/pi-menu-display` on the Pi
2. Run `chmod +x install.sh scripts/*.sh && ./install.sh`
3. Reboot (`sudo reboot`) to switch from Wayland to X11
4. Both screens come up automatically showing menus

## Verification
1. Run the FastAPI server locally, open `/display/screen1` and `/display/screen2` in browser tabs
2. Upload an image via `/admin`, confirm display updates without page reload
3. Drop a file into `images/screen1/` on disk, confirm display picks it up
4. Place a file named for the current month in `images/specials/screen1/`, confirm overlay fades in on schedule
5. On the Pi: run `install.sh`, reboot, confirm both screens show menus automatically
6. From another machine: access the SMB share, drop in a new image, confirm display updates
