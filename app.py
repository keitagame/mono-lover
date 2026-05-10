from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os

PORT = 8000
FILE_NAME = "post.txt"

class Handler(BaseHTTPRequestHandler):

    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_POST(self):
        if self.path != "/post":
            self.send_error(404)
            return

        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            message = data.get("message", "")

            with open(FILE_NAME, "a", encoding="utf-8") as f:
                f.write(message.replace("\n", " ") + "\n")

            self._set_headers()
            self.wfile.write(json.dumps({
                "status": "ok"
            }).encode("utf-8"))

        except Exception as e:
            self.send_error(500, str(e))

    def do_GET(self):
        if self.path != "/messages":
            self.send_error(404)
            return

        if not os.path.exists(FILE_NAME):
            open(FILE_NAME, "w", encoding="utf-8").close()

        with open(FILE_NAME, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]

        self._set_headers()

        self.wfile.write(json.dumps({
            "messages": lines
        }).encode("utf-8"))

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Server running on http://localhost:{PORT}")
    server.serve_forever()
