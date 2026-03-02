#!/usr/bin/env python3
"""
NSU Audit Core — 2000 Unique Student Transcript Generator
Generates 2000 individual transcript CSV files in a 'transcripts/' directory,
each representing a different student with varied academic profiles.
"""

import csv
import os
import random
import sys
from engine.credit_engine import SEMESTERS
from engine.prerequisites import PREREQUISITES_CSE, PREREQUISITES_BBA

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from engine.course_db import *
for d in [CSE_MAJOR_CORE, CSE_CAPSTONE, CSE_SEPS_CORE, CSE_GED, CSE_GED_CHOICE_1, CSE_GED_CHOICE_2,
          CSE_GED_CHOICE_3, CSE_ELECTIVES_400, OPEN_ELECTIVES, BBA_SCHOOL_CORE, BBA_CORE, BBA_GED,
          BBA_GED_CHOICE_LANG, BBA_GED_CHOICE_HIS, BBA_GED_CHOICE_POL, BBA_GED_CHOICE_SOC,
          BBA_GED_CHOICE_SCI, BBA_GED_CHOICE_LAB, BBA_INTERNSHIP]:
    ALL_COURSES.update(d)
for conc_data in BBA_CONC_COURSES.values():
    ALL_COURSES.update(conc_data["required"])
    ALL_COURSES.update(conc_data["elective"])
ALL_COURSES["ENG102"] = ("Introduction to Composition", 3)
ALL_COURSES["MAT112"] = ("College Algebra", 0)
ALL_COURSES["BUS112"] = ("Intro to Business Mathematics", 3)

# SEMESTERS imported from engine.credit_engine


# ─── Student Profile Types ───────────────────────────────

PROFILES = [
    "top_student",        # CGPA 3.5+, all courses done, eligible
    "good_student",       # CGPA 2.5-3.5, most courses done
    "struggling",         # CGPA 1.5-2.5, many retakes, probation risk
    "early_stage",        # Freshman/sophomore, few courses
    "mid_stage",          # Junior, about half done
    "nearly_done",        # Senior, missing 1-3 courses
    "retake_heavy",       # Many retakes and Fs
    "transfer_student",   # Several T grades
    "withdrawn_heavy",    # Many W grades
    "probation",          # CGPA < 2.0
]


def grade_for_profile(profile, grade_counts=None):
    """Return a weighted random grade based on student profile.
    If grade_counts is provided, ensures no single passing grade (A through D) 
    appears more than 5 times."""
    
    if grade_counts is None:
        grade_counts = {}

    def get_raw_grade():
        if profile == "top_student":
            return random.choices(
                ["A", "A-", "B+", "B", "B-", "C+"],
                weights=[30, 25, 20, 15, 7, 3], k=1)[0]
        elif profile == "good_student":
            return random.choices(
                ["A", "A-", "B+", "B", "B-", "C+", "C", "C-"],
                weights=[10, 15, 20, 20, 15, 10, 7, 3], k=1)[0]
        elif profile == "struggling":
            return random.choices(
                ["B", "B-", "C+", "C", "C-", "D+", "D", "F"],
                weights=[10, 15, 15, 20, 15, 10, 10, 5], k=1)[0]
        elif profile == "retake_heavy":
            return random.choices(
                ["B", "B-", "C+", "C", "C-", "D+", "D", "F", "W"],
                weights=[5, 10, 10, 15, 15, 10, 10, 15, 10], k=1)[0]
        elif profile == "probation":
            return random.choices(
                ["B", "B-", "C+", "C", "C-", "D+", "D", "F", "I"],
                weights=[5, 5, 10, 15, 15, 15, 15, 15, 5], k=1)[0]
        elif profile == "withdrawn_heavy":
            return random.choices(
                ["A", "B+", "B", "C+", "C", "D", "F", "W"],
                weights=[8, 10, 12, 10, 10, 5, 5, 40], k=1)[0]
        elif profile == "transfer_student":
            return random.choices(
                ["A", "A-", "B+", "B", "C+", "C", "T"],
                weights=[12, 12, 15, 15, 10, 10, 26], k=1)[0]
        else:
            return random.choices(
                ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F", "W"],
                weights=[8, 8, 10, 12, 10, 10, 10, 8, 7, 7, 6, 4], k=1)[0]

    # Try up to 10 times to get a grade that hasn't hit the limit
    for _ in range(10):
        grade = get_raw_grade()
        if grade not in ("F", "W", "I", "T"):
            if grade_counts.get(grade, 0) < 5:
                # Grade limit not reached
                return grade
        else:
            return grade # Don't limit F, W, I, T
            
    # If we couldn't find one that hasn't hit the limit, just return the lowest valid passing grade or F as fallback
    fallback_grades = ["C-", "D+", "D", "F"]
    for fg in fallback_grades:
        if fg == "F" or grade_counts.get(fg, 0) < 5:
            return fg
    return "F"


