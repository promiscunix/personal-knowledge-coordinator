#!/usr/bin/env bash
set -euo pipefail

BASE=${PKC_PG_SMOKE_DIR:-/tmp/pkc-postgres-smoke}
PORT=${PKC_PG_SMOKE_PORT:-55432}
rm -rf "$BASE"
install -d -m 0700 -o damajha -g users "$BASE"

runuser -u damajha -- initdb -D "$BASE/pgdata" >/tmp/pkc-initdb.log
runuser -u damajha -- pg_ctl -D "$BASE/pgdata" -o "-k $BASE -p $PORT" -l "$BASE/postgres.log" start >/tmp/pkc-pgctl.log
cleanup() {
  runuser -u damajha -- pg_ctl -D "$BASE/pgdata" stop >/dev/null 2>&1 || true
}
trap cleanup EXIT

runuser -u damajha -- createdb -h "$BASE" -p "$PORT" pkc
export PKC_DATABASE_URL="postgresql:///pkc?host=${BASE}&port=${PORT}&user=damajha"
python -m pkc.cli init-db
python -m pkc.cli capture "I don't like the UI for the Parts Advisor page in part-suite." --json
python -m pkc.cli inbox
