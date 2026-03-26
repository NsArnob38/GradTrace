"""
GradeTrace CLI — Main Entry Point

Usage:
    python -m packages.cli audit <file.csv> --program CSE [--concentration FIN]
    python -m packages.cli history
    python -m packages.cli login
    python -m packages.cli logout
    python -m packages.cli status
"""

import argparse
import sys
import os

# Default API URL
DEFAULT_API_URL = os.environ.get("GRADETRACE_API_URL", "http://localhost:8000")


def main():
    from packages.cli.ui import console, logo, AMBER, GRAY, RED, GREEN, BOLD

    parser = argparse.ArgumentParser(
        prog="gradetrace",
        description="GradeTrace — Academic Transcript Auditor CLI",
    )
    parser.add_argument(
        "--api-url", default=DEFAULT_API_URL,
        help=f"API server URL (default: {DEFAULT_API_URL})",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # ── login ──
    sub.add_parser("login", help="Log in with your NSU email")

    # ── logout ──
    sub.add_parser("logout", help="Log out and clear saved session")

    # ── status ──
    sub.add_parser("status", help="Show login status and account info")

    # ── audit ──
    audit_p = sub.add_parser("audit", help="Upload a transcript and run audit")
    audit_p.add_argument("file", help="Path to transcript CSV file")
    audit_p.add_argument("--program", "-p", default="CSE", choices=["CSE", "BBA"],
                         help="Degree program (default: CSE)")
    audit_p.add_argument("--concentration", "-c", default=None,
                         help="BBA concentration (e.g., FIN, MKT, ACT)")

    # ── history ──
    sub.add_parser("history", help="View past audit results")

    # ── offline ──
    offline_p = sub.add_parser("offline", help="Run audit locally without API")
    offline_p.add_argument("file", help="Path to transcript CSV file")
    offline_p.add_argument("--program", "-p", default="CSE", choices=["CSE", "BBA"])
    offline_p.add_argument("--concentration", "-c", default=None)

    args = parser.parse_args()

    if not args.command:
        logo()
        console.print(f"\n  [{GRAY}]Run [bold]python -m packages.cli --help[/bold] for usage.[/]\n")
        parser.print_help()
        return

    logo()

    if args.command == "login":
        _cmd_login(args.api_url)
    elif args.command == "logout":
        _cmd_logout()
    elif args.command == "status":
        _cmd_status(args.api_url)
    elif args.command == "audit":
        _cmd_audit(args)
    elif args.command == "history":
        _cmd_history(args.api_url)
    elif args.command == "offline":
        _cmd_offline(args)


def _ensure_auth(api_url: str) -> str:
    """Ensure user is authenticated. Returns access token or exits."""
    from packages.cli.auth import get_token, login_interactive
    from packages.cli.ui import console, GRAY, RED

    token = get_token(api_url)
    if token:
        return token

    console.print(f"\n  [{GRAY}]You need to log in first.[/]")
    session = login_interactive(api_url)
    if not session:
        console.print(f"  [{RED}]Login failed. Aborting.[/]\n")
        sys.exit(1)

    return session.get("access_token", "")


# ═══════════════════════════════════════════════
# Commands
# ═══════════════════════════════════════════════

def _cmd_login(api_url: str):
    from packages.cli.auth import login_interactive, load_session
    from packages.cli.ui import console, GREEN, GRAY

    session = login_interactive(api_url)
    if session:
        email = session.get("user", {}).get("email", "")
        console.print(f"  [{GREEN}]✓ Logged in as {email}[/]")
        console.print(f"  [{GRAY}]Session saved to ~/.gradetrace/session.json[/]\n")


def _cmd_logout():
    from packages.cli.auth import clear_session
    from packages.cli.ui import console, GREEN

    clear_session()
    console.print(f"\n  [{GREEN}]✓ Logged out. Session cleared.[/]\n")


def _cmd_status(api_url: str):
    from packages.cli.auth import load_session, is_token_expired
    from packages.cli.api_client import APIClient
    from packages.cli.ui import console, GREEN, RED, GRAY, AMBER

    session = load_session()
    if not session:
        console.print(f"\n  [{RED}]✗ Not logged in[/]")
        console.print(f"  [{GRAY}]Run: python -m packages.cli login[/]\n")
        return

    expired = is_token_expired(session)
    if expired:
        console.print(f"\n  [{AMBER}]⚠ Session expired — will auto-refresh on next command[/]")
    else:
        console.print(f"\n  [{GREEN}]✓ Logged in[/]")

    # Try to get profile
    token = session.get("access_token")
    if token and not expired:
        try:
            client = APIClient(api_url, token)
            profile = client.get_profile()
            name = profile.get("full_name", "—")
            sid = profile.get("student_id", "—")
            email = profile.get("email", "—")
            prog = profile.get("program", "—")
            console.print(f"    Name:     [{GRAY}]{name}[/]")
            console.print(f"    ID:       [{GRAY}]{sid}[/]")
            console.print(f"    Email:    [{GRAY}]{email}[/]")
            console.print(f"    Program:  [{GRAY}]{prog}[/]")
        except Exception:
            console.print(f"  [{GRAY}]Could not fetch profile (API may be offline)[/]")

    console.print()


def _cmd_audit(args):
    from packages.cli.api_client import APIClient
    from packages.cli.formatter import format_full_audit
    from packages.cli.ui import console, AMBER, GREEN, RED, GRAY
    import os

    # Validate file
    if not os.path.isfile(args.file):
        console.print(f"\n  [{RED}]✗ File not found: {args.file}[/]\n")
        sys.exit(1)

    if not args.file.endswith(".csv"):
        console.print(f"\n  [{RED}]✗ Only CSV files are supported[/]\n")
        sys.exit(1)

    token = _ensure_auth(args.api_url)
    client = APIClient(args.api_url, token)

    # Upload
    with console.status(f"[{AMBER}]Uploading {os.path.basename(args.file)}...[/]", spinner="dots"):
        try:
            upload_res = client.upload_transcript(args.file)
        except Exception as e:
            console.print(f"\n  [{RED}]✗ Upload failed: {e}[/]\n")
            sys.exit(1)

    transcript_data = upload_res.get("data", {})
    transcript_id = transcript_data.get("id")
    if not transcript_id:
        console.print(f"\n  [{RED}]✗ Upload failed: no transcript ID returned[/]\n")
        sys.exit(1)

    console.print(f"  [{GREEN}]✓ Uploaded[/] [{GRAY}]{os.path.basename(args.file)}[/]")

    # Run audit
    with console.status(f"[{AMBER}]Running audit (program: {args.program})...[/]", spinner="dots"):
        try:
            audit_res = client.run_audit(transcript_id, args.program, args.concentration)
        except Exception as e:
            detail = ""
            try:
                import requests
                if hasattr(e, "response") and e.response is not None:
                    detail = e.response.json().get("detail", "")
            except Exception:
                pass
            console.print(f"\n  [{RED}]✗ Audit failed: {detail or e}[/]\n")
            sys.exit(1)

    result = audit_res.get("data", audit_res)
    console.print(f"  [{GREEN}]✓ Audit complete[/]")

    format_full_audit(result)


def _cmd_history(api_url: str):
    from packages.cli.api_client import APIClient
    from packages.cli.formatter import format_history
    from packages.cli.ui import console, AMBER

    token = _ensure_auth(api_url)
    client = APIClient(api_url, token)

    with console.status(f"[{AMBER}]Fetching history...[/]", spinner="dots"):
        try:
            history = client.list_history()
        except Exception as e:
            from packages.cli.ui import RED
            console.print(f"\n  [{RED}]✗ Failed: {e}[/]\n")
            sys.exit(1)

    format_history(history)


def _cmd_offline(args):
    """Run audit locally using packages/core without the API."""
    from packages.cli.formatter import format_full_audit
    from packages.cli.ui import console, AMBER, GREEN, RED
    import os

    if not os.path.isfile(args.file):
        console.print(f"\n  [{RED}]✗ File not found: {args.file}[/]\n")
        sys.exit(1)

    with console.status(f"[{AMBER}]Running local audit...[/]", spinner="dots"):
        from packages.core.unified import UnifiedAuditor
        result = UnifiedAuditor.run_from_file(args.file, args.program, args.concentration)

    if result.get("meta", {}).get("fake_transcript"):
        unrecognized = result["meta"].get("unrecognized_courses", [])
        console.print(f"\n  [{RED}]✗ Fake transcript detected[/]")
        console.print(f"  [{RED}]  Unrecognized: {', '.join(unrecognized)}[/]\n")
        sys.exit(1)

    console.print(f"  [{GREEN}]✓ Local audit complete[/]")
    format_full_audit(result)


if __name__ == "__main__":
    main()
