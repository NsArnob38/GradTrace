#!/usr/bin/env python3
"""
NSU Audit Core — Academic Transcript Audit CLI
Usage:
    python audit.py <transcript.csv> <program> [--normal-report | --full-report]

Program: CSE or BBA
"""

import argparse
import os
import sys

# Fix encoding for Windows terminals
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from engine.credit_engine import process_transcript
from engine.cgpa_engine import process_cgpa
from engine.audit_engine import run_audit, build_graduation_roadmap
from engine.course_db import ALL_COURSES

# ─── Color helpers (graceful fallback) ───────────────────
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    GREEN = Fore.GREEN
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    CYAN = Fore.CYAN
    BOLD = Style.BRIGHT
    RESET = Style.RESET_ALL
except ImportError:
    GREEN = RED = YELLOW = CYAN = BOLD = RESET = ""


# ─── Formatting helpers ──────────────────────────────────

def color(text, clr):
    return f"{clr}{text}{RESET}"


def header_bar(title, width=50):
    return f"\n{'=' * width}\n  {title}\n{'=' * width}"


def section_bar(title, width=50):
    return f"\n{'─' * width}\n  {title}\n{'─' * width}"


def format_table(headers, rows, col_widths=None):
    """Build a simple aligned ASCII table."""
    if col_widths is None:
        col_widths = []
        for i, h in enumerate(headers):
            max_w = len(h)
            for row in rows:
                if i < len(row):
                    max_w = max(max_w, len(str(row[i])))
            col_widths.append(max_w + 2)

    sep = "+" + "+".join("-" * w for w in col_widths) + "+"
    def fmt_row(vals):
        cells = []
        for i, v in enumerate(vals):
            w = col_widths[i] if i < len(col_widths) else 12
            cells.append(f" {str(v).ljust(w - 1)}")
        return "|" + "|".join(cells) + "|"

    lines = [sep, fmt_row(headers), sep]
    for row in rows:
        lines.append(fmt_row(row))
    lines.append(sep)
    return "\n".join(lines)


def status_color(status):
    """Colorize a status string."""
    if status == "BEST":
        return color(status, GREEN)
    elif status in ("FAILED", "REJECTED-TRANSFER"):
        return color(status, RED)
    elif status in ("WITHDRAWN", "RETAKE-IGNORED", "UNAUTHORIZED-RETAKE"):
        return color(status, YELLOW)
    elif status == "WAIVED":
        return color(status, CYAN)
    return status


def grade_color(grade):
    """Colorize a grade."""
    if grade in ("A", "A-", "B+", "B", "B-"):
        return color(grade, GREEN)
    elif grade in ("C+", "C", "C-"):
        return color(grade, YELLOW)
    elif grade in ("D+", "D"):
        return color(grade, YELLOW)
    elif grade in ("F", "I"):
        return color(grade, RED)
    elif grade == "W":
        return color(grade, YELLOW)
    elif grade == "T":
        return color(grade, CYAN)
    return grade


# ─── Report Generators ───────────────────────────────────

def print_normal_report(filepath, program, records, credits_attempted, credits_earned, cgpa_data, audit_result):
    """Print the brief report: Summary header (Credits & CGPA)."""
    total_req = audit_result["total_credits_required"]
    cgpa = cgpa_data["cgpa"]
    standing = cgpa_data["standing"]
    eligible = audit_result["eligible"]
    reasons = audit_result["reasons"]
    
    print(header_bar(f"NSU AUDIT REPORT - {program.upper()}"))
    print(f"  Student Transcript : {os.path.basename(filepath)}")
    print(f"  Credits Attempted  : {credits_attempted}")

    earned_str = f"{credits_earned} / {total_req}"
    print(f"  Credits Earned     : {color(earned_str, GREEN if credits_earned >= total_req else RED)}")
    
    cgpa_str = f"{cgpa:.2f} / 4.00"
    print(f"  CGPA               : {color(cgpa_str, GREEN if cgpa >= 2.0 else RED)}")

    if program.upper() == "CSE":
        core_cgpa = audit_result.get("major_core_cgpa", 0.0)
        core_str = f"{core_cgpa:.2f} / 4.00"
        print(f"  Major Core CGPA    : {color(core_str, GREEN if core_cgpa >= 2.0 else RED)}")
    else:
        core_cgpa = audit_result.get("core_cgpa", 0.0)
        print(f"  School & Core CGPA : {color(f'{core_cgpa:.2f}', GREEN if core_cgpa >= 2.0 else RED)}")

    if "PROBATION" in standing or "DISMISSAL" in standing:
        print(f"  Academic Standing  : {color(standing, RED)}")

    if eligible:
        print(f"  Graduation Eligible: {color('YES', GREEN)}")
    else:
        print(f"  Graduation Eligible: {color('NO', RED)}")
        for r in reasons:
            print(f"    {color('X', RED)} {r}")
    
    print("=" * 50)