def sort_rows(rows):
    """Sort transcript rows chronologically by semester, and randomly scatter within semester."""
    # Create a mapping for quick lookup
    sem_map = {sem: i for i, sem in enumerate(SEMESTERS)}
    
    # Randomly shuffle rows first so that stable sorting scrambles courses within the same semester
    random.shuffle(rows)
    
    # If a semester is not in the list (e.g. transfer), give it index -1
    return sorted(rows, key=lambda r: sem_map.get(r[4], -1))


def pick_semesters(n, start_idx=None):
    """Pick n sequential semesters starting from a random point."""
    if start_idx is None:
        start_idx = random.randint(0, max(0, len(SEMESTERS) - n))
    end = min(start_idx + n, len(SEMESTERS))
    return SEMESTERS[start_idx:end]


def get_eligible_courses(pool_codes, passed_set, prereq_map, credits_earned):
    """Filter a pool of course codes based on prerequisites and credits earned."""
    eligible = []
    for code in pool_codes:
        if code in passed_set:
            continue
        
        reqs = prereq_map.get(code, [])
        met = True
        for req in reqs:
            if req == "_SENIOR_":
                if credits_earned < 100:
                    met = False
                    break
            elif req not in passed_set:
                met = False
                break
        
        if met:
            # Special case for Labs: Prefer taking with theory or after
            # However, for simplicity here, we just ensure theory is passed or we could allow same-sem
            # Let's keep it simple: if theory is in passed_set, lab is eligible.
            if code.endswith("L"):
                theory = code[:-1]
                if theory not in passed_set:
                    # Allow same-semester theory+lab by not adding to eligible yet if theory not passed,
                    # but we'll handle same-semester selection in the main loop.
                    pass
            eligible.append(code)
    return eligible


