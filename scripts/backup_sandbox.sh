#!/usr/bin/env bash
# GHBS Trading web — sandbox backup (Release Train F).
# Backs up app data (test ledger DB, alert audit file, .env) into a
# timestamped tarball under ./backups/. The .env is included so the VPS
# runtime can be restored, but backups/ is gitignored — NEVER commit backups.
set -euo pipefail
APP_DIR="${1:-$(pwd)}"
BACKUP_DIR="${APP_DIR}/backups"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARBALL="${BACKUP_DIR}/ghbs-sandbox-backup-${STAMP}.tar.gz"

mkdir -p "${BACKUP_DIR}"

INCLUDE=()
for f in tasi_ledger_test.db alert_attempts_audit.jsonl .env; do
  [ -f "${APP_DIR}/${f}" ] && INCLUDE+=("${f}")
done

if [ "${#INCLUDE[@]}" -eq 0 ]; then
  echo "Nothing to back up (no data files found in ${APP_DIR})."
  exit 1
fi

tar -czf "${TARBALL}" -C "${APP_DIR}" "${INCLUDE[@]}"
chmod 600 "${TARBALL}"
echo "Backup written: ${TARBALL}"
echo "Contents: ${INCLUDE[*]}"
echo "Reminder: backups/ is gitignored and must stay on the VPS only."