def print_prerequisite_violations(violations):
    """Print detailed prerequisite violations."""
    print(section_bar("PREREQUISITE VIOLATIONS"))
    print(f"  {color('CAUTION:', RED)} The following courses were taken without passing prerequisites.")
    print("  This may lead to credit cancellation or administrative holds.\n")
    
    for v in violations:
        course = v["course"]
        sem = v["semester"]
        missing = ", ".join(v["missing"])
        print(f"    {color('!', RED)} {color(course, BOLD)} (taken in {sem})")
        print(f"       Missing: {color(missing, YELLOW)}")
    print()

def print_full_report(filepath, program, records, credits_attempted, credits_earned, cgpa_data, audit_result):
    """Print the full report: Summary + Result Sheet + Roadmap + Missing Courses."""
    # 1. Start with Normal (Summary)
    print_normal_report(filepath, program, records, credits_attempted, credits_earned, cgpa_data, audit_result)
    
    # 2. Prerequisite Detail (If any)
    violations = audit_result.get("prereq_violations", [])
    if violations:
        print_prerequisite_violations(violations)
    
    # 2. Course Result Sheet
    print(section_bar("COURSE RESULT SHEET"))
    headers = ["Code", "Course Name", "Cr", "Grade", "Semester", "Status"]
    rows = []
    raw_rows = []
    for r in records:
        rows.append([r.course_code, r.course_name[:30], str(r.credits), grade_color(r.grade), r.semester, status_color(r.status)])
        raw_rows.append([r.course_code, r.course_name[:30], str(r.credits), r.grade, r.semester, r.status])
    
    col_widths = []
    for i, h in enumerate(headers):
        max_w = len(h)
        for row in raw_rows:
            max_w = max(max_w, len(str(row[i])))
        col_widths.append(max_w + 2)

    sep = "+" + "+".join("-" * w for w in col_widths) + "+"
    def fmt_row(vals, raw_vals=None):
        cells = []
        for i, v in enumerate(vals):
            w = col_widths[i] if i < len(col_widths) else 12
            raw_len = len(str(raw_vals[i])) if raw_vals else len(str(v))
            cells.append(f" {v}{' ' * max(0, w - 1 - raw_len)}")
        return "|" + "|".join(cells) + "|"

    print(sep)
    print(fmt_row(headers, headers))
    print(sep)
    for i, row in enumerate(rows):
        print(fmt_row(row, raw_rows[i]))
    print(sep)
    print(f"  Total: {len(records)} course attempt(s)")

    # 3. Path to Graduation (Roadmap)
    roadmap = audit_result.get("roadmap")
    if roadmap and not roadmap["eligible"]:
        print_graduation_roadmap(roadmap)
    
    # 4. Detailed Missing Courses
    remaining = audit_result.get("remaining", {})
    if remaining:
        print(section_bar("DETAILED MISSING COURSES"))
        for category, courses in remaining.items():
            print(f"\n  {color(f'[{category}]', YELLOW)}")
            for code, cr in courses.items():
                print(f"    {color('o', RED)} {code} ({cr} credits)")
    print("\n" + "=" * 50)


def print_graduation_roadmap(roadmap):
    """Print the PATH TO GRADUATION section."""
    print(section_bar("PATH TO GRADUATION"))

    if roadmap["eligible"]:
        print(f"  {color('All graduation requirements met!', GREEN)}")
        return

    # Estimates bar
    gap = roadmap["credit_gap"]
    est_sem = roadmap["estimated_semesters"]
    est_courses = roadmap["estimated_courses_left"]
    print(f"\n  {color('Summary:', BOLD)}")
    if gap > 0:
        print(f"    Credits still needed  : {color(str(gap), RED)}")
    if est_courses > 0:
        print(f"    Courses to complete   : {est_courses}")
    print(f"    Estimated semesters   : ~{est_sem} (at 15 credits/semester)")

    # Priority legend
    priority_colors = {
        "CRITICAL": RED,
        "HIGH": RED,
        "MEDIUM": YELLOW,
        "LOW": CYAN,
        "RECOMMENDED": GREEN,
    }

    # Steps
    print(f"\n  {color('Action Items:', BOLD)}")
    for i, step in enumerate(roadmap["steps"], 1):
        prio = step["priority"]
        prio_clr = priority_colors.get(prio, YELLOW)
        tag = color(f"[{prio}]", prio_clr)
        cat = color(step['category'], BOLD)

        print(f"\n    {i}. {tag} {cat}")
        print(f"       {step['action']}")
        if step.get("detail"):
            # Wrap long detail lines
            detail = step["detail"]
            if len(detail) > 70:
                parts = detail.split(", ")
                lines = []
                current = ""
                for p in parts:
                    if current and len(current + ", " + p) > 65:
                        lines.append(current)
                        current = p
                    else:
                        current = (current + ", " + p) if current else p
                if current:
                    lines.append(current)
                for line in lines:
                    print(f"       {color(line, YELLOW)}")
            else:
                print(f"       {color(detail, YELLOW)}")

    print()


