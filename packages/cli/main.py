"""
GradeTrace CLI — Main Entry Point

Interactive menu-driven CLI for transcript auditing.
Also supports direct commands via arguments.

Usage:
    python -m packages.cli                  # Interactive menu
    python -m packages.cli audit file.csv   # Direct command
"""

import argparse
import sys
import os
import glob

DEFAULT_API_URL = os.environ.get("GRADETRACE_API_URL", "http://localhost:8000")


def main():
    from packages.cli.ui import console, logo, AMBER, GRAY, RED, GREEN, BOLD
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel

    parser = argparse.ArgumentParser(
        prog="gradetrace",
        description="GradeTrace — Academic Transcript Auditor CLI",
    )
    parser.add_argument(
        "--api-url", default=DEFAULT_API_URL,
        help=f"API server URL (default: {DEFAULT_API_URL})",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # Direct subcommands (still available)
    sub.add_parser("login", help="Log in with your NSU email")
    sub.add_parser("logout", help="Log out and clear saved session")
    sub.add_parser("status", help="Show login status and account info")

    audit_p = sub.add_parser("audit", help="Upload a transcript and run audit")
    audit_p.add_argument("file", help="Path to transcript file")
    audit_p.add_argument("--program", "-p", default="CSE", choices=["CSE", "BBA"])
    audit_p.add_argument("--concentration", "-c", default=None)
    audit_p.add_argument("--edit", "-e", action="store_true", help="Manually edit courses before auditing")

    sub.add_parser("history", help="View past audit results")

    offline_p = sub.add_parser("offline", help="Run audit locally without API")
    offline_p.add_argument("file", help="Path to transcript file")
    offline_p.add_argument("--program", "-p", default="CSE", choices=["CSE", "BBA"])
    offline_p.add_argument("--concentration", "-c", default=None)
    offline_p.add_argument("--edit", "-e", action="store_true", help="Manually edit courses before auditing")

    args = parser.parse_args()

    if args.command:
        # Direct command mode
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
    else:
        # Interactive menu mode
        _interactive_menu(args.api_url)


# ═══════════════════════════════════════════════
# Interactive Menu
# ═══════════════════════════════════════════════

def _interactive_menu(api_url: str):
    """Main interactive menu loop."""
    from packages.cli.ui import console, logo, AMBER, GRAY, RED, GREEN, BOLD, BLUE

    logo()

    while True:
        console.print(f"\n  [{AMBER}]What would you like to do?[/]\n")
        console.print(f"    [{GREEN}]1[/]  📋  Run audit on a transcript (offline)")
        console.print(f"    [{GREEN}]2[/]  ☁️   Upload & audit via API (online)")
        console.print(f"    [{GREEN}]3[/]  📜  View audit history (online)")
        console.print(f"    [{GREEN}]4[/]  🔐  Login / Account status")
        console.print(f"    [{GREEN}]5[/]  🚪  Logout")
        console.print(f"    [{RED}]0[/]  ✕   Exit")
        console.print()

        try:
            choice = console.input(f"  [{BOLD}]Enter choice (0-5):[/] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n  [{GRAY}]Goodbye![/]\n")
            break

        if choice == "0":
            console.print(f"\n  [{GRAY}]Goodbye![/]\n")
            break
        elif choice == "1":
            _menu_offline_audit()
        elif choice == "2":
            _menu_online_audit(api_url)
        elif choice == "3":
            _cmd_history(api_url)
        elif choice == "4":
            _menu_account(api_url)
        elif choice == "5":
            _cmd_logout()
        else:
            console.print(f"  [{RED}]Invalid choice. Enter a number 0-5.[/]")


def _menu_offline_audit():
    """Interactive offline audit flow."""
    from packages.cli.ui import console, AMBER, GRAY, RED, GREEN, BOLD, BLUE
    from packages.cli.formatter import format_full_audit

    console.print(f"\n  [{AMBER}]▸ Offline Audit[/]")
    console.print(f"  [{GRAY}]{'─' * 42}[/]")

    # Step 1: Find transcript files
    transcript_files = _find_transcript_files()

    if transcript_files:
        console.print(f"\n  [{GRAY}]Found transcript files:[/]\n")
        for i, f in enumerate(transcript_files, 1):
            console.print(f"    [{GREEN}]{i}[/]  {os.path.basename(f)}  [{GRAY}]{os.path.dirname(f) or '.'}[/]")
        console.print(f"    [{AMBER}]{len(transcript_files) + 1}[/]  Enter a custom path")
        console.print()

        try:
            file_choice = console.input(f"  [{BOLD}]Select file (1-{len(transcript_files) + 1}):[/] ").strip()
        except (KeyboardInterrupt, EOFError):
            return

        idx = int(file_choice) if file_choice.isdigit() else 0
        if 1 <= idx <= len(transcript_files):
            filepath = transcript_files[idx - 1]
        elif idx == len(transcript_files) + 1:
            filepath = console.input(f"  [{BOLD}]File path:[/] ").strip()
        else:
            console.print(f"  [{RED}]Invalid choice.[/]")
            return
    else:
        filepath = console.input(f"  [{BOLD}]File path:[/] ").strip()

    if not filepath or not os.path.isfile(filepath):
        console.print(f"  [{RED}]✗ File not found: {filepath}[/]")
        return

    # Step 2: Select program
    console.print(f"\n  [{GRAY}]Select program:[/]\n")
    console.print(f"    [{GREEN}]1[/]  CSE — Computer Science & Engineering")
    console.print(f"    [{GREEN}]2[/]  BBA — Bachelor of Business Administration")
    console.print()

    try:
        prog_choice = console.input(f"  [{BOLD}]Program (1-2):[/] ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    program = "CSE" if prog_choice != "2" else "BBA"
    concentration = None

    # Step 3: BBA concentration
    if program == "BBA":
        console.print(f"\n  [{GRAY}]Select concentration (or skip):[/]\n")
        concs = ["ACT", "FIN", "MKT", "MGT", "HRM", "MIS", "SCM", "ECO", "INB"]
        labels = [
            "Accounting", "Finance", "Marketing", "Management",
            "Human Resource Mgmt", "Info Systems", "Supply Chain",
            "Economics", "International Business",
        ]
        for i, (c, l) in enumerate(zip(concs, labels), 1):
            console.print(f"    [{GREEN}]{i}[/]  {c} — {l}")
        console.print(f"    [{AMBER}]0[/]  Auto-detect / Skip")
        console.print()

        try:
            conc_choice = console.input(f"  [{BOLD}]Concentration (0-9):[/] ").strip()
        except (KeyboardInterrupt, EOFError):
            return

        cidx = int(conc_choice) if conc_choice.isdigit() else 0
        if 1 <= cidx <= len(concs):
            concentration = concs[cidx - 1]

    # Step 3.5: Select audit level
    console.print(f"\n  [{GRAY}]Select audit level:[/]\n")
    console.print(f"    [{GREEN}]1[/]  Level 1 — Credits Only")
    console.print(f"    [{GREEN}]2[/]  Level 2 — Credits + CGPA + Standing")
    console.print(f"    [{GREEN}]3[/]  Level 3 — Complete Degree Audit")
    console.print(f"    [{GREEN}]4[/]  Full    — Audit + Graduation Roadmap")
    console.print()

    try:
        level_choice = console.input(f"  [{BOLD}]Choice (1-4, Default 4):[/] ").strip()
    except (KeyboardInterrupt, EOFError):
        return
    audit_level = int(level_choice) if level_choice in ("1", "2", "3", "4") else 4

    # Step 4: Run audit
    console.print()
    with console.status(f"[{AMBER}]Running audit...[/]", spinner="dots"):
        from packages.core.unified import UnifiedAuditor
        result = UnifiedAuditor.run_from_file(filepath, program, concentration)

    if result.get("meta", {}).get("fake_transcript") or result.get("meta", {}).get("unrecognized_courses"):
        result = _handle_correction_loop(result, program, filepath)
        if not result:
            return

    console.print(f"  [{GREEN}]✓ Audit complete[/]")
    format_full_audit(result, level=audit_level)


def _menu_online_audit(api_url: str):
    """Interactive online audit (upload + run via API)."""
    from packages.cli.ui import console, AMBER, GRAY, RED, GREEN, BOLD
    from packages.cli.api_client import APIClient
    from packages.cli.formatter import format_full_audit

    console.print(f"\n  [{AMBER}]▸ Online Audit (via API)[/]")
    console.print(f"  [{GRAY}]{'─' * 42}[/]")

    token = _ensure_auth(api_url)
    if not token:
        return
    client = APIClient(api_url, token)

    # File selection (same as offline)
    transcript_files = _find_transcript_files()
    if transcript_files:
        console.print(f"\n  [{GRAY}]Found transcript files:[/]\n")
        for i, f in enumerate(transcript_files, 1):
            console.print(f"    [{GREEN}]{i}[/]  {os.path.basename(f)}")
        console.print(f"    [{AMBER}]{len(transcript_files) + 1}[/]  Enter a custom path")
        console.print()

        try:
            file_choice = console.input(f"  [{BOLD}]Select file (1-{len(transcript_files) + 1}):[/] ").strip()
        except (KeyboardInterrupt, EOFError):
            return

        idx = int(file_choice) if file_choice.isdigit() else 0
        if 1 <= idx <= len(transcript_files):
            filepath = transcript_files[idx - 1]
        elif idx == len(transcript_files) + 1:
            filepath = console.input(f"  [{BOLD}]File path:[/] ").strip()
        else:
            console.print(f"  [{RED}]Invalid choice.[/]")
            return
    else:
        filepath = console.input(f"  [{BOLD}]CSV file path:[/] ").strip()

    if not filepath or not os.path.isfile(filepath):
        console.print(f"  [{RED}]✗ File not found: {filepath}[/]")
        return

    # Program selection
    console.print(f"\n  [{GRAY}]Select program:[/]\n")
    console.print(f"    [{GREEN}]1[/]  CSE")
    console.print(f"    [{GREEN}]2[/]  BBA")
    console.print()

    try:
        prog_choice = console.input(f"  [{BOLD}]Program (1-2):[/] ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    program = "CSE" if prog_choice != "2" else "BBA"
    concentration = None

    if program == "BBA":
        concs = ["ACT", "FIN", "MKT", "MGT", "HRM", "MIS", "SCM", "ECO", "INB"]
        console.print(f"\n  [{GRAY}]Concentration (0 = auto-detect):[/]")
        for i, c in enumerate(concs, 1):
            console.print(f"    [{GREEN}]{i}[/]  {c}")
        console.print()
        try:
            conc_choice = console.input(f"  [{BOLD}]Choice (0-9):[/] ").strip()
        except (KeyboardInterrupt, EOFError):
            return
        cidx = int(conc_choice) if conc_choice.isdigit() else 0
        if 1 <= cidx <= len(concs):
            concentration = concs[cidx - 1]

    # Level selection
    console.print(f"\n  [{GRAY}]Select audit level (1-4, Default 4):[/]")
    console.print(f"    [{GREEN}]1[/] L1 | [{GREEN}]2[/] L2 | [{GREEN}]3[/] L3 | [{GREEN}]4[/] Full")
    try:
        level_choice = console.input(f"  [{BOLD}]Level (1-4):[/] ").strip()
    except (KeyboardInterrupt, EOFError):
        return
    audit_level = int(level_choice) if level_choice in ("1", "2", "3", "4") else 4

    # Upload
    console.print()
    with console.status(f"[{AMBER}]Uploading {os.path.basename(filepath)}...[/]", spinner="dots"):
        try:
            upload_res = client.upload_transcript(filepath)
        except Exception as e:
            console.print(f"  [{RED}]✗ Upload failed: {e}[/]")
            return

    transcript_data = upload_res.get("data", {})
    transcript_id = transcript_data.get("id")
    if not transcript_id:
        console.print(f"  [{RED}]✗ Upload failed — no transcript ID[/]")
        return

    console.print(f"  [{GREEN}]✓ Uploaded[/]")

    # Run audit
    with console.status(f"[{AMBER}]Running audit...[/]", spinner="dots"):
        try:
            audit_res = client.run_audit(transcript_id, program, concentration)
        except Exception as e:
            console.print(f"  [{RED}]✗ Audit failed: {e}[/]")
            return

    result = audit_res.get("data", audit_res)
    console.print(f"  [{GREEN}]✓ Audit complete[/]")
    format_full_audit(result, level=audit_level)


def _menu_account(api_url: str):
    """Account status / login menu."""
    from packages.cli.auth import load_session, is_token_expired
    from packages.cli.ui import console, AMBER, GRAY, RED, GREEN, BOLD

    session = load_session()
    if session and not is_token_expired(session):
        console.print(f"\n  [{GREEN}]✓ You are logged in[/]")
        _cmd_status(api_url)

        console.print(f"    [{GRAY}]1 = Stay logged in  │  2 = Log out  │  3 = Re-login[/]")
        try:
            choice = console.input(f"\n  [{BOLD}]Choice (1-3):[/] ").strip()
        except (KeyboardInterrupt, EOFError):
            return
        if choice == "2":
            _cmd_logout()
        elif choice == "3":
            _cmd_logout()
            _cmd_login(api_url)
    else:
        console.print(f"\n  [{GRAY}]You are not logged in.[/]")
        _cmd_login(api_url)


def _handle_correction_loop(result: dict, program: str, original_path: str) -> dict | None:
    """Interactive loop to fix unrecognized courses or manually edit transcript."""
    from packages.cli.ui import console, AMBER, GRAY, RED, GREEN, BOLD, BLUE
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from packages.core.unified import UnifiedAuditor
    from packages.core.course_catalog import ALL_COURSES

    records = result.get("level_1", {}).get("records", [])
    # If no records (e.g. from a failed CreditAuditor.process), we need to extract from meta if possible
    # but UnifiedAuditor usually returns partial records.
    
    unrecognized = result.get("meta", {}).get("unrecognized_courses", [])
    
    while True:
        console.print(f"\n  [{AMBER}]▸ Transcript Correction Mode[/]")
        console.print(f"  [{GRAY}]{'─' * 42}[/]")
        
        table = Table(show_header=True, header_style="bold", box=None)
        table.add_column("#", style="dim", width=3)
        table.add_column("Code", style="bold", width=10)
        table.add_column("Grade", width=6)
        table.add_column("Semester", width=15)
        table.add_column("Status")

        for i, r in enumerate(records, 1):
            is_bad = r["course_code"] in unrecognized or r["course_code"] not in ALL_COURSES
            status = f"[{RED}]UNRECOGNIZED[/]" if is_bad else f"[{GREEN}]OK[/]"
            table.add_row(str(i), r["course_code"], r["grade"], r["semester"], status)

        console.print(table)
        console.print(f"\n  [{GRAY}]Options: [0] Finish & Re-audit  [#] Edit Row  [q] Cancel[/]")
        
        choice = Prompt.ask("\n  [bold]Selection[/]").strip().lower()
        
        if choice == "q":
            return None
        if choice == "0":
            break
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(records):
                row = records[idx]
                console.print(f"\n  Editing Row {idx + 1}: [{BOLD}]{row['course_code']}[/]")
                new_code = Prompt.ask("    New Code", default=row["course_code"]).strip().upper()
                new_grade = Prompt.ask("    New Grade", default=row["grade"]).strip().upper()
                new_sem = Prompt.ask("    New Semester", default=row["semester"]).strip().title()
                
                row["course_code"] = new_code
                row["grade"] = new_grade
                row["semester"] = new_sem
                
                # Update unrecognized list
                unrecognized = [c for c in unrecognized if c != row["course_code"]]
                if new_code not in ALL_COURSES:
                    unrecognized.append(new_code)
            else:
                console.print(f"  [{RED}]Invalid row number.[/]")

    # Re-audit
    with console.status(f"[{AMBER}]Re-running audit...[/]", spinner="dots"):
        new_result = UnifiedAuditor.run_from_rows(records, program)
    
    # Auto-save logic
    if Confirm.ask(f"\n  Save corrected transcript to [bold]{os.path.basename(original_path)}_corrected.csv[/]?"):
        save_path = f"{os.path.splitext(original_path)[0]}_corrected.csv"
        try:
            import pandas as pd
            df = pd.DataFrame(records)
            # Reorder columns to match standard transcript format
            cols = ["course_code", "course_name", "credits", "grade", "semester"]
            df = df[cols]
            df.to_csv(save_path, index=False)
            console.print(f"  [{GREEN}]✓ Saved to {save_path}[/]")
        except Exception as e:
            console.print(f"  [{RED}]✗ Save failed: {e}[/]")

    return new_result


# ═══════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════

def _find_transcript_files() -> list[str]:
    """Find CSV, PDF, and Image files in common locations."""
    patterns = [
        "*.csv", "transcripts/*.csv", "test_scenarios/*.csv",
        "*.pdf", "transcripts/*.pdf",
        "*.jpg", "*.jpeg", "*.png", "*.webp", "transcripts/*.jpg",
    ]
    files = []
    seen = set()
    for pattern in patterns:
        for f in sorted(glob.glob(pattern)):
            real = os.path.abspath(f)
            if real not in seen:
                files.append(f)
                seen.add(real)
    return files[:20]  # Cap at 20


def _ensure_auth(api_url: str) -> str | None:
    """Ensure user is authenticated. Returns access token or None."""
    from packages.cli.auth import get_token, login_interactive
    from packages.cli.ui import console, GRAY, RED

    token = get_token(api_url)
    if token:
        return token

    console.print(f"\n  [{GRAY}]You need to log in first.[/]")
    session = login_interactive(api_url)
    if not session:
        console.print(f"  [{RED}]Login failed. Returning to menu.[/]\n")
        return None

    return session.get("access_token", "")


# ═══════════════════════════════════════════════
# Direct Commands
# ═══════════════════════════════════════════════

def _cmd_login(api_url: str):
    from packages.cli.auth import login_interactive
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
        console.print(f"\n  [{RED}]✗ Not logged in[/]\n")
        return

    expired = is_token_expired(session)
    if expired:
        console.print(f"\n  [{AMBER}]⚠ Session expired[/]")
    else:
        console.print(f"\n  [{GREEN}]✓ Logged in[/]")

    token = session.get("access_token")
    if token and not expired:
        try:
            client = APIClient(api_url, token)
            profile = client.get_profile()
            console.print(f"    Name:     [{GRAY}]{profile.get('full_name', '—')}[/]")
            console.print(f"    ID:       [{GRAY}]{profile.get('student_id', '—')}[/]")
            console.print(f"    Email:    [{GRAY}]{profile.get('email', '—')}[/]")
            console.print(f"    Program:  [{GRAY}]{profile.get('program', '—')}[/]")
        except Exception:
            console.print(f"  [{GRAY}]Could not fetch profile (API offline?)[/]")
    console.print()


def _cmd_audit(args):
    from packages.cli.api_client import APIClient
    from packages.cli.formatter import format_full_audit
    from packages.cli.ui import console, AMBER, GREEN, RED

    if not os.path.isfile(args.file):
        console.print(f"\n  [{RED}]✗ File not found: {args.file}[/]\n")
        sys.exit(1)

    token = _ensure_auth(args.api_url)
    if not token:
        return
    client = APIClient(args.api_url, token)

    with console.status(f"[{AMBER}]Uploading...[/]", spinner="dots"):
        upload_res = client.upload_transcript(args.file)

    tid = upload_res.get("data", {}).get("id")
    if not tid:
        console.print(f"  [{RED}]✗ Upload failed[/]\n")
        sys.exit(1)

    console.print(f"  [{GREEN}]✓ Uploaded[/]")

    with console.status(f"[{AMBER}]Running audit...[/]", spinner="dots"):
        audit_res = client.run_audit(tid, args.program, args.concentration)

    result = audit_res.get("data", audit_res)
    console.print(f"  [{GREEN}]✓ Audit complete[/]")
    format_full_audit(result)


def _cmd_history(api_url: str):
    from packages.cli.api_client import APIClient
    from packages.cli.formatter import format_history
    from packages.cli.ui import console, AMBER, RED

    token = _ensure_auth(api_url)
    if not token:
        return
    client = APIClient(api_url, token)

    with console.status(f"[{AMBER}]Fetching history...[/]", spinner="dots"):
        try:
            history = client.list_history()
        except Exception as e:
            console.print(f"  [{RED}]✗ Failed: {e}[/]\n")
            return

    format_history(history)


def _cmd_offline(args):
    from packages.cli.formatter import format_full_audit
    from packages.cli.ui import console, AMBER, GREEN, RED

    if not os.path.isfile(args.file):
        console.print(f"\n  [{RED}]✗ File not found: {args.file}[/]\n")
        sys.exit(1)

    with console.status(f"[{AMBER}]Running local audit...[/]", spinner="dots"):
        from packages.core.unified import UnifiedAuditor
        result = UnifiedAuditor.run_from_file(args.file, args.program, args.concentration)

    if args.edit or result.get("meta", {}).get("fake_transcript") or result.get("meta", {}).get("unrecognized_courses"):
        result = _handle_correction_loop(result, args.program, args.file)
        if not result:
            sys.exit(1)

    console.print(f"  [{GREEN}]✓ Local audit complete[/]")
    format_full_audit(result)


if __name__ == "__main__":
    main()
