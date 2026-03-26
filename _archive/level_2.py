#!/usr/bin/env python3
"""
Level 2 — CGPA Calculation & Standing Report
Computes cumulative GPA, determines academic standing, and checks waiver eligibility.

Usage:
    python level_2.py <transcript.csv> <program>

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
from engine.cgpa_engine import process_cgpa, GRADE_POINTS, compute_major_cgpa

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


def grade_color(grade):
    if grade in ("A", "A-", "B+", "B", "B-"):
        return color(grade, GREEN)
    elif grade in ("C+", "C", "C-", "D+", "D"):
        return color(grade, YELLOW)
    elif grade in ("F", "I"):
        return color(grade, RED)
    elif grade == "W":
        return color(grade, YELLOW)
    elif grade == "T":
        return color(grade, CYAN)
    return grade


# ─── Report ──────────────────────────────────────────────

def print_level2_report(filepath, program, records, credits_attempted, credits_earned, cgpa_data):
    """Print the Level 2 CGPA & Standing report."""
    cgpa = cgpa_data["cgpa"]
    standing = cgpa_data["standing"]
    qp = cgpa_data["quality_points"]
    gc = cgpa_data["gpa_credits"]
    waivers = cgpa_data["waivers"]
    credit_reduction = cgpa_data["credit_reduction"]

    print(header_bar(f"LEVEL 2 — CGPA & STANDING REPORT ({program})"))
    print(f"  Transcript File  : {os.path.basename(filepath)}")
    print(f"  Program          : {program}")
    print(f"  Credits Attempted: {credits_attempted}")
    print(f"  Credits Earned   : {credits_earned}")

    # CGPA breakdown
    print(section_bar("CGPA CALCULATION"))
    print(f"  GPA Credits (denominator) : {gc}")
    print(f"  Quality Points (numerator): {qp:.2f}")
    cgpa_str = f"{cgpa:.2f}"
    if cgpa >= 2.0:
        print(f"  Cumulative GPA            : {color(cgpa_str, GREEN)} / 4.00")
    else:
        print(f"  Cumulative GPA            : {color(cgpa_str, RED)} / 4.00")

    # Standing
    if "PROBATION" in standing or "DISMISSAL" in standing:
        print(f"  Academic Standing         : {color(standing, RED)}")
    else:
        print(f"  Academic Standing         : {color('NORMAL', GREEN)}")

    # Semester-by-semester breakdown (replacing the flat list)
    print(section_bar("SEMESTER-BY-SEMESTER PROGRESSION"))
    from engine.credit_engine import SEMESTERS, resolve_retakes
    from engine.cgpa_engine import compute_cgpa
    import copy

    sem_map = {sem: i for i, sem in enumerate(SEMESTERS)}
    transcript_sems = sorted(
        list(set(r.semester for r in records if r.semester in sem_map)), 
        key=lambda s: sem_map[s]
    )

    consecutive_p = 0
    dismissed = False

    for current_sem in transcript_sems:
        if dismissed:
            break

        # Get records up to and including strictly this semester ONLY
        cutoff_idx = sem_map[current_sem]
        subset = [copy.copy(r) for r in records if r.semester in sem_map and sem_map[r.semester] <= cutoff_idx]
        
        # Calculate standing and cumulative CGPA specifically for this snapshot
        resolved_subset = resolve_retakes(subset)
        snap_cgpa, _, snap_credits = compute_cgpa(resolved_subset)
        
        if snap_cgpa < 2.0:
            consecutive_p += 1
            if consecutive_p == 1:
                snap_standing = color("PROBATION (P1)", YELLOW)
            elif consecutive_p == 2:
                snap_standing = color("PROBATION (P2)", RED)
            else:
                snap_standing = color("DISMISSAL", RED)
                dismissed = True
        else:
            consecutive_p = 0
            snap_standing = color("NORMAL", GREEN)

        print(header_bar(f"SEMESTER: {current_sem}", width=60))
        
        # Determine courses specifically taken THIS semester
        sem_records = [r for r in records if r.semester == current_sem]
        
        headers = ["Code", "Course Name", "Cr", "Grade", "GP", "QP"]
        raw_rows = []
        colored_rows = []
        
        for r in sem_records:
            # We display all courses taken, even if not 'BEST' (like a real transcript would)
            gp = GRADE_POINTS.get(r.grade, 0.0)
            qp_val = gp * r.credits if r.grade not in ("W", "I", "T") else 0.0
            
            gp_str = f"{gp:.1f}" if r.grade not in ("W", "T") else "-"
            qp_str = f"{qp_val:.1f}" if r.grade not in ("W", "T") else "-"
            
            raw_rows.append([r.course_code, r.course_name[:28], str(r.credits),
                             r.grade, gp_str, qp_str])
            colored_rows.append([r.course_code, r.course_name[:28], str(r.credits),
                                 grade_color(r.grade), gp_str, qp_str])

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
                padding = w - 1 - raw_len
                cells.append(f" {v}{' ' * max(0, padding)}")
            return "|" + "|".join(cells) + "|"

        print(sep)
        print(fmt_row(headers, headers))
        print(sep)
        for i, row in enumerate(colored_rows):
            print(fmt_row(row, raw_rows[i]))
        print(sep)
        print(f"  Snapshot ->  Cum. Credits: {snap_credits}   Cum. CGPA: {snap_cgpa:.2f}   Standing: {snap_standing}")
        print()

    # Academic Standing Detail
    if dismissed:
        print(section_bar("ACADEMIC STANDING"))
        print(f"  Status: {color('DISMISSAL', RED)}")
        print(f"  {color('Transcript Halt: Student has been academically dismissed.', RED)}")
        print(f"  {color('Action Required: Contact Academic Advising immediately.', RED)}")
    elif "PROBATION" in standing:
        print(section_bar("ACADEMIC STANDING"))
        print(f"  Status: {color(standing, RED)}")
        if "P2" in standing:
            print(f"  {color('Warning: This is your LAST semester on probation before dismissal.', YELLOW)}")

    # Waivers
    print(section_bar("WAIVER STATUS"))
    for course, waived in waivers.items():
        if waived:
            print(f"  {course}: {color('WAIVED', CYAN)}")
        else:
            print(f"  {course}: {color('NOT WAIVED', YELLOW)}")
    if credit_reduction > 0:
        print(f"\n  Credit Reduction from Waivers: {credit_reduction} credits")

    # Grade distribution
    print(section_bar("GRADE DISTRIBUTION"))
    grade_dist = {}
    for r in records:
        if r.status == "BEST" and r.credits > 0 and r.grade not in ("W", "T"):
            grade_dist[r.grade] = grade_dist.get(r.grade, 0) + 1
    grade_order = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F", "I"]
    for g in grade_order:
        if g in grade_dist:
            bar = "█" * grade_dist[g]
            print(f"  {grade_color(g):10s}: {grade_dist[g]:3d}  {bar}")

    print("\n" + "=" * 50)


WAIVER_COURSE_INFO = {
    "ENG102": ("Introduction to Composition", 3),
    "MAT112": ("College Algebra", 0),
    "BUS112": ("Intro to Business Mathematics", 3),
}


def ask_waivers(program, records):
    """Ask the user interactively whether each waiverable course is waived.
    Skips courses already present in the transcript.
    Returns (all_waivers, new_waivers) — new_waivers only has freshly waived courses."""
    print(section_bar("WAIVER INPUT"))
    waivers = {}
    new_waivers = {}
    existing_codes = {r.course_code for r in records}

    if program == "CSE":
        waiver_codes = ["ENG102", "MAT112"]
    else:  # BBA
        waiver_codes = ["ENG102", "BUS112"]

    courses_to_ask = []
    for code in waiver_codes:
        if code in existing_codes:
            print(f"  {code}: {color('Already in transcript', CYAN)} (skipped)")
            waivers[code] = True  # already satisfied
        else:
            name, cr = WAIVER_COURSE_INFO[code]
            courses_to_ask.append((code, f"{name} ({cr}cr)"))

    for code, desc in courses_to_ask:
        while True:
            answer = input(f"  Is {code} ({desc}) waived? (y/n): ").strip().lower()
            if answer in ("y", "yes"):
                waivers[code] = True
                new_waivers[code] = True
                break
            elif answer in ("n", "no"):
                waivers[code] = False
                break
            else:
                print("    Please enter 'y' or 'n'.")

    return waivers, new_waivers


def save_waivers_to_csv(filepath, waivers):
    """Append waived courses as T-grade rows to the transcript CSV."""
    import csv
    rows_to_add = []
    for code, waived in waivers.items():
        if waived and code in WAIVER_COURSE_INFO:
            name, cr = WAIVER_COURSE_INFO[code]
            rows_to_add.append([code, name, str(cr), "T", "waiver"])

    if rows_to_add:
        with open(filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for row in rows_to_add:
                writer.writerow(row)
        print(f"\n  {color('✓', GREEN)} Saved {len(rows_to_add)} waiver(s) to {os.path.basename(filepath)}")


# ─── Main CLI ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Level 2 — CGPA Calculation & Standing Report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python level_2.py transcript.csv CSE
  python level_2.py transcripts/student_0005_CSE_top_student.csv CSE
        """
    )
    parser.add_argument("transcript", help="Path to transcript CSV file")
    parser.add_argument("program", choices=["CSE", "BBA", "cse", "bba"],
                        help="Program: CSE or BBA")
    args = parser.parse_args()

    if not os.path.isfile(args.transcript):
        print(color(f"Error: File '{args.transcript}' not found.", RED))
        sys.exit(1)

    program = args.program.upper()

    # Level 1: Credit tallying (prerequisite)
    records, credits_attempted, credits_earned = process_transcript(args.transcript)

    from engine.course_db import ALL_COURSES
    unrecognized = set(r.course_code for r in records if r.course_code not in ALL_COURSES)
    if unrecognized:
        print(header_bar(f"LEVEL 2 — CGPA & STANDING REPORT ({program})"))
        print(f"  Transcript File  : {os.path.basename(args.transcript)}")
        print(f"\n  {color('!!! FAKE TRANSCRIPT DETECTED !!!', RED)}")
        print(f"  Unrecognized Course Codes: {color(', '.join(unrecognized), RED)}")
        print(f"  This transcript contains courses that do not exist in the NSU database.")
        print(f"  {color('AUDIT ABORTED', RED)}")
        print(f"  {'-' * 46}\n")
        sys.exit(1)

    # Ask user about waivers (skips if already in transcript)
    user_waivers, new_waivers = ask_waivers(program, records)

    # Save only newly waived courses to CSV
    if new_waivers:
        save_waivers_to_csv(args.transcript, new_waivers)
        # Re-read transcript with updated waivers
        records, credits_attempted, credits_earned = process_transcript(args.transcript)

    # Level 2: CGPA calculation (with user-provided waivers)
    cgpa_data = process_cgpa(records, program, user_waivers=user_waivers)

    # Print report
    print_level2_report(args.transcript, program, records, credits_attempted, credits_earned, cgpa_data)


if __name__ == "__main__":
    main()

