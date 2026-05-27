#!/bin/bash
PORT="${1:-8080}"
ERRORS=0

check_service() {
    if systemctl is-active --quiet "$1"; then
        echo "  [OK] $1"
    else
        echo "  [FAIL] $1"
        ERRORS=$((ERRORS + 1))
    fi
}

echo "=== Pi Menu Display Health Check ==="
echo ""
echo "Services:"
check_service pi-menu-server
check_service pi-menu-screen1
check_service pi-menu-screen2

echo ""
echo "Server:"
if curl -s "http://localhost:${PORT}/health" | grep -q '"ok"'; then
    echo "  [OK] HTTP server responding on port ${PORT}"
else
    echo "  [FAIL] HTTP server not responding"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "Samba:"
if systemctl is-active --quiet smbd; then
    echo "  [OK] smbd running"
else
    echo "  [FAIL] smbd not running"
    ERRORS=$((ERRORS + 1))
fi

echo ""
if [ ${ERRORS} -eq 0 ]; then
    echo "All checks passed."
else
    echo "${ERRORS} check(s) failed."
    exit 1
fi
