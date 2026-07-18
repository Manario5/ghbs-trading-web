#!/bin/bash

# Ensure we are root or using sudo
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root or with sudo"
  exit 1
fi

echo "Stopping mapped services..."
systemctl stop ghbs-backend.service ghbs-frontend.service || true

echo "Disabling daemon mounts cleanly..."
systemctl disable ghbs-backend.service ghbs-frontend.service || true

echo "Removing systemd unit structural boundaries..."
rm -f /etc/systemd/system/ghbs-backend.service
rm -f /etc/systemd/system/ghbs-frontend.service

# Cleanup daemon configurations
systemctl daemon-reload

echo "Systemd templates and service deployments uninstalled successfully cleanly. Native project files are untouched."
