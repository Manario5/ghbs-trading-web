#!/bin/bash

# Required for start, stop, restart
COMMAND=$1

if [ -z "$COMMAND" ] || [[ ! "$COMMAND" =~ ^(start|stop|restart|status)$ ]]; then
    echo "Usage: sudo ./scripts/private_app_ops.sh [start|stop|restart|status]"
    exit 1
fi

PROJECT_DIR=$(pwd)

if [[ "$COMMAND" =~ ^(start|stop|restart)$ ]]; then
    if [ "$EUID" -ne 0 ]; then
        echo "ERROR: 'start', 'stop', and 'restart' must be run as root or with sudo."
        exit 1
    fi
fi

status_ops() {
    echo "--- STATUS ---"
    bash "$PROJECT_DIR/scripts/tailscale_private_status.sh"
}

start_ops() {
    echo "--- START ---"
    echo "Verifying .env Sandbox..."
    grep -q "^ALLOW_PRODUCTION_DB=false" "$PROJECT_DIR/.env" || { echo "ERROR: ALLOW_PRODUCTION_DB != false"; exit 1; }
    
    echo "Starting systemd services..."
    bash "$PROJECT_DIR/scripts/install_systemd_services.sh" --start
    
    echo "Installing/Refreshing Tailscale Private Proxy..."
    bash "$PROJECT_DIR/scripts/install_tailscale_private_proxy.sh"
    
    echo "Running Health Checks..."
    status_ops
}

stop_ops() {
    echo "--- STOP ---"
    echo "Uninstalling Tailscale Private Proxy..."
    bash "$PROJECT_DIR/scripts/uninstall_tailscale_private_proxy.sh" || true
    
    echo "Stopping systemd services..."
    systemctl stop ghbs-backend.service ghbs-frontend.service || true
    echo "Services stopped cleanly (Note: they remain enabled in systemd. Use exact uninstall scripts to fully drop)."
}

case "$COMMAND" in
    status)
        status_ops
        ;;
    start)
        start_ops
        ;;
    stop)
        stop_ops
        ;;
    restart)
        stop_ops
        sleep 2
        start_ops
        ;;
esac

exit 0
