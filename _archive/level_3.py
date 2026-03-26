#!/usr/bin/env python3
"""
Level 3 — Audit & Graduation Eligibility Report
Compares passed courses against program requirements, identifies deficiencies,
and builds a graduation roadmap.

Usage:
    python level_3.py <transcript.csv> <program>

Program: CSE or BBA
"""

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from engine.credit_engine import process_transcript
from engine.cgpa_engine import process_cgpa
from engine.audit_engine import run_audit, build_graduation_roadmap

# ─── Color helpers ───────────────────────────────────────
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


def color(text, clr):
    return f"{clr}{text}{RESET}"


def header_bar(title, width=50):
    return f"\n{'=' * width}\n  {title}\n{'=' * width}"


def section_bar(title, width=50):
    return f"\n{'─' * width}\n  {title}\n{'─' * width}"


# ─── Report ──────────────────────────────────────────────

def print_level3_report(filepath, program, records, credits_attempted, credits_earned, cgpa_data, audit_result):
    """Print the Level 3 Audit & Graduation Eligibility report."""
    total_req = audit_result["total_credits_required"]
    cgpa = cgpa_data["cgpa"]
    standing = cgpa_data["standing"]
    eligible = audit_result["eligible"]
    reasons = audit_result["reasons"]
    remaining = audit_result.get("remaining", {})

    print(header_bar(f"LEVEL 3 — AUDIT REPORT ({program})"))
    print(f"  Transcript File  : {os.path.basename(filepath)}")
    print(f"  Program          : {program}")

    # Credits
    earned_str = f"{credits_earned} / {total_req}"
    if credits_earned >= total_req:
        print(f"  Credits Earned   : {color(earned_str, GREEN)}")
    else:
        print(f"  Credits Earned   : {color(earned_str, RED)}")

    # Overall CGPA
    cgpa_str = f"{cgpa:.2f} / 4.00"
    if cgpa >= 2.0:
        print(f"  CGPA             : {color(cgpa_str, GREEN)}")
    else:
        print(f"  CGPA             : {color(cgpa_str, RED)}")

    # Program-specific CGPA
    if program == "CSE":
        core_cgpa = audit_result.get("major_core_cgpa", 0.0)
        elective_cgpa = audit_result.get("major_elective_cgpa", 0.0)
        core_str = f"{core_cgpa:.2f} / 4.00"
        elec_str = f"{elective_cgpa:.2f} / 4.00"
        if core_cgpa >= 2.0:
            print(f"  Major Core CGPA  : {color(core_str, GREEN)}")
        else:
            print(f"  Major Core CGPA  : {color(core_str, RED)}")
        if elective_cgpa >= 2.0:
            print(f"  Major Elec CGPA  : {color(elec_str, GREEN)}")
        else:
            print(f"  Major Elec CGPA  : {color(elec_str, RED)}")
    else:  # BBA
        core_cgpa = audit_result.get("core_cgpa", 0.0)
        conc_cgpa = audit_result.get("concentration_cgpa", 0.0)
        conc_label = audit_result.get("concentration_label", "Undeclared")
        if conc_label == "Undeclared":
            conc_label = color("[UNDECLARED]", YELLOW)
        core_str = f"{core_cgpa:.2f} / 4.00"
        conc_str = f"{conc_cgpa:.2f} / 4.00"
        if core_cgpa >= 2.0:
            print(f"  School & Core CGPA: {color(core_str, GREEN)}")
        else:
            print(f"  School & Core CGPA: {color(core_str, RED)}")
        if conc_cgpa >= 2.5:
            print(f"  {conc_label} CGPA  : {color(conc_str, GREEN)}")
        else:
            print(f"  {conc_label} CGPA  : {color(conc_str, RED)}")

    # Standing
    if "PROBATION" in standing or "DISMISSAL" in standing:
        print(f"  Academic Standing: {color(standing, RED)}")

    # Eligibility
    if eligible:
        print(f"  Graduation Eligible: {color('YES', GREEN)}")
    else:
        print(f"  Graduation Eligible: {color('NO', RED)}")
        for r in reasons:
            print(f"    {color('X', RED)} {r}")

    # ── Prerequisites ──
    violations = audit_result.get("prereq_violations", [])
    if violations:
        print(section_bar("PREREQUISITE VIOLATIONS"))
        print(f"  {color('CAUTION:', RED)} Found {len(violations)} violation(s):\n")
        for v in violations:
            print(f"    {color('!', RED)} {v['course']} (taken in {v['semester']})")
            print(f"       Missing: {color(', '.join(v['missing']), YELLOW)}")

    print("=" * 50)

    # ── Remaining Courses ──
    if remaining:
        print(section_bar("MISSING COURSES / REQUIREMENTS"))
        total_missing_courses = 0
        total_missing_credits = 0
        for category, courses in remaining.items():
            cat_credits = sum(cr for _, cr in courses.items())
            total_missing_courses += len(courses)
            total_missing_credits += cat_credits

            print(f"\n  {color(f'[{category}]', YELLOW)} — {len(courses)} course(s), {cat_credits} credits")
            for code, cr in courses.items():
                print(f"    {color('○', RED)} {code} ({cr} credits)")

        print(f"\n  {color('Total Missing:', BOLD)} {total_missing_courses} course(s), {total_missing_credits} credits")
    else:
        print(section_bar("MISSING COURSES / REQUIREMENTS"))
        print(f"  {color('All required courses satisfied!', GREEN)}")

    print("=" * 50)

    # ── Graduation Roadmap ──
    roadmap = audit_result.get("roadmap")
    if roadmap and not roadmap["eligible"]:
        print_graduation_roadmap(roadmap)