def generate_cse_student(profile, student_id):
    """Generate a CSE student transcript strictly following prerequisites."""
    rows = []
    passed_courses = set()
    credits_earned = 0
    grade_counts = {}
    
    # ── Simulation Parameters ──
    # Determine progress based on profile
    if profile == "top_student":
        target_credits = 130
        pref_load = 5  # courses/sem
    elif profile == "good_student":
        target_credits = random.randint(100, 130)
        pref_load = random.randint(4, 5)
    elif profile == "nearly_done":
        target_credits = random.randint(115, 128)
        pref_load = 4
    elif profile == "mid_stage":
        target_credits = random.randint(50, 80)
        pref_load = random.randint(3, 4)
    elif profile == "early_stage":
        target_credits = random.randint(12, 40)
        pref_load = random.randint(3, 4)
    else:
        target_credits = random.randint(30, 110)
        pref_load = random.randint(2, 4)

    # ── Waivers ──
    # Simulating admission waivers (MAT112/116, ENG102)
    # These count as "passed" for prerequisite purposes and need to be in the transcript
    if random.random() < 0.6: 
         passed_courses.add("MAT112")
         rows.append(["MAT112", "College Algebra", "0", "T", SEMESTERS[0]])
    if random.random() < 0.4: 
         passed_courses.add("MAT116")
         rows.append(["MAT116", "Pre-Calculus", "0", "T", SEMESTERS[0]])
    if random.random() < 0.5: 
         passed_courses.add("ENG102")
         rows.append(["ENG102", "Introduction to Composition", "3", "T", SEMESTERS[0]])

    # ── Semester Loop ──
    n_semesters = random.randint(2, len(SEMESTERS))
    start_idx = random.randint(0, len(SEMESTERS) - n_semesters)
    avail_sems = SEMESTERS[start_idx : start_idx + n_semesters]
    
    # Define pools
    major_core = list(CSE_MAJOR_CORE.keys())
    seps_core = list(CSE_SEPS_CORE.keys())
    ged_req = list(CSE_GED.keys())
    capstone = list(CSE_CAPSTONE.keys())
    
    for sem in avail_sems:
        if credits_earned >= target_credits:
            break
            
        # 1. Identify all eligible courses from all pools
        all_eligible = []
        all_eligible += get_eligible_courses(major_core, passed_courses, PREREQUISITES_CSE, credits_earned)
        all_eligible += get_eligible_courses(seps_core, passed_courses, PREREQUISITES_CSE, credits_earned)
        all_eligible += get_eligible_courses(ged_req, passed_courses, PREREQUISITES_CSE, credits_earned)
        all_eligible += get_eligible_courses(capstone, passed_courses, PREREQUISITES_CSE, credits_earned)
        
        # Handle choice groups (one from each)
        for choice_pool in [CSE_GED_CHOICE_1, CSE_GED_CHOICE_2, CSE_GED_CHOICE_3]:
            if not any(c in passed_courses for c in choice_pool):
                all_eligible += get_eligible_courses(list(choice_pool.keys()), passed_courses, PREREQUISITES_CSE, credits_earned)

        # 2. Add Electives if eligible
        if credits_earned > 60:
            all_eligible += get_eligible_courses(list(CSE_ELECTIVES_400.keys()), passed_courses, PREREQUISITES_CSE, credits_earned)
            all_eligible += get_eligible_courses(list(OPEN_ELECTIVES.keys()), passed_courses, PREREQUISITES_CSE, credits_earned)

        if not all_eligible:
            continue
            
        # 3. Select load for this semester
        # Prioritize lower-level courses (shorter strings or specific prefixes usually)
        # Or just random sample from eligible
        current_load = min(len(all_eligible), pref_load + random.randint(-1, 1))
        if current_load <= 0: continue
        
        # Sort eligible to prioritize "foundational" (e.g. MAT120 before CSE311)
        # Simple heuristic: courses with more children in prereq map are higher priority
        priority_map = {c: 0 for c in all_eligible}
        for target, reqs in PREREQUISITES_CSE.items():
            for r in reqs:
                if r in priority_map: priority_map[r] += 1
        
        all_eligible.sort(key=lambda c: priority_map.get(c, 0), reverse=True)
        # Take some top ones and some random ones
        n_top = min(current_load, 2)
        taking = all_eligible[:n_top]
        if current_load > n_top:
            taking += random.sample(all_eligible[n_top:], current_load - n_top)

        # 4. Process the selected courses
        sem_passed = []
        for code in taking:
            if code in sem_passed:
                continue # Prevent accidental duplicate in same semester
                
            name, credits = ALL_COURSES[code]
            grade = grade_for_profile(profile, grade_counts)
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
            rows.append([code, name, str(credits), grade, sem])
            
            if grade not in ("F", "W", "I"):
                sem_passed.append(code)
                credits_earned += credits
                
                # If theory passed, allow lab in next sem (already covered by get_eligible)
                # If lab is in all_eligible and theory is also taken this sem, let's just allow it
                if not code.endswith("L") and code + "L" in ALL_COURSES and code + "L" in all_eligible and (code + "L") not in sem_passed:
                    if random.random() < 0.8: # Take lab with theory
                         l_code = code + "L"
                         l_name, l_credits = ALL_COURSES[l_code]
                         l_grade = grade_for_profile(profile, grade_counts)
                         grade_counts[l_grade] = grade_counts.get(l_grade, 0) + 1
                         rows.append([l_code, l_name, str(l_credits), l_grade, sem])
                         if l_grade not in ("F", "W", "I"):
                             sem_passed.append(l_code)
                             credits_earned += l_credits
                             
        # Sometimes intentionally do an unauthorized retake (retake a passed course) if struggling/retake_heavy
        if profile in ("struggling", "retake_heavy") and len(passed_courses) > 5 and random.random() < 0.10:
            # Pick a course already passed with a good grade
            possible_retakes = [r for r in rows if r[0] in passed_courses and r[3] in ("A", "A-", "B+", "B", "B-")]
            if possible_retakes:
                retake_course = random.choice(possible_retakes)
                code = retake_course[0]
                if code not in sem_passed: # Don't retake it the same semester we just passed it
                    name, credits = ALL_COURSES[code]
                    grade = grade_for_profile(profile, grade_counts)
                    grade_counts[grade] = grade_counts.get(grade, 0) + 1
                    rows.append([code, name, str(credits), grade, sem])
                    # No need to add to sem_passed or credits_earned because it's an unauthorized retake

        passed_courses.update(sem_passed)

    return sort_rows(rows)


