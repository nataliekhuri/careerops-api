#!/bin/sh
# Container entrypoint: optionally apply database migrations, then start the API.
#
#   RUN_MIGRATIONS=true   run `alembic upgrade head` first (used on Render, where the
#                         paid-only pre-deploy command is not available on the free plan)
#   PORT                  port to listen on (set by most hosting platforms; default 8000)
#   FORWARDED_ALLOW_IPS   proxies trusted for X-Forwarded-* headers (default 127.0.0.1)
#
# If migrations fail, this script exits with an error BEFORE the API starts. On Render
# that fails the deploy and the previous version keeps serving traffic. Each migration
# runs in a single transaction, so a failure leaves the database unchanged.
set -eu

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "start.sh: applying database migrations..."
    if ! alembic upgrade head; then
        echo "start.sh: migrations FAILED - not starting the API." >&2
        exit 1
    fi
    echo "start.sh: migrations complete."
fi

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --proxy-headers \
    --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}"
