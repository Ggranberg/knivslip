#!/bin/bash
# Knivslip AB — Backup-script for JSON-datafiler
# Kor manuellt eller via cron: ./scripts/backup.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/data"
BACKUP_DIR="$DATA_DIR/backups"

TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"

# Skapa backup-katalog
mkdir -p "$BACKUP_PATH"

# Kopiera alla JSON-filer
for file in "$DATA_DIR"/*.json; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_PATH/"
    fi
done

echo "Backup skapad: $BACKUP_PATH"

# Behall bara de 30 senaste backuparna
cd "$BACKUP_DIR" || exit 1
BACKUP_COUNT=$(ls -d */ 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 30 ]; then
    ls -d */ | sort | head -n $(($BACKUP_COUNT - 30)) | xargs rm -rf
    echo "Raderade $(($BACKUP_COUNT - 30)) gamla backupar"
fi

echo "Klart! $BACKUP_COUNT backupar totalt."
