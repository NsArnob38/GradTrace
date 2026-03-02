#!/usr/bin/env python3
"""
Level 1 — Credit Tallying Report
Calculates attempted and earned credits from a transcript CSV.

Usage:
    python level_1.py <transcript.csv>
"""

import sys
import os
from engine.credit_engine import process_transcript

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

def header_bar(title, width=50):
    return f"\n{'=' * width}\n  {title}\n{'=' * width}"

def color(text, clr):
    return f"{clr}{text}{RESET}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python level_1.py <transcript.csv>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)

    # Level 1 Processing
    records, attempted, earned = process_transcript(filepath)

    from engine.course_db import ALL_COURSES
    unrecognized = set(r.course_code for r in records if r.course_code not in ALL_COURSES)
    if unrecognized:
        print(header_bar("LEVEL 1 — CREDIT TALLY REPORT"))
        print(f"  Transcript File  : {os.path.basename(filepath)}")
        print(f"\n  {color('!!! FAKE TRANSCRIPT DETECTED !!!', RED)}")
        print(f"  Unrecognized Course Codes: {color(', '.join(unrecognized), RED)}")
        print(f"  This transcript contains courses that do not exist in the NSU database.")
        print(f"  {color('AUDIT ABORTED', RED)}")
        print(f"  {'-' * 46}\n")
        sys.exit(1)

    # Calculate Dismissal Point
    from engine.credit_engine import SEMESTERS, resolve_retakes
    from engine.cgpa_engine import compute_cgpa
    import copy
    
    sem_map = {sem: i for i, sem in enumerate(SEMESTERS)}
    transcript_sems = sorted(
        list(set(r.semester for r in records if r.semester in sem_map)), 
        key=lambda s: sem_map[s]
    )

    consecutive_p = 0
    dismissal_sem = None
    cutoff_records = []
    
    for current_sem in transcript_sems:
        if dismissal_sem:
            break
            
        cutoff_idx = sem_map[current_sem]
        subset = [copy.copy(r) for r in records if r.semester in sem_map and sem_map[r.semester] <= cutoff_idx]
        resolved_subset = resolve_retakes(subset)
        snap_cgpa, _, _ = compute_cgpa(resolved_subset)
        
        # Add these records to our safe cutoff
        cutoff_records.extend([r for r in records if r.semester == current_sem])
        
        if snap_cgpa < 2.0:
            consecutive_p += 1
            if consecutive_p >= 3:
                dismissal_sem = current_sem
        else:
            consecutive_p = 0

    # If dismissed, recalculate earned credits up to the cutoff
    if dismissal_sem:
        filtered_earned = sum(r.credits for r in cutoff_records if r.status in ("BEST", "WAIVED") and r.grade not in ("F", "W", "I"))
        earned = filtered_earned
        records = cutoff_records

    # Report
    print(header_bar("LEVEL 1 — CREDIT TALLY REPORT"))
    print(f"  Transcript File  : {os.path.basename(filepath)}")
    print(f"  Credits Attempted: {BOLD}{attempted}{RESET}")
    print(f"  Credits Earned   : {BOLD}{GREEN}{earned}{RESET}")

    print(f"\n{'CODE':<10} {'COURSE NAME':<30} {'CR':<4} {'GRADE':<10} {'STATUS'}")
    print("-" * 75)
    for r in records:
        status_color = GREEN if r.status in ("BEST", "WAIVED") else ""
        if r.status in ("RETAKE-IGNORED", "UNAUTHORIZED-RETAKE", "WITHDRAWN"):
            status_color = Style.DIM if r.status == "RETAKE-IGNORED" else YELLOW
        elif r.status in ("FAILED", "REJECTED-TRANSFER"): 
            status_color = RED

        print(f"{r.course_code:<10} {r.course_name[:28]:<30} {r.credits:<4} {r.grade:<10} {status_color}{r.status}{RESET}")
    print("-" * 75)
    print(f"  Total Credits Earned: {BOLD}{GREEN}{earned}{RESET}")
    print("=" * 75 + "\n")

    if dismissal_sem:
        print(header_bar("ACADEMIC STANDING EXCEPTION", width=50))
        print(f"  {color('Transcript Halt: Student triggered academic dismissal.', RED)}")
        print(f"  {color('Dismissal reached in: ' + dismissal_sem, RED)}")
        print(f"  {color('Contact Academic Advising immediately.', RED)}")
        print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
