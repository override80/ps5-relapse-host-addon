import http.server
import os
import ssl
import threading
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTTP_PORT = int(os.environ.get("HTTP_PORT", "80"))
HTTPS_PORT = int(os.environ.get("HTTPS_PORT", "443"))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def translate_path(self, path):
        # The PS5 User's Guide requests deep paths like /document/en/ps5/...
        # Map any requested path onto the repo: try the full path, then strip
        # leading segments until a real file matches; fall back to index.html.
        path = urllib.parse.unquote(path.split("?", 1)[0].split("#", 1)[0])
        parts = [p for p in path.split("/") if p and p not in (".", "..")]
        for i in range(len(parts)):
            candidate = ROOT.joinpath(*parts[i:])
            if candidate.is_file():
                return str(candidate)
            if candidate.is_dir() and (candidate / "index.html").is_file():
                return str(candidate / "index.html")
        return str(ROOT / "index.html")


def serve(port, use_tls):
    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler)
    if use_tls:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(ROOT / "cert.pem", ROOT / "key.pem")
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    print(f"serving {'https' if use_tls else 'http'} on 0.0.0.0:{port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=serve, args=(HTTP_PORT, False), daemon=True).start()
    serve(HTTPS_PORT, True)