def generate_bba_student(profile, student_id):
    """Generate a BBA student transcript."""
    rows = []
    passed_courses = set()
    credits_earned = 0
    concentration = random.choice(BBA_CONC_NAMES)
    grade_counts = {}
    
    # ── Simulation Parameters ──
    if profile == "top_student":
        target_credits = 124
        pref_load = 5
    elif profile == "good_student":
        target_credits = random.randint(100, 124)
        pref_load = random.randint(4, 5)
    elif profile == "nearly_done":
        target_credits = random.randint(110, 120)
        pref_load = 4
    elif profile == "mid_stage":
        target_credits = random.randint(50, 80)
        pref_load = random.randint(3, 4)
    elif profile == "early_stage":
        target_credits = random.randint(12, 40)
        pref_load = random.randint(3, 4)
    else:
        target_credits = random.randint(30, 100)
        pref_load = random.randint(2, 4)

    # ── Waivers ──
    if random.random() < 0.5: 
        passed_courses.add("BUS112")
        rows.append(["BUS112", "Intro to Business Mathematics", "3", "T", SEMESTERS[0]])
    if random.random() < 0.5: 
        passed_courses.add("ENG102")
        rows.append(["ENG102", "Introduction to Composition", "3", "T", SEMESTERS[0]])

    # ── Semester Loop ──
    n_semesters = random.randint(2, len(SEMESTERS))
    start_idx = random.randint(0, len(SEMESTERS) - n_semesters)
    avail_sems = SEMESTERS[start_idx : start_idx + n_semesters]
    
    # Pools
    school_core = list(BBA_SCHOOL_CORE.keys())
    bba_core = list(BBA_CORE.keys())
    ged_req = list(BBA_GED.keys())
    conc_data = BBA_CONC_COURSES[concentration]
    conc_req = list(conc_data["required"].keys())
    conc_elec = list(conc_data["elective"].keys())
    
    for sem in avail_sems:
        if credits_earned >= target_credits:
            break
            
        all_eligible = []
        all_eligible += get_eligible_courses(school_core, passed_courses, PREREQUISITES_BBA, credits_earned)
        all_eligible += get_eligible_courses(bba_core, passed_courses, PREREQUISITES_BBA, credits_earned)
        all_eligible += get_eligible_courses(ged_req, passed_courses, PREREQUISITES_BBA, credits_earned)
        
        # GED Choices
        for choice_pool in [BBA_GED_CHOICE_LANG, BBA_GED_CHOICE_POL, BBA_GED_CHOICE_SOC, BBA_GED_CHOICE_SCI]:
             if not any(c in passed_courses for c in choice_pool):
                 all_eligible += get_eligible_courses(list(choice_pool.keys()), passed_courses, PREREQUISITES_BBA, credits_earned)
        
        # History needs 2
        his_passed = [c for c in BBA_GED_CHOICE_HIS if c in passed_courses]
        if len(his_passed) < 2:
             all_eligible += get_eligible_courses(list(BBA_GED_CHOICE_HIS.keys()), passed_courses, PREREQUISITES_BBA, credits_earned)

        # Concentration
        if credits_earned >= 30: # Realistic threshold to start major
            all_eligible += get_eligible_courses(conc_req, passed_courses, PREREQUISITES_BBA, credits_earned)
            all_eligible += get_eligible_courses(conc_elec, passed_courses, PREREQUISITES_BBA, credits_earned)

        if not all_eligible:
            continue

        current_load = min(len(all_eligible), pref_load + random.randint(-1, 1))
        if current_load <= 0: continue
        
        # Prioritize foundational
        priority_map = {c: 0 for c in all_eligible}
        for target, reqs in PREREQUISITES_BBA.items():
            for r in reqs:
                if r in priority_map: priority_map[r] += 1
        
        all_eligible.sort(key=lambda c: priority_map.get(c, 0), reverse=True)
        taking = random.sample(all_eligible[:min(len(all_eligible), current_load+2)], current_load)

        # 4. Process the selected courses
        sem_passed = []
        for code in taking:
            if code in sem_passed:
                continue # Prevent accidental duplicate in same semester
                
            name, credits = ALL_COURSES[code]
            grade = grade_for_profile(profile, grade_counts)
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
            rows.append([code, name, str(credits), grade, sem])
            if grade not in ("F", "W", "I"):
                sem_passed.append(code)
                credits_earned += credits
                
                # Matching Lab
                if code in BBA_GED_CHOICE_SCI and code + "L" in ALL_COURSES and (code + "L") not in sem_passed:
                    if random.random() < 0.7:
                        l_code = code + "L"
                        l_name, l_credits = ALL_COURSES[l_code]
                        l_grade = grade_for_profile(profile, grade_counts)
                        grade_counts[l_grade] = grade_counts.get(l_grade, 0) + 1
                        rows.append([l_code, l_name, str(l_credits), l_grade, sem])
                        if l_grade not in ("F", "W", "I"):
                            sem_passed.append(l_code)
                            credits_earned += l_credits
                            
        # Sometimes intentionally do an unauthorized retake (retake a passed course) if struggling/retake_heavy
        if profile in ("struggling", "retake_heavy") and len(passed_courses) > 5 and random.random() < 0.10:
            # Pick a course already passed with a good grade
            possible_retakes = [r for r in rows if r[0] in passed_courses and r[3] in ("A", "A-", "B+", "B", "B-")]
            if possible_retakes:
                retake_course = random.choice(possible_retakes)
                code = retake_course[0]
                if code not in sem_passed: # Don't retake it the same semester we just passed it
                    name, credits = ALL_COURSES[code]
                    grade = grade_for_profile(profile, grade_counts)
                    grade_counts[grade] = grade_counts.get(grade, 0) + 1
                    rows.append([code, name, str(credits), grade, sem])
                    # No need to add to sem_passed or credits_earned because it's an unauthorized retake

        passed_courses.update(sem_passed)

    # Internship
    if credits_earned >= 100 and profile in ("top_student", "good_student", "nearly_done"):
        grade = grade_for_profile(profile, grade_counts)
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
        rows.append(["BUS498", "Internship", "4", grade, avail_sems[-1]])

    return sort_rows(rows), concentration


