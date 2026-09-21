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

    def submit(self, submission, token=None):
        if not self.is_http:
            raise RuntimeError("submit() requires HTTP source; run docker server")
        data = json.dumps(submission).encode()
        token = token or os.environ.get("JUDGE_TOKEN") or os.environ.get("SUBMISSION_TOKEN") or os.environ.get("API_KEY") or "change-me"
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["X-Judge-Token"] = token
            headers["X-API-Key"] = token
        req = urllib.request.Request(self.source + "/submit", data=data,
                                     headers=headers, method="POST")
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode("utf-8"))

    def _get_json(self, path):
        with urllib.request.urlopen(self.source + path) as r:
            return json.loads(r.read())

    def _get_bytes(self, path):
        with urllib.request.urlopen(self.source + path) as r:
            return r.read()


def post_submission(submission_path="submission.json", target_url="http://localhost:8080/submit", token=None):
    """
    Posts submission JSON output payload to the evaluation HTTP server endpoint.
    Includes Authorization (Bearer), X-Judge-Token, and X-API-Key authentication headers.
    """
    path = Path(submission_path)
    if not path.exists():
        alt_path = Path("shipping-verification/output.json")
        if alt_path.exists():
            path = alt_path
        else:
            raise FileNotFoundError(f"Submission file not found: {path.absolute()}")

    submission_data = json.loads(path.read_text(encoding="utf-8"))
    token = token or os.environ.get("JUDGE_TOKEN") or os.environ.get("SUBMISSION_TOKEN") or os.environ.get("API_KEY") or "change-me"

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-Judge-Token"] = token
        headers["X-API-Key"] = token

    def _do_post(data):
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            target_url,
            data=payload,
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            res_data = resp.read().decode("utf-8")
            return json.loads(res_data) if res_data else {"status": "ok"}

    try:
        return _do_post(submission_data)
    except urllib.error.HTTPError as err:
        if err.code == 400:
            # Fallback: strict schema server requiring exact 5 standard keys
            standard_keys = {"category", "status", "review_reason", "has_defect", "defect_fields"}
            clean_payload = {}
            for eid, item in submission_data.items():
                if isinstance(item, dict):
                    clean_payload[eid] = {k: item[k] for k in standard_keys if k in item}
                else:
                    clean_payload[eid] = item
            return _do_post(clean_payload)
        raise err



if __name__ == "__main__":
    import sys
    sub_file = sys.argv[1] if len(sys.argv) > 1 else "shipping-verification/output.json"
    if not Path(sub_file).exists() and Path("submission.json").exists():
        sub_file = "submission.json"

    url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8080/submit"
    token = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("JUDGE_TOKEN", "change-me")

    print(f"Posting {sub_file} to {url}...")
    try:
        response = post_submission(sub_file, url, token=token)
        print("Submission posted successfully. Server response:", json.dumps(response, indent=2))
    except Exception as e:
        print(f"Error posting submission: {e}")


