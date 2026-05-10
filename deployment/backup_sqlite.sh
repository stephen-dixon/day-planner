#!/usr/bin/env bash
set -euo pipefail

SOURCE_DB="${SOURCE_DB:-/var/lib/dayplanner/dayplanner.db}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/dayplanner}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

timestamp="$(date +%Y-%m-%d-%H%M%S)"
destination="${BACKUP_DIR}/dayplanner-${timestamp}.db"

if [[ ! -f "${SOURCE_DB}" ]]; then
  echo "Source database not found: ${SOURCE_DB}" >&2
  exit 1
fi

mkdir -p "${BACKUP_DIR}"
sqlite3 "${SOURCE_DB}" ".backup '${destination}'"
chmod 600 "${destination}"

find "${BACKUP_DIR}" -name "dayplanner-*.db" -type f -mtime +"${RETENTION_DAYS}" -delete

echo "Wrote backup: ${destination}"
