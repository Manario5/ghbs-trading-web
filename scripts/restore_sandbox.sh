#!/usr/bin/env bash
# GHBS Trading web — sandbox restore (Release Train F).
# Restores a tarball created by backup_sandbox.sh into the app directory.
# Refuses to overwrite existing files unless --force is passed.
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <backup-tarball> [app-dir] [--force]"
  exit 1
fi

TARBALL="$1"
APP_DIR="${2:-$(pwd)}"
FORCE="${3:-}"

[ -f "${TARBALL}" ] || { echo "Backup not found: ${TARBALL}"; exit 1; }

if [ "${FORCE}" != "--force" ]; then
  for f in $(tar -tzf "${TARBALL}"); do
    if [ -f "${APP_DIR}/${f}" ]; then
      echo "Refusing to overwrite existing ${APP_DIR}/${f} (pass --force as 3rd arg to override)."
      exit 1
    fi
  done
fi

tar -xzf "${TARBALL}" -C "${APP_DIR}"
echo "Restored $(tar -tzf "${TARBALL}" | tr '\n' ' ') into ${APP_DIR}"
echo "Restart the backend service, then verify: GET /api/system/safety-matrix must return SAFE."
