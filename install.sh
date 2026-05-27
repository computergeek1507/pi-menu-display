#!/bin/bash
set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="$(whoami)"

echo "=== Pi Menu Display - Installation ==="
echo "Install directory: ${INSTALL_DIR}"
echo "User: ${USER_NAME}"
echo ""

# 1. System dependencies
echo "[1/7] Installing system packages..."
sudo apt update -qq
sudo apt install -y python3-venv python3-pip samba chromium-browser

# 2. Switch to X11 (required for reliable dual-display Chromium placement)
echo "[2/7] Configuring X11 display server..."
if command -v raspi-config &>/dev/null; then
    sudo raspi-config nonint do_wayland W1
    echo "  Switched to X11 (reboot required)"
else
    echo "  raspi-config not found, skipping (ensure X11 is configured manually)"
fi

# 3. Python virtual environment
echo "[3/7] Setting up Python environment..."
cd "${INSTALL_DIR}"
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

# 4. Image directories
echo "[4/7] Creating image directories..."
mkdir -p images/screen1 images/screen2 images/specials/screen1 images/specials/screen2

# 5. Samba share
echo "[5/7] Configuring Samba share..."
SMB_CONF="/etc/samba/smb.conf"
if ! grep -q "\[MenuImages\]" "${SMB_CONF}" 2>/dev/null; then
    # Update the path in the config to match the actual install directory
    sed "s|/home/pi/pi-menu-display|${INSTALL_DIR}|g" smb/pi-menu-share.conf | \
        sed "s/force user = pi/force user = ${USER_NAME}/g" | \
        sed "s/force group = pi/force group = ${USER_NAME}/g" | \
        sudo tee -a "${SMB_CONF}" > /dev/null
    echo "  Added MenuImages share to ${SMB_CONF}"
else
    echo "  MenuImages share already configured"
fi
sudo systemctl enable --now smbd

# 6. Systemd services
echo "[6/7] Installing systemd services..."

# Update service files with actual paths and user
for svc in systemd/*.service; do
    svc_name="$(basename "${svc}")"
    sed \
        -e "s|/home/pi/pi-menu-display|${INSTALL_DIR}|g" \
        -e "s/User=pi/User=${USER_NAME}/g" \
        "${svc}" | sudo tee "/etc/systemd/system/${svc_name}" > /dev/null
done

sudo systemctl daemon-reload
sudo systemctl enable pi-menu-server pi-menu-screen1 pi-menu-screen2

# Make launch script executable
chmod +x scripts/launch-display.sh

# 7. Disable screen blanking
echo "[7/7] Disabling screen blanking..."
if command -v raspi-config &>/dev/null; then
    sudo raspi-config nonint do_blanking 1
    echo "  Screen blanking disabled"
fi

# Set up dual display in .xprofile
XPROFILE="${HOME}/.xprofile"
if ! grep -q "Pi Menu Display" "${XPROFILE}" 2>/dev/null; then
    cat >> "${XPROFILE}" << 'XEOF'

# Pi Menu Display - Dual monitor setup
xrandr --output HDMI-1 --mode 1920x1080 --pos 0x0 --primary 2>/dev/null || true
xrandr --output HDMI-2 --mode 1920x1080 --pos 1920x0 2>/dev/null || true
xrandr --output HDMI-A-1 --mode 1920x1080 --pos 0x0 --primary 2>/dev/null || true
xrandr --output HDMI-A-2 --mode 1920x1080 --pos 1920x0 2>/dev/null || true
XEOF
    echo "  Added dual-display xrandr config to ${XPROFILE}"
fi

echo ""
echo "=== Installation Complete ==="
IP_ADDR="$(hostname -I | awk '{print $1}')"
echo ""
echo "  Admin UI:   http://${IP_ADDR}:8080/admin"
echo "  Screen 1:   http://${IP_ADDR}:8080/display/screen1"
echo "  Screen 2:   http://${IP_ADDR}:8080/display/screen2"
echo "  SMB Share:  \\\\${IP_ADDR}\\MenuImages"
echo ""
echo "  A REBOOT IS REQUIRED to apply X11 and display changes."
echo "  Run:  sudo reboot"
echo ""
