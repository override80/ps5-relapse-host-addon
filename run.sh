#!/bin/bash
# PS5 Relapse exploit host entrypoint.
# Serves /app/relapse on host port 8082 (host_network addon).
# The nginx addon (core_nginx_proxy) terminates TLS for manuals.playstation.net
# and proxies here; a self-signed cert is generated only for direct/local use.
set -euo pipefail

cd /app/relapse

if [ ! -f cert.pem ] || [ ! -f key.pem ]; then
  openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes \
    -subj "/CN=manuals.playstation.net" \
    -addext "subjectAltName=DNS:manuals.playstation.net"
fi

export HTTP_PORT="${HTTP_PORT:-8082}"
export HTTPS_PORT="${HTTPS_PORT:-8444}"

echo "PS5 exploit host: http://0.0.0.0:${HTTP_PORT} https://0.0.0.0:${HTTPS_PORT}"
exec python3 serve_tls.py
