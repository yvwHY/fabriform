"""
Fabri-Form · Cloud API Proxy (Render deployment)
================================================
Forwards browser requests from the Fabri-Form interface to the
Anthropic API. Reads the API key from an environment variable so
the source code can be safely committed to a public repository.

Local use:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python3 proxy.py
    # → listens on 127.0.0.1:8787

Render use:
    Set ANTHROPIC_API_KEY in the Render environment-variables panel.
    Render injects a PORT variable; this script binds 0.0.0.0:$PORT.

Health check:
    GET /ping  →  {"ok": true, "service": "fabriform-proxy"}

Endpoint:
    POST /analyse   (raw Anthropic /v1/messages payload)
"""

import http.server
import json
import os
import socketserver
import urllib.request
import urllib.error

# ==========  CONFIG  =================================================
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT = int(os.environ.get("PORT", "8787"))
HOST = "0.0.0.0"  # listen on all interfaces (required by Render)
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
# =====================================================================


class ProxyHandler(http.server.BaseHTTPRequestHandler):

    def _send_cors(self):
        # Open CORS so any origin (GitHub Pages, file://) can call this proxy
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_GET(self):
        # Health-check endpoint used by the front-end status indicator
        if self.path == "/ping":
            self.send_response(200)
            self._send_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true, "service": "fabriform-proxy"}')
            return
        # Render's own health probe sometimes hits /
        if self.path == "/":
            self.send_response(200)
            self._send_cors()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Fabri-Form proxy is running. POST sketches to /analyse.")
            return
        self.send_response(404)
        self._send_cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/analyse":
            self.send_response(404)
            self._send_cors()
            self.end_headers()
            return

        if not ANTHROPIC_API_KEY:
            self._respond_json(500, {
                "error": "api_key_missing",
                "message": "ANTHROPIC_API_KEY env var not set on the server."
            })
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        req = urllib.request.Request(
            ANTHROPIC_URL,
            data=raw_body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
                status = resp.status
        except urllib.error.HTTPError as e:
            body = e.read()
            status = e.code
        except Exception as e:
            self._respond_json(502, {
                "error": "upstream_unreachable",
                "message": str(e),
            })
            return

        self.send_response(status)
        self._send_cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _respond_json(self, status, obj):
        payload = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self._send_cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        print("[proxy]", format % args)


def main():
    with socketserver.TCPServer((HOST, PORT), ProxyHandler) as httpd:
        print("=" * 60)
        print(f" Fabri-Form proxy running on {HOST}:{PORT}")
        print(f" Health check:  /ping")
        print(f" Analyse:       POST /analyse")
        if not ANTHROPIC_API_KEY:
            print(" !!  WARNING: ANTHROPIC_API_KEY not set — /analyse will fail.")
        print(" Press Ctrl+C to stop.")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[proxy] stopped.")


if __name__ == "__main__":
    main()
