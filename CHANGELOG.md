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

## 1.1.1
- Docs: name-agnostic docker exec command (container is app_<repo>_ps5_relapse_host).

## 1.2.0
- Added disc backup/load payloads to /app/tools: kstuff.elf v1.6.7, etaHEN-2.5B.bin,
  ps5-app-dumper_v2.10.elf; TOOLS.md gained a "Backup & load your own disc games" section.

## 1.3.0
- Added ftpsrv-ps5.elf (FTP :2121) and websrv-ps5.elf (HTTP :8084) to /app/tools.
- TOOLS.md: file transfer, moving backups / PS5 Pro / factory reset, other tools.

## 1.4.0
- Bundled all tools in /app/tools: webkit-autoloader-installer v0.8.4, pldmgr v0.6.3,
  ps5debug-NG v1.3.2, CheatRunner v0.18.1, ps5-backpork, klogsrv-ps5.
- TOOLS.md rewritten: per-tool instructions, exact backup folders (USB root for
  dumps/installs, /data/etaHen/games, /data/etaHen/pkgs), autoloader setup, pfSense
  update-block location.

## 1.5.0
- Added GUIDE.md (comprehensive day-to-day guide) to the image at /app/GUIDE.md.
