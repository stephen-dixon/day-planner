#!/usr/bin/env bash
set -euo pipefail

# Readable Raspberry Pi install helper for a private dayplanner deployment.
# Run from the repository root on the Pi:
#   sudo deployment/install_pi.sh

APP_USER="${APP_USER:-dayplanner}"
APP_ROOT="${APP_ROOT:-/opt/dayplanner}"
DATA_DIR="${DATA_DIR:-/var/lib/dayplanner}"
CONFIG_DIR="${CONFIG_DIR:-/etc/dayplanner}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/dayplanner}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo $0" >&2
  exit 1
fi

echo "Creating app user and directories..."
id -u "${APP_USER}" >/dev/null 2>&1 || useradd --system --home "${APP_ROOT}" --shell /usr/sbin/nologin "${APP_USER}"
mkdir -p "${APP_ROOT}" "${DATA_DIR}/catalogs" "${CONFIG_DIR}" "${BACKUP_DIR}"

echo "Copying application files..."
rsync -a --delete --exclude ".git" --exclude "node_modules" --exclude ".venv" day-planner/backend/ "${APP_ROOT}/backend/"
rsync -a --delete --exclude "node_modules" day-planner/frontend/ "${APP_ROOT}/frontend/"
rsync -a deployment/ "${APP_ROOT}/deployment/"

if [[ ! -f "${CONFIG_DIR}/backend.env" ]]; then
  echo "Creating ${CONFIG_DIR}/backend.env from example. Edit secrets before exposing the app."
  cp day-planner/backend/.env.example "${CONFIG_DIR}/backend.env"
  sed -i "s#^DATABASE_URL=.*#DATABASE_URL=sqlite:////var/lib/dayplanner/dayplanner.db#" "${CONFIG_DIR}/backend.env"
  sed -i "s#^CATALOG_DIR=.*#CATALOG_DIR=/var/lib/dayplanner/catalogs#" "${CONFIG_DIR}/backend.env"
  chmod 600 "${CONFIG_DIR}/backend.env"
fi

echo "Installing backend Python environment..."
python3 -m venv "${APP_ROOT}/backend/.venv"
"${APP_ROOT}/backend/.venv/bin/pip" install --upgrade pip
"${APP_ROOT}/backend/.venv/bin/pip" install -r "${APP_ROOT}/backend/requirements.txt"

echo "Building static frontend..."
cd "${APP_ROOT}/frontend"
npm ci
npm run build

echo "Fixing ownership and permissions..."
chown -R "${APP_USER}:${APP_USER}" "${APP_ROOT}" "${DATA_DIR}" "${BACKUP_DIR}"
chown root:"${APP_USER}" "${CONFIG_DIR}/backend.env"
chmod 640 "${CONFIG_DIR}/backend.env"
chmod 700 "${DATA_DIR}" "${DATA_DIR}/catalogs"

echo "Installing systemd service..."
cp "${APP_ROOT}/deployment/dayplanner-backend.service.example" /etc/systemd/system/dayplanner-backend.service
systemctl daemon-reload
systemctl enable --now dayplanner-backend.service

cat <<EOF

Backend service installed.

Next steps:
1. Install Caddy if needed: sudo apt install caddy
2. Copy deployment/Caddyfile.example to /etc/caddy/Caddyfile and adjust root/port if needed.
3. Reload Caddy: sudo systemctl reload caddy
4. Access privately via Tailscale or LAN: http://<pi-tailnet-name>:8080

Check logs:
  journalctl -u dayplanner-backend -f

EOF
