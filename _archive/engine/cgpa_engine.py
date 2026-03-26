"""
Level 2 — CGPA Calculation Engine
Computes CGPA from transcript records, handles waiver logic,
and determines academic standing.
"""

# Grade-to-GPA point mapping (NSU 4.0 scale)
GRADE_POINTS = {
    "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0,
    "F": 0.0,
    "I": 0.0,  # Incomplete treated as F
}

# Grades excluded from GPA calculation entirely
GPA_EXCLUDED_GRADES = {"W", "T"}


def grade_to_points(grade):
    """Convert a letter grade to GPA points. Returns None if excluded."""
    if grade in GPA_EXCLUDED_GRADES:
        return None
    return GRADE_POINTS.get(grade, None)


def compute_cgpa(records):
    """
    Compute CGPA using only BEST-grade attempts.
    - Excludes W, T grades entirely
    - Excludes 0-credit courses
    - I (Incomplete) treated as F (0.0)
    - Only records with status 'BEST' or 'FAILED' (when no better attempt exists) count

    Returns (cgpa, total_quality_points, total_gpa_credits)
    """
    total_quality_points = 0.0
    total_gpa_credits = 0

    for r in records:
        # Only count the BEST attempt or a standalone FAILED attempt
        if r.status not in ("BEST", "FAILED"):
            continue

        # Skip 0-credit courses
        if r.credits == 0:
            continue

        # Skip GPA-excluded grades
        points = grade_to_points(r.grade)
        if points is None:
            continue

        total_quality_points += points * r.credits
        total_gpa_credits += r.credits

    if total_gpa_credits == 0:
        return 0.0, 0.0, 0

    cgpa = total_quality_points / total_gpa_credits
    # Strict NSU Truncation: 1.996 -> 1.99 (Do not round up)
    truncated_cgpa = int(cgpa * 100) / 100.0
    return truncated_cgpa, round(total_quality_points, 2), total_gpa_credits


def compute_major_cgpa(records, major_course_codes):
    """
    Compute CGPA for only the major/core courses.
    Same rules as compute_cgpa but filtered to the given course codes.
    """
    major_codes = set(major_course_codes)
    total_qp = 0.0
    total_cr = 0

    for r in records:
        if r.course_code not in major_codes:
            continue
        if r.status not in ("BEST", "FAILED"):
            continue
        if r.credits == 0:
            continue
        points = grade_to_points(r.grade)
        if points is None:
            continue
        total_qp += points * r.credits
        total_cr += r.credits

    if total_cr == 0:
        return 0.0
        
    major_cgpa = total_qp / total_cr
    # Strict NSU Truncation
    return int(major_cgpa * 100) / 100.0


def determine_standing(cgpa):
    """Determine academic standing based on overall CGPA."""
    if cgpa < 2.0:
        return "PROBATION"
    return "NORMAL"


def calculate_probation_history(records):
    """
    Calculate the probation phase (P1, P2, etc.) based on consecutive semesters < 2.0 CGPA.
    NSU Policy: 2 consecutive semesters allowed; dismissal in the 3rd if still < 2.0.
    """
    from engine.credit_engine import SEMESTERS, resolve_retakes
    import copy

    sem_map = {sem: i for i, sem in enumerate(SEMESTERS)}
    
    # Filter and sort unique semesters present in the transcript
    transcript_sems = sorted(list(set(r.semester for r in records if r.semester in sem_map)), 
                            key=lambda s: sem_map[s])
    
    if not transcript_sems:
        return "NORMAL", 0

    consecutive_p = 0
    for current_sem in transcript_sems:
        cutoff_idx = sem_map[current_sem]
        # Get attempts up to this semester
        subset = [copy.copy(r) for r in records if r.semester in sem_map and sem_map[r.semester] <= cutoff_idx]
        
        # Resolve retakes based on knowledge UP TO this semester
        resolved_subset = resolve_retakes(subset)
        
        # Compute CGPA for this snapshot
        snap_cgpa, _, _ = compute_cgpa(resolved_subset)
        
        if snap_cgpa < 2.0:
            consecutive_p += 1
        else:
            consecutive_p = 0

    # Map count to label
    if consecutive_p == 0:
        return "NORMAL", 0
    elif consecutive_p == 1:
        return "PROBATION (P1)", 1
    elif consecutive_p == 2:
        return "PROBATION (P2)", 2
    else:
        return "DISMISSAL", consecutive_p


def check_waivers_cse(records):
    """
    CSE waiver logic for ENG102.
    ENG102 (3-credit): waived if scored >=60% on English admission test.
    Returns dict with waiver info and credit reduction.
    """
    waivers = {"ENG102": False}
    credit_reduction = 0
    for r in records:
        if r.course_code == "ENG102":
            if r.grade == "T":
                waivers["ENG102"] = True
                credit_reduction += 3  # ENG102 is 3 credits
            elif r.status in ("BEST", "WAIVED") and r.grade not in ("F", "I", "W"):
                waivers["ENG102"] = True  # Passed, so satisfied
    return waivers, credit_reduction


def check_waivers_bba(records):
    """
    BBA waiver logic for ENG102 and BUS112.
    ENG102 (3-credit): waived if >=60% English admission test.
    BUS112 (3-credit): waived if >=60% Math admission test.
    Returns dict with waiver info and credit adjustment.
    """
    waivers = {"ENG102": False, "BUS112": False}
    credit_reduction = 0

    for r in records:
        if r.course_code == "ENG102":
            if r.grade == "T":
                waivers["ENG102"] = True
                credit_reduction += 3
            elif r.status in ("BEST", "WAIVED") and r.grade not in ("F", "I", "W"):
                waivers["ENG102"] = True
        if r.course_code == "BUS112":
            if r.grade == "T":
                waivers["BUS112"] = True
                credit_reduction += 3
            elif r.status in ("BEST",) and r.grade not in ("F", "I", "W"):
                waivers["BUS112"] = True  # Passed normally

    return waivers, credit_reduction


def check_waivers_from_input(program, user_waivers):
    """
    Accept user-provided waiver dict and compute credit reduction.
    user_waivers: dict like {"ENG102": True, "BUS112": False}
    """
    credit_reduction = 0
    if program.upper() == "CSE":
        if user_waivers.get("ENG102", False):
            credit_reduction += 3
    else:
        if user_waivers.get("ENG102", False):
            credit_reduction += 3
        if user_waivers.get("BUS112", False):
            credit_reduction += 3
    return user_waivers, credit_reduction


def process_cgpa(records, program="CSE", user_waivers=None):
    """
    Full Level 2 pipeline.
    Returns dict with: cgpa, quality_points, gpa_credits, standing, waivers, credit_reduction, probation_count
    If user_waivers is provided, uses those instead of scanning transcript.
    """
    cgpa, qp, gc = compute_cgpa(records)
    standing, p_count = calculate_probation_history(records)

    if user_waivers is not None:
        waivers, credit_reduction = check_waivers_from_input(program, user_waivers)
    elif program.upper() == "CSE":
        waivers, credit_reduction = check_waivers_cse(records)
    else:
        waivers, credit_reduction = check_waivers_bba(records)

    return {
        "cgpa": cgpa,
        "quality_points": qp,
        "gpa_credits": gc,
        "standing": standing,
        "probation_count": p_count,
        "waivers": waivers,
        "credit_reduction": credit_reduction,
    }