def generate_dept_change_student(student_id, current_program, previous_program):
    """Generate a student who switched from previous_program to current_program, following prerequisites."""
    rows = []
    passed_courses = set()
    credits_earned = 0
    concentration = None
    grade_counts = {}
    
    # Selection of semesters
    n_semesters = random.randint(8, 12)
    start_idx = random.randint(0, len(SEMESTERS) - n_semesters)
    avail_sems = SEMESTERS[start_idx : start_idx + n_semesters]
    
    # Split: first 3-4 semesters in old program, rest in new
    switch_sem_idx = random.randint(3, 4)
    
    # Pools
    if previous_program == "CSE":
        old_pool = list(CSE_SEPS_CORE.keys()) + list(CSE_MAJOR_CORE.keys()) + list(CSE_GED.keys())
        old_prereqs = PREREQUISITES_CSE
    else:
        old_pool = list(BBA_SCHOOL_CORE.keys()) + list(BBA_CORE.keys()) + list(BBA_GED.keys())
        old_prereqs = PREREQUISITES_BBA
        
    if current_program == "CSE":
        new_pool = list(CSE_SEPS_CORE.keys()) + list(CSE_MAJOR_CORE.keys()) + list(CSE_GED.keys()) + list(CSE_CAPSTONE.keys())
        new_prereqs = PREREQUISITES_CSE
    else:
        concentration = random.choice(BBA_CONC_NAMES)
        new_pool = list(BBA_SCHOOL_CORE.keys()) + list(BBA_CORE.keys()) + list(BBA_GED.keys())
        conc_data = BBA_CONC_COURSES[concentration]
        new_pool += list(conc_data["required"].keys()) + list(conc_data["elective"].keys())
        new_prereqs = PREREQUISITES_BBA

    # Loop through semesters
    for i, sem in enumerate(avail_sems):
        is_old = i < switch_sem_idx
        pool = old_pool if is_old else new_pool
        p_map = old_prereqs if is_old else new_prereqs
        
        # Determine eligible
        eligible = get_eligible_courses(pool, passed_courses, p_map, credits_earned)
        if not eligible: continue
        
        # Load
        load = random.randint(3, 5)
        taking = random.sample(eligible, min(len(eligible), load))
        
        sem_passed = []
        for code in taking:
            if code in sem_passed:
                continue
                
            name, credits = ALL_COURSES[code]
            grade = grade_for_profile("good_student" if is_old else "mid_stage", grade_counts)
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
            rows.append([code, name, str(credits), grade, sem])
            if grade not in ("F", "W", "I"):
                sem_passed.append(code)
                credits_earned += credits
                
                # Lab logic
                if code + "L" in ALL_COURSES and code + "L" in eligible and (code + "L") not in sem_passed:
                    l_code = code + "L"
                    l_name, l_credits = ALL_COURSES[l_code]
                    l_grade = grade_for_profile("good_student", grade_counts)
                    grade_counts[l_grade] = grade_counts.get(l_grade, 0) + 1
                    rows.append([l_code, l_name, str(l_credits), l_grade, sem])
                    sem_passed.append(l_code)
                    credits_earned += l_credits

        passed_courses.update(sem_passed)
            
    return sort_rows(rows), concentration


