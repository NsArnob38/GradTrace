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
    """Interactive login/signup menu. Returns session data or None."""
    from packages.cli.ui import console, AMBER, GRAY, RED, GREEN, BOLD

    console.print(f"\n  [{AMBER}]🔐 GradeTrace Account[/]")
    console.print(f"  [{GRAY}]Choose an option:[/]\n")
    console.print(f"    [{GREEN}]1[/]  Log in with Email & Password")
    console.print(f"    [{GREEN}]2[/]  Create Account / Set Password (for existing Google users)")
    console.print(f"    [{GREEN}]0[/]  Cancel\n")

    choice = console.input(f"  [{BOLD}]Choice (0-2):[/] ").strip()
    
    if choice == "1":
        return _login_password(api_url)
    elif choice == "2":
        return _register(api_url)
    
    return None

def _login_password(api_url: str) -> dict | None:
    from packages.cli.ui import console, AMBER, RED, BOLD, GRAY
    console.print(f"\n  [{GRAY}]--- Password Login ---[/]")
    email = console.input(f"  [{BOLD}]Email:[/] ").strip()
    if not email: return None
    password = console.input(f"  [{BOLD}]Password:[/] ")
    
    import requests
    try:
        with console.status(f"[{AMBER}]Authenticating...[/]", spinner="dots"):
            resp = requests.post(
                f"{api_url}/auth/login",
                json={"email": email, "password": password},
                timeout=15,
            )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            save_session(data)
            return data
        console.print(f"  [{RED}]✗ {resp.json().get('detail', 'Login failed')}[/]\n")
    except Exception as e:
        console.print(f"  [{RED}]✗ Error: {e}[/]\n")
    return None

def _register(api_url: str) -> dict | None:
    from packages.cli.ui import console, AMBER, RED, GREEN, BOLD, GRAY
    console.print(f"\n  [{GRAY}]--- Register / Set Password ---[/]")
    console.print(f"  [{GRAY}](Must be a @northsouth.edu email)[/]\n")
    
    email = console.input(f"  [{BOLD}]Email:[/] ").strip()
    if not email: return None
    
    password = console.input(f"  [{BOLD}]Create Password:[/] ")
    if not password or len(password) < 6:
        console.print(f"  [{RED}]✗ Password must be at least 6 characters[/]\n")
        return None
        
    full_name = console.input(f"  [{BOLD}]Full Name (optional):[/] ").strip()
    student_id = console.input(f"  [{BOLD}]Student ID (optional):[/] ").strip()
    
    import requests
    try:
        with console.status(f"[{AMBER}]Creating account...[/]", spinner="dots"):
            resp = requests.post(
                f"{api_url}/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": full_name,
                    "student_id": student_id
                },
                timeout=15,
            )
            
        if resp.status_code == 200:
            console.print(f"\n  [{GREEN}]🎉 Account created successfully![/]")
            
            # Auto-login after registration
            with console.status(f"[{AMBER}]Logging in...[/]", spinner="dots"):
                login_resp = requests.post(f"{api_url}/auth/login", json={"email": email, "password": password}, timeout=10)
                if login_resp.status_code == 200:
                    data = login_resp.json().get("data", {})
                    save_session(data)
                    return data
            return None
        console.print(f"  [{RED}]✗ {resp.json().get('detail', 'Registration failed')}[/]\n")
    except Exception as e:
        console.print(f"  [{RED}]✗ Error: {e}[/]\n")
    return None
