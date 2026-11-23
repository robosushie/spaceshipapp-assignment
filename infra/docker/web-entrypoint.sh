#!/bin/sh
set -eu

if [ -z "${PORT:-}" ]; then
  echo "PORT is required" >&2
  exit 1
fi

if [ -z "${API_UPSTREAM:-}" ]; then
  echo "API_UPSTREAM is required" >&2
  exit 1
fi

envsubst '${PORT} ${API_UPSTREAM}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
