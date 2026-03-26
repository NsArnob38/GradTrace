"""
GradeTrace CLI — Authentication

Handles login, token caching, and token refresh for the CLI.
Tokens are stored in ~/.gradetrace/session.json
"""

import json
import os
import sys
import time
from pathlib import Path

SESSION_DIR = Path.home() / ".gradetrace"
SESSION_FILE = SESSION_DIR / "session.json"


def _ensure_dir():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)


def save_session(data: dict):
    """Save auth tokens to disk."""
    _ensure_dir()
    data["saved_at"] = time.time()
    SESSION_FILE.write_text(json.dumps(data, indent=2))


def load_session() -> dict | None:
    """Load saved session, or None if not logged in."""
    if not SESSION_FILE.exists():
        return None
    try:
        return json.loads(SESSION_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def clear_session():
    """Delete saved session (logout)."""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def is_token_expired(session: dict) -> bool:
    """Check if the access token is likely expired."""
    saved_at = session.get("saved_at", 0)
    expires_in = session.get("expires_in", 3600)
    return time.time() > (saved_at + expires_in - 60)  # 60s buffer


def get_token(api_url: str) -> str | None:
    """Get a valid access token, refreshing if needed."""
    session = load_session()
    if not session:
        return None

    if not is_token_expired(session):
        return session.get("access_token")

    # Try to refresh
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        return None

    try:
        import requests
        resp = requests.post(
            f"{api_url}/auth/refresh",
            json={"refresh_token": refresh_token},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            save_session(data)
            return data.get("access_token")
    except Exception:
        pass

    return None


def login_interactive(api_url: str) -> dict | None:
    """Interactive login prompt. Returns session data or None."""
    from packages.cli.ui import console, AMBER, GRAY, RED, BOLD

    console.print(f"\n  [{AMBER}]🔐 GradeTrace Login[/]")
    console.print(f"  [{GRAY}]Use your @northsouth.edu credentials[/]\n")

    email = console.input(f"  [{BOLD}]Email:[/] ")
    if not email.strip():
        return None

    from rich.prompt import Prompt
    password = Prompt.ask(f"  [{BOLD}]Password[/]", password=True, console=console)

    console.print()

    try:
        import requests
        with console.status(f"[{AMBER}]Authenticating...[/]", spinner="dots"):
            resp = requests.post(
                f"{api_url}/auth/login",
                json={"email": email.strip(), "password": password},
                timeout=15,
            )

        if resp.status_code == 200:
            data = resp.json().get("data", {})
            save_session(data)
            return data
        else:
            detail = resp.json().get("detail", "Login failed")
            console.print(f"  [{RED}]✗ {detail}[/]\n")
            return None
    except requests.ConnectionError:
        console.print(f"  [{RED}]✗ Cannot connect to API at {api_url}[/]")
        console.print(f"  [{GRAY}]  Is the server running?[/]\n")
        return None
    except Exception as e:
        console.print(f"  [{RED}]✗ Error: {e}[/]\n")
        return None