# ─── Main CLI ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="NSU Audit Core — Academic Transcript Audit Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python audit.py transcript.csv CSE --normal-report
  python audit.py transcript.csv BBA --concentration FIN --full-report
        """
    )
    parser.add_argument("transcript", help="Path to transcript CSV file")
    parser.add_argument("program", choices=["CSE", "BBA", "cse", "bba"],
                        help="Program: CSE or BBA")
    parser.add_argument("--concentration", "-c",
                        choices=["ACT", "FIN", "MKT", "MGT", "HRM", "MIS", "SCM", "ECO", "INB",
                                 "act", "fin", "mkt", "mgt", "hrm", "mis", "scm", "eco", "inb"],
                        help="BBA concentration/major area")
    report_group = parser.add_mutually_exclusive_group(required=False)
    report_group.add_argument("--normal-report", action="store_true",
                              help="Show summary report only (default)")
    report_group.add_argument("--full-report", action="store_true",
                              help="Show full course history + remaining courses")

    args = parser.parse_args()

    # Validate file exists
    if not os.path.isfile(args.transcript):
        print(color(f"Error: File '{args.transcript}' not found.", RED))
        sys.exit(1)

    program = args.program.upper()
    concentration = args.concentration.upper() if args.concentration else None

    # Auto-detect concentration from filename if not specified
    if program == "BBA" and concentration is None:
        from engine.audit_engine import VALID_CONCENTRATIONS
        basename = os.path.basename(args.transcript)
        parts = basename.replace(".csv", "").split("_")
        for part in parts:
            if part.upper() in VALID_CONCENTRATIONS:
                concentration = part.upper()
                break

    # Level 1: Credit tallying
    records, credits_attempted, credits_earned = process_transcript(args.transcript)

    from engine.course_db import ALL_COURSES
    unrecognized = set(r.course_code for r in records if r.course_code not in ALL_COURSES and r.grade not in ("W", "I"))
    if unrecognized:
        print(header_bar(f"NSU AUDIT REPORT - {program}"))
        print(f"  Student Transcript : {os.path.basename(args.transcript)}")
        print(f"\n  {color('!!! FAKE TRANSCRIPT DETECTED !!!', RED)}")
        print(f"  Unrecognized Course Codes: {color(', '.join(unrecognized), RED)}")
        print(f"  This transcript contains courses that do not exist in the NSU database.")
        print(f"  {color('AUDIT ABORTED', RED)}")
        print(f"  {'-' * 46}\n")
        sys.exit(1)

    # Level 2: CGPA calculation
    cgpa_data = process_cgpa(records, program)

    # Level 3: Audit / deficiency check
    audit_result = run_audit(
        records,
        program,
        cgpa_data["waivers"],
        credits_earned,
        cgpa_data["cgpa"],
        cgpa_data.get("credit_reduction", 0),
        concentration=concentration,
    )

    # Build graduation roadmap
    major_cgpa_for_roadmap = 0.0
    if program == "CSE":
        major_cgpa_for_roadmap = audit_result.get("major_core_cgpa", 0.0)
    else:
        major_cgpa_for_roadmap = audit_result.get("core_cgpa", 0.0)

    roadmap = build_graduation_roadmap(
        program, records, credits_earned,
        cgpa_data["cgpa"],
        major_cgpa_for_roadmap,
        audit_result,
        cgpa_data["standing"],
    )
    audit_result["roadmap"] = roadmap

    # Output
    if args.full_report:
        print_full_report(args.transcript, program, records, credits_attempted,
                          credits_earned, cgpa_data, audit_result)
    else:
        print_normal_report(args.transcript, program, records, credits_attempted,
                            credits_earned, cgpa_data, audit_result)


if __name__ == "__main__":
    main()
