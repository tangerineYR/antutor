#!/usr/bin/env bash
set -euo pipefail
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -v authenticator_password="$POSTGRES_PASSWORD" <<'SQL'
CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD :'authenticator_password';
GRANT anon, authenticated, service_role TO authenticator;
SQL
