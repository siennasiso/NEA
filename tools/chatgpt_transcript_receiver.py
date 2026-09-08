"""Local-only receiver used to archive ChatGPT project transcripts.

Run this script, then submit a filename and transcript to http://127.0.0.1:8765.
Files are written only beneath chatgpt/conversations in this repository.
"""

from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs
import re


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = REPOSITORY_ROOT / "chatgpt" / "conversations"
SAFE_FILENAME = re.compile(r"[^a-z0-9._-]+")


class TranscriptHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._send_form("Ready")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        fields = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        raw_filename = fields.get("filename", ["conversation.md"])[0].lower()
        filename = SAFE_FILENAME.sub("-", raw_filename).strip("-.") or "conversation.md"
        if not filename.endswith(".md"):
            filename += ".md"
        transcript = fields.get("transcript", [""])[0]
        OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
        destination = OUTPUT_DIRECTORY / filename
        destination.write_text(transcript.rstrip() + "\n", encoding="utf-8")
        self._send_form(f"Saved {escape(filename)} ({len(transcript)} characters)")

    def _send_form(self, message: str) -> None:
        body = f"""<!doctype html>
<html><head><meta charset=\"utf-8\"><title>NEA transcript receiver</title></head>
<body><p id=\"status\">{message}</p>
<form method=\"post\">
<label>Filename <input name=\"filename\" aria-label=\"Filename\"></label>
<label>Transcript <textarea name=\"transcript\" aria-label=\"Transcript\"></textarea></label>
<button type=\"submit\">Save transcript</button>
</form></body></html>""".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8765), TranscriptHandler).serve_forever()