def print_graduation_roadmap(roadmap):
    """Print the PATH TO GRADUATION section."""
    print(section_bar("PATH TO GRADUATION"))

    if roadmap["eligible"]:
        print(f"  {color('All graduation requirements met!', GREEN)}")
        return

    gap = roadmap["credit_gap"]
    est_sem = roadmap["estimated_semesters"]
    est_courses = roadmap["estimated_courses_left"]
    print(f"\n  {color('Summary:', BOLD)}")
    if gap > 0:
        print(f"    Credits still needed  : {color(str(gap), RED)}")
    if est_courses > 0:
        print(f"    Courses to complete   : {est_courses}")
    print(f"    Estimated semesters   : ~{est_sem} (at 15 credits/semester)")

    priority_colors = {
        "CRITICAL": RED,
        "HIGH": RED,
        "MEDIUM": YELLOW,
        "LOW": CYAN,
        "RECOMMENDED": GREEN,
    }

    print(f"\n  {color('Action Items:', BOLD)}")
    for i, step in enumerate(roadmap["steps"], 1):
        prio = step["priority"]
        prio_clr = priority_colors.get(prio, YELLOW)
        tag = color(f"[{prio}]", prio_clr)
        cat = color(step['category'], BOLD)

        print(f"\n    {i}. {tag} {cat}")
        print(f"       {step['action']}")
        if step.get("detail"):
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
    print("=" * 50)


# ─── Main CLI ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Level 3 — Audit & Graduation Eligibility Report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python level_3.py transcript.csv CSE
  python level_3.py transcript.csv BBA --concentration FIN
  python level_3.py transcripts/student_0065_BBA_FIN_top_student.csv BBA --concentration FIN
        """
    )
    parser.add_argument("transcript", help="Path to transcript CSV file")
    parser.add_argument("program", choices=["CSE", "BBA", "cse", "bba"],
                        help="Program: CSE or BBA")
    parser.add_argument("--concentration", "-c",
                        choices=["ACT", "FIN", "MKT", "MGT", "HRM", "MIS", "SCM", "ECO", "INB",
                                 "act", "fin", "mkt", "mgt", "hrm", "mis", "scm", "eco", "inb"],
                        help="BBA concentration/major area (required for BBA)")
    args = parser.parse_args()

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
    unrecognized = set(r.course_code for r in records if r.course_code not in ALL_COURSES)
    if unrecognized:
        print(header_bar(f"LEVEL 3 — AUDIT REPORT ({program})"))
        print(f"  Transcript File  : {os.path.basename(args.transcript)}")
        print(f"\n  {color('!!! FAKE TRANSCRIPT DETECTED !!!', RED)}")
        print(f"  Unrecognized Course Codes: {color(', '.join(unrecognized), RED)}")
        print(f"  This transcript contains courses that do not exist in the NSU database.")
        print(f"  {color('AUDIT ABORTED', RED)}")
        print(f"  {'-' * 46}\n")
        sys.exit(1)

    # Level 2: CGPA calculation (auto-detects waivers from transcript)
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

    # Print report
    print_level3_report(args.transcript, program, records, credits_attempted, credits_earned, cgpa_data, audit_result)


if __name__ == "__main__":
    main()
