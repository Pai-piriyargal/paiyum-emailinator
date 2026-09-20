#!/usr/bin/env python3
"""
loader.py — Dataset loader supporting local directory and HTTP server endpoints.
"""
import json
import os
import urllib.request
from pathlib import Path


class Inbox:
    def __init__(self, source):
        self.source = str(source).rstrip("/")
        self.is_http = self.source.startswith("http://") or self.source.startswith("https://")

    def emails(self):
        """Return list of email dicts."""
        if self.is_http:
            return self._get_json("/emails")
        inbox_dir = Path(self.source) / "inbox"
        if not inbox_dir.exists():
            inbox_dir = Path(self.source)
        return [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted(inbox_dir.glob("email_*.json"))]

    def __iter__(self):
        return iter(self.emails())

    def get(self, email_id):
        if self.is_http:
            return self._get_json(f"/emails/{email_id}")
        p = Path(self.source) / "inbox" / f"{email_id}.json"
        if not p.exists():
            p = Path(self.source) / f"{email_id}.json"
        return json.loads(p.read_text(encoding="utf-8"))

    def read_bytes(self, att_path):
        if self.is_http:
            return self._get_bytes("/" + att_path.lstrip("/"))
        p = Path(self.source) / att_path
        if not p.exists():
            # Try root relative
            p = Path(att_path)
        return p.read_bytes()

    def read_text(self, att_path, encoding="utf-8"):
        return self.read_bytes(att_path).decode(encoding, errors="replace")

    def submit(self, submission):
        if not self.is_http:
            raise RuntimeError("submit() requires HTTP source; run docker server")
        data = json.dumps(submission).encode()
        req = urllib.request.Request(self.source + "/submit", data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())

    def _get_json(self, path):
        with urllib.request.urlopen(self.source + path) as r:
            return json.loads(r.read())

    def _get_bytes(self, path):
        with urllib.request.urlopen(self.source + path) as r:
            return r.read()
