#!/usr/bin/env bash
# Odoo restore from a snapshot made by backup.sh.
# Usage: restore.sh [snapshot-name]   (default: latest)
set -euo pipefail

: "${BACKUP_DIR:?set BACKUP_DIR}"
SNAPSHOT=${1:-$(ls -1 "$BACKUP_DIR" | sort | tail -1)}
SRC="$BACKUP_DIR/$SNAPSHOT"
[ -f "$SRC/odoo.sql" ] || { echo "no snapshot at $SRC"; exit 1; }

read -r -p "Restore $SNAPSHOT over the CURRENT odoo database? [y/N] " ans
[ "$ans" = "y" ] || exit 1

DB_USER=$(kubectl get secret odoo-secrets -n odoo -o jsonpath='{.data.ODOO_DB_USER}' | base64 -d)

echo "==> stopping odoo"
kubectl scale -n odoo deploy/odoo --replicas=0
kubectl wait -n odoo --for=delete pod -l app=odoo --timeout=120s || true

echo "==> restoring database"
kubectl exec -n odoo deploy/odoo-db -- dropdb -U "$DB_USER" --if-exists odoo
kubectl exec -n odoo deploy/odoo-db -- createdb -U "$DB_USER" odoo
kubectl exec -i -n odoo deploy/odoo-db -- psql -U "$DB_USER" -d odoo < "$SRC/odoo.sql"

echo "==> restoring filestore"
if [ -f "$SRC/filestore.tar.gz" ]; then
  /bin/rm -rf /opt/odoo/data/filestore
  tar -xzf "$SRC/filestore.tar.gz" -C /opt/odoo/data
fi

echo "==> starting odoo"
kubectl scale -n odoo deploy/odoo --replicas=1
echo "==> done"
