#!/usr/bin/env bash
# Pings every running service and prints a PASS/FAIL table. Use after `pnpm dev` (or compose up)
# to confirm Postgres, Redis, FastAPI, and the embedding/LLM gateways are wired correctly. Reads
# nothing secret; safe to run anytime. Exit code is non-zero if any required service is down.
set -u

API="${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000}"
PG_HOST="${PGHOST:-localhost}"
PG_PORT="${PGPORT:-5432}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

pass=0
fail=0
row() { printf "  %-28s %s\n" "$1" "$2"; }

echo "TAU 3346 — service healthcheck"
echo "--------------------------------------------"

# Postgres
if (exec 3<>"/dev/tcp/${PG_HOST}/${PG_PORT}") 2>/dev/null; then
  row "Postgres (${PG_PORT})" "PASS"; pass=$((pass+1))
else
  row "Postgres (${PG_PORT})" "FAIL"; fail=$((fail+1))
fi

# Redis
if (exec 3<>"/dev/tcp/${REDIS_HOST}/${REDIS_PORT}") 2>/dev/null; then
  row "Redis (${REDIS_PORT})" "PASS"; pass=$((pass+1))
else
  row "Redis (${REDIS_PORT})" "FAIL"; fail=$((fail+1))
fi

# FastAPI /healthz — parse the four dependency states.
HEALTH="$(curl -fsS "${API}/healthz" 2>/dev/null || echo '')"
if [ -n "$HEALTH" ]; then
  row "FastAPI /healthz" "PASS"; pass=$((pass+1))
  for key in db redis embedding_service gateway; do
    state="$(printf '%s' "$HEALTH" | grep -o "\"${key}\":\"[a-z]*\"" | cut -d'"' -f4)"
    [ "$state" = "up" ] && { row "  └ ${key}" "up"; } || { row "  └ ${key}" "DOWN"; fail=$((fail+1)); }
  done
else
  row "FastAPI /healthz" "FAIL"; fail=$((fail+1))
fi

echo "--------------------------------------------"
echo "  PASS=${pass}  FAIL=${fail}"
[ "$fail" -eq 0 ] || exit 1
