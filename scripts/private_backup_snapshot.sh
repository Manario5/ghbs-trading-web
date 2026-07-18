#!/bin/bash

echo "=========================================================="
echo " GHBS Private Backup Snapshot Helper (Phase 6R) "
echo "=========================================================="

PROJECT_DIR=$(pwd)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups/private_ops/$TIMESTAMP"

mkdir -p "$BACKUP_DIR"

echo "Creating conservative backup snapshot at: $BACKUP_DIR"

if [ -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env" "$BACKUP_DIR/.env"
    echo "Copied: .env"
fi

if [ -f "$PROJECT_DIR/tasi_ledger_test.db" ]; then
    cp "$PROJECT_DIR/tasi_ledger_test.db" "$BACKUP_DIR/tasi_ledger_test.db"
    echo "Copied: tasi_ledger_test.db"
fi

if [ -d "$PROJECT_DIR/deploy" ]; then
    cp -r "$PROJECT_DIR/deploy" "$BACKUP_DIR/deploy"
    echo "Copied: deploy/"
fi

if [ -d "$PROJECT_DIR/scripts" ]; then
    cp -r "$PROJECT_DIR/scripts" "$BACKUP_DIR/scripts"
    echo "Copied: scripts/"
fi

mkdir -p "$BACKUP_DIR/docs"
if [ -f "$PROJECT_DIR/docs/VPS_DEPLOYMENT_RUNBOOK.md" ]; then
    cp "$PROJECT_DIR/docs/VPS_DEPLOYMENT_RUNBOOK.md" "$BACKUP_DIR/docs/"
    echo "Copied: VPS_DEPLOYMENT_RUNBOOK.md"
fi
if [ -f "$PROJECT_DIR/docs/PHASE_6Q_PRIVATE_TAILSCALE_ACCESS_REPORT.md" ]; then
    cp "$PROJECT_DIR/docs/PHASE_6Q_PRIVATE_TAILSCALE_ACCESS_REPORT.md" "$BACKUP_DIR/docs/"
    echo "Copied: PHASE_6Q_PRIVATE_TAILSCALE_ACCESS_REPORT.md"
fi
if [ -f "$PROJECT_DIR/docs/PHASE_6R_PRIVATE_ACCESS_HARDENING_REPORT.md" ]; then
    cp "$PROJECT_DIR/docs/PHASE_6R_PRIVATE_ACCESS_HARDENING_REPORT.md" "$BACKUP_DIR/docs/"
    echo "Copied: PHASE_6R_PRIVATE_ACCESS_HARDENING_REPORT.md"
fi

echo ""
echo "Backup snapshot successfully completed at:"
echo "$(realpath "$BACKUP_DIR")"
echo "=========================================================="
exit 0
