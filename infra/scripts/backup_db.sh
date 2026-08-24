#!/usr/bin/env bash
# Automated Postgres Database Backup Script
set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_NAME="${POSTGRES_DB:-devops_risk_db}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${POSTGRES_HOST:-postgres}"

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/riskline_backup_${TIMESTAMP}.sql.gz"

echo "[INFO] Starting Postgres database backup for $DB_NAME at $(date)..."
PGPASSWORD="${POSTGRES_PASSWORD:-postgres_prod_secret}" pg_dump -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

echo "[SUCCESS] Database backup saved to $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Keep last 14 daily backups
find "$BACKUP_DIR" -type f -name "riskline_backup_*.sql.gz" -mtime +14 -delete
echo "[INFO] Cleaned up backups older than 14 days."
