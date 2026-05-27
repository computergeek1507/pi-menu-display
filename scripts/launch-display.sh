#!/bin/bash
SCREEN_ID="${1:-screen1}"
X_POS="${2:-0}"
PORT="${3:-8080}"
URL="http://localhost:${PORT}/display/${SCREEN_ID}"

# Wait for server to be ready
until curl -s "http://localhost:${PORT}/health" > /dev/null 2>&1; do
    sleep 1
done

# Clear stale profile locks
rm -f "/tmp/chromium-${SCREEN_ID}/SingletonLock"

exec chromium-browser \
    --kiosk \
    --window-position="${X_POS},0" \
    --user-data-dir="/tmp/chromium-${SCREEN_ID}" \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --noerrdialogs \
    --disable-translate \
    --no-first-run \
    --check-for-update-interval=31536000 \
    --disable-features=TranslateUI \
    --disable-component-update \
    --disable-dev-shm-usage \
    "${URL}"
