#!/usr/bin/env python3
"""Send a payload ELF to a PS5 ELF loader (elfldr) on port 9021.

Usage: python3 send_payload.py <ps5-ip> <port> <payload.elf>
"""
import socket
import sys


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    host, port, path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
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