def generate_all():
    random.seed(2024)
    output_dir = os.path.join(os.path.dirname(__file__) or ".", "transcripts")
    os.makedirs(output_dir, exist_ok=True)

    # Clean old transcripts
    import glob
    for old_file in glob.glob(os.path.join(output_dir, "*.csv")):
        try:
            os.remove(old_file)
        except PermissionError:
            pass # Skip locked files

    # Profile distribution across 2000 students
    profile_weights = {
        "top_student": 200,
        "good_student": 350,
        "struggling": 200,
        "early_stage": 150,
        "mid_stage": 200,
        "nearly_done": 250,
        "retake_heavy": 150,
        "transfer_student": 100,
        "withdrawn_heavy": 100,
        "probation": 200,
        "dept_change": 100,
    }

    students = []
    for profile, count in profile_weights.items():
        students.extend([profile] * count)
    random.shuffle(students)

    # Stats tracking
    stats = {
        "total": 0, "cse": 0, "bba": 0,
        "eligible_count": 0,
        "probation_count": 0,
        "profile_counts": {p: 0 for p in PROFILES + ["dept_change"]},
        "total_rows": 0,
        "retake_rows": 0,
        "w_rows": 0, "f_rows": 0, "t_rows": 0, "i_rows": 0,
    }

    for i, profile in enumerate(students):
        student_id = i + 1
        program = random.choices(["CSE", "BBA"], weights=[65, 35], k=1)[0]
        concentration = None
        ex_major = None

        if profile == "dept_change":
            ex_major = "BBA" if program == "CSE" else "CSE"
            rows, concentration = generate_dept_change_student(student_id, program, ex_major)
        elif program == "CSE":
            rows = generate_cse_student(profile, student_id)
            stats["cse"] += 1
        else:
            rows, concentration = generate_bba_student(profile, student_id)
            stats["bba"] += 1

        if profile == "dept_change":
            if program == "CSE": stats["cse"] += 1
            else: stats["bba"] += 1

        stats["profile_counts"][profile] += 1
        stats["total"] += 1

        # Count stats
        course_attempts = {}
        for row in rows:
            code, name, cr, grade, sem = row
            stats["total_rows"] += 1
            if grade == "W": stats["w_rows"] += 1
            if grade == "F": stats["f_rows"] += 1
            if grade == "T": stats["t_rows"] += 1
            if grade == "I": stats["i_rows"] += 1
            course_attempts.setdefault(code, []).append(grade)

        for code, attempts in course_attempts.items():
            if len(attempts) > 1:
                stats["retake_rows"] += len(attempts)

        # Write CSV — encode concentration and department change in filenames
        parts = [f"student_{student_id:04d}", program]
        if concentration:
            parts.append(concentration)
        if ex_major:
            parts.append(f"ex_{ex_major}")
        parts.append(profile)
        
        filename = "_".join(parts) + ".csv"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["course_code", "course_name", "credits", "grade", "semester"])
            for row in rows:
                writer.writerow(row)

    return stats, output_dir


def print_summary(stats, output_dir):
    print("=" * 60)
    print("  NSU 2000 UNIQUE TRANSCRIPT GENERATOR - SUMMARY")
    print("=" * 60)
    print(f"  Output directory     : {output_dir}")
    print(f"  Total transcripts    : {stats['total']}")
    print(f"  CSE students         : {stats['cse']}")
    print(f"  BBA students         : {stats['bba']}")
    print(f"  Total course rows    : {stats['total_rows']}")
    print(f"  Retake rows          : {stats['retake_rows']}")
    print(f"  W (Withdrawn) rows   : {stats['w_rows']}")
    print(f"  F (Failed) rows      : {stats['f_rows']}")
    print(f"  T (Transfer) rows    : {stats['t_rows']}")
    print(f"  I (Incomplete) rows  : {stats['i_rows']}")
    print()
    print("  Profile Distribution:")
    for profile, count in stats["profile_counts"].items():
        bar = "#" * (count // 10)
        print(f"    {profile:20s}: {count:4d}  {bar}")
    print("=" * 60)


if __name__ == "__main__":
    stats, output_dir = generate_all()
    print_summary(stats, output_dir)
