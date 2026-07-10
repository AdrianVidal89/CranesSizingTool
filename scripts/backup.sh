#!/bin/sh
# Runs inside the `backup` service (docker-compose.prod.yml, postgres:16-alpine
# image — has pg_dump). Dumps the whole database on a fixed interval, keeps
# BACKUP_RETENTION_DAYS days of dumps, deletes the rest. No cloud/paid backup
# service involved — dumps land on a bind-mounted host directory
# (./backups) so the VPS owner can copy them off with plain scp/rsync.
#
# Values already encrypted at rest by the application (see
# backend/app/infrastructure/db/encrypted_types.py) stay encrypted in the
# dump; nothing extra is done here for that.
set -eu

export PGUSER="$POSTGRES_USER"
export PGPASSWORD="$POSTGRES_PASSWORD"

RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
INTERVAL_SECONDS="${BACKUP_INTERVAL_SECONDS:-86400}"
BACKUP_DIR="/backups"

mkdir -p "$BACKUP_DIR"

echo "backup: starting, db=${POSTGRES_DB} retention=${RETENTION_DAYS}d interval=${INTERVAL_SECONDS}s"

while :; do
    timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
    dump_file="${BACKUP_DIR}/${POSTGRES_DB}_${timestamp}.dump"
    tmp_file="${dump_file}.tmp"

    if pg_dump -Fc -f "$tmp_file" "$POSTGRES_DB"; then
        mv "$tmp_file" "$dump_file"
        echo "backup: wrote ${dump_file}"
    else
        echo "backup: pg_dump failed, skipping this cycle" >&2
        rm -f "$tmp_file"
    fi

    find "$BACKUP_DIR" -name "${POSTGRES_DB}_*.dump" -mtime "+${RETENTION_DAYS}" -delete

    sleep "$INTERVAL_SECONDS" &
    wait $!
done
