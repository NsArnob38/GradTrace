"""
GradeTrace CLI — API Client

HTTP wrapper for all GradeTrace API calls.
"""

import requests
from pathlib import Path


class APIClient:
    """Thin HTTP client for the GradeTrace FastAPI backend."""

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    @property
    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    # ── Health ──

    def health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    # ── Auth ──

    def login(self, email: str, password: str) -> dict:
        r = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password},
            timeout=15,
        )
        r.raise_for_status()
        return r.json()

    # ── Profile ──

    def get_profile(self) -> dict:
        r = requests.get(f"{self.base_url}/me", headers=self._headers, timeout=10)
        r.raise_for_status()
        return r.json().get("data", {})

    # ── Transcripts ──

    def upload_transcript(self, filepath: str) -> dict:
        """Upload a CSV transcript file."""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        with open(filepath, "rb") as f:
            r = requests.post(
                f"{self.base_url}/transcripts/upload",
                files={"file": (Path(filepath).name, f, "text/csv")},
                headers=headers,
                timeout=30,
            )
        r.raise_for_status()
        return r.json()

    # ── Audit ──

    def run_audit(self, transcript_id: str, program: str, 
                  concentration: str | None = None,
                  custom_mappings: dict | None = None,
                  ignored_courses: list[str] | None = None) -> dict:
        body = {
            "program": program,
            "concentration": concentration,
            "custom_mappings": custom_mappings,
            "ignored_courses": ignored_courses
        }
        r = requests.post(
            f"{self.base_url}/audit/{transcript_id}",
            json=body,
            headers=self._headers,
            timeout=60,
        )
        r.raise_for_status()
        return r.json()

    def get_audit(self, transcript_id: str) -> dict:
        r = requests.get(
            f"{self.base_url}/audit/{transcript_id}",
            headers=self._headers,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()

    def list_history(self) -> list:
        r = requests.get(
            f"{self.base_url}/audit",
            headers=self._headers,
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("data", [])

    def delete_audit(self, transcript_id: str) -> dict:
        r = requests.delete(
            f"{self.base_url}/audit/{transcript_id}",
            headers=self._headers,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
