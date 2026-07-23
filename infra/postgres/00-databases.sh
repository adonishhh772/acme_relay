#!/bin/bash
set -euo pipefail
# POSTGRES_USER is "relay" but POSTGRES_DB is "relay_ops" — psql defaults to a DB
# named like the user, which does not exist. Always target POSTGRES_DB (or postgres).
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${POSTGRES_DB:-postgres}" <<-EOSQL
    SELECT 'CREATE DATABASE glitchtip'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'glitchtip')\gexec
EOSQL
