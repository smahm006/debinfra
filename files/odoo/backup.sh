#!/usr/bin/env bash
# Odoo backup: pg_dump + filestore tarball, keeps 7 days of snapshots.
# Requires BACKUP_DIR. Run as the user with kubectl access.
set -euo pipefail

: "${BACKUP_DIR:?set BACKUP_DIR}"
STAMP=$(date +"%Y-%m-%d_%H-%M-%S")
DEST="$BACKUP_DIR/$STAMP"
mkdir -p "$DEST"

DB_USER=$(kubectl get secret odoo-secrets -n odoo -o jsonpath='{.data.ODOO_DB_USER}' | base64 -d)

echo "==> dumping database"
kubectl exec -n odoo deploy/odoo-db -- pg_dump -U "$DB_USER" -d odoo > "$DEST/odoo.sql"

echo "==> archiving filestore"
tar -czf "$DEST/filestore.tar.gz" -C /opt/odoo/data filestore 2>/dev/null || echo "(no filestore yet)"

echo "==> pruning snapshots older than 7 days"
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec /bin/rm -rf {} +

echo "==> done: $DEST"
