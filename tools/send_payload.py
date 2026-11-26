#!/usr/bin/env python3
"""Send a payload ELF to a PS5 ELF loader (elfldr) on port 9021.

Usage: send_payload.py [ps5-ip] [port] [payload.elf]
Defaults: PS5_HOST (or 10.11.12.74), PS5_PORT (or 9021),
          PS5_PAYLOAD (or /app/tools/shsrv-ps5.elf inside the addon).
"""
import os
import socket
import sys


def main():
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    host = args[0] if len(args) > 0 else os.environ.get("PS5_HOST", "10.11.12.74")
    port = int(args[1]) if len(args) > 1 else int(os.environ.get("PS5_PORT", "9021"))
    path = args[2] if len(args) > 2 else os.environ.get("PS5_PAYLOAD", "/app/tools/shsrv-ps5.elf")

    with open(path, "rb") as f:
        data = f.read()
    print(f"sending {len(data)} bytes from {path} to {host}:{port}")
    s = socket.create_connection((host, port), timeout=10)
    s.sendall(data)
    s.shutdown(socket.SHUT_WR)
    try:
        resp = s.recv(4096)
        print("loader response:", resp.decode(errors="replace") or "(empty)")
    except Exception as e:
        print("no response (payload may still have loaded):", e)
    s.close()


if __name__ == "__main__":
    main()
