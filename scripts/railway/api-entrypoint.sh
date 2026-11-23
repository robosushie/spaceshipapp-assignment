#!/bin/sh
set -eu
port="${PORT:-8000}"
exec python -m uvicorn src.main:app --host 0.0.0.0 --port "$port"
