#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
# Uses a ledger: reruns skip applied files, changed checksums fail explicitly.
docker compose exec -T db psql -U postgres -d antutor -v ON_ERROR_STOP=1 <<'SQL'
CREATE SCHEMA IF NOT EXISTS antutor_migrations;
CREATE TABLE IF NOT EXISTS antutor_migrations.applied (version text PRIMARY KEY, checksum text NOT NULL);
SQL
for file in supabase/migrations/*.sql; do
  version=$(basename "$file")
  checksum=$(sha256sum "$file" | cut -d ' ' -f 1)
  previous=$(docker compose exec -T db psql -U postgres -d antutor -At -c "SELECT checksum FROM antutor_migrations.applied WHERE version='$version'")
  if [[ -n "$previous" ]]; then
    [[ "$previous" == "$checksum" ]] || { echo "Changed applied migration: $version" >&2; exit 1; }
    continue
  fi
  { echo 'BEGIN;'; cat "$file"; echo "INSERT INTO antutor_migrations.applied VALUES ('$version', '$checksum');"; echo 'COMMIT;'; } |
    docker compose exec -T db psql -U postgres -d antutor -v ON_ERROR_STOP=1
 done
