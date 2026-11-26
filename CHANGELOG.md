# Changelog

## 1.0.0
- Initial: Relapse-Exploit site (7.00-13.60 offsets + payloads) served on host
  port 8082/8444 via serve_tls.py (no-store headers, deep-path mapping for the
  User's Guide URL). Bundled tools: send_payload.py, shsrv-ps5.elf,
  elfldr-ps5-generic.elf, ps5-firmware-pin.

## 1.1.0
- Tools usable inside the container via docker exec: TOOLS.md added to the image
  (/app/TOOLS.md), netcat-openbsd installed, send_payload.py now defaults to
  PS5_HOST/PS5_PORT/PS5_PAYLOAD env vars (PS5_HOST defaults to 10.11.12.74).
