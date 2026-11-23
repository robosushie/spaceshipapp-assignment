#!/bin/sh
set -eu
exec python - <<'PY'
import os
import socket

import uvicorn

port = int(os.environ.get("PORT", "8000"))
sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("::", port))
sock.setblocking(False)
config = uvicorn.Config("src.main:app", host="::", port=port)
uvicorn.Server(config).run(sockets=[sock])
PY
