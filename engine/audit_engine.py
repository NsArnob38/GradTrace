"""
Level 3 — Audit / Deficiency Reporting Engine
Compares passed courses against program requirements,
identifies remaining courses, and determines graduation eligibility.

Current curriculum: Post-Fall 2014 (130 credits for both CSE and BBA)
"""

from engine.cgpa_engine import compute_major_cgpa
from engine.credit_engine import SEMESTERS

# ─────────────────────────────────────────────────────
# CSE PROGRAM REQUIREMENTS (130 credits)
# ─────────────────────────────────────────────────────

# CSE Major Core (42 credits)
CSE_MAJOR_CORE = {
    "CSE173": 3,                              # Discrete Mathematics
    "CSE215": 3, "CSE215L": 1,                # Programming Language II (OOP)
    "CSE225": 3, "CSE225L": 1,                # Data Structures & Algorithms
    "CSE231": 3, "CSE231L": 1,                # Digital Logic Design
    "CSE299": 1,                              # Junior Design Project
    "CSE311": 3, "CSE311L": 1,                # Database Management Systems
    "CSE323": 3,                              # Operating Systems Design
    "CSE327": 3,                              # Software Engineering
    "CSE331": 3, "CSE331L": 1,                # Microprocessor Interfacing
    "CSE332": 3,                              # Computer Organization & Architecture
    "CSE373": 3,                              # Design & Analysis of Algorithms
    "CSE425": 3,                              # Concepts of Programming Languages
    "EEE141": 3, "EEE141L": 1,                # Electrical Circuits I
    "EEE111": 3, "EEE111L": 1,                # Analog Electronics I
}

# CSE Capstone + Engineering Economics (7 credits)
CSE_CAPSTONE = {
    "CSE499A": 2,                              # Senior Capstone Design I
    "CSE499B": 2,                              # Senior Capstone Design II
    "EEE452": 3,                              # Engineering Economics
}

# SEPS Core — Math, Science, Programming (41 credits)
CSE_SEPS_CORE = {
    "CSE115": 3, "CSE115L": 1,                # Programming Language I
    "MAT116": 3,                              # Pre-Calculus
    "MAT120": 3,                              # Calculus I
    "MAT130": 3,                              # Calculus II
    "MAT250": 3,                              # Calculus III
    "MAT125": 3,                              # Linear Algebra
    "MAT350": 3,                              # Complex Variables
    "MAT361": 3,                              # Discrete Mathematics II
    "PHY107": 3, "PHY107L": 1,                # Physics I
    "PHY108": 3, "PHY108L": 1,                # Physics II
    "CHE101": 3, "CHE101L": 1,                # Chemistry I
    "BIO103": 3, "BIO103L": 1,                # Biology I (Wait, checking if BIO is in SEPS)
    "CEE110": 1,                              # Engineering Drawing (CAD)
}

# University Core / GED (34 credits)
CSE_GED_REQUIRED = {
    "ENG103": 3,                              # Intermediate Composition
    "ENG105": 3,                              # Advanced Writing Skills
    "ENG111": 3,                              # Public Speaking
    "PHI104": 3,                              # Introduction to Ethics
    "HIS101": 3,                              # Bangladesh History & Culture
    "HIS102": 3,                              # World Civilization
    "CSE101": 3,                              # Intro to Python Programming (GED)
    "CSE145": 3,                              # Intro to AI (GED)
    "CSE226": 3,                              # Fundamentals of Vibe Coding (GED)
}

CSE_GED_CHOICE_1 = {"ECO101": 3, "ECO104": 3}       # pick 1
CSE_GED_CHOICE_2 = {"POL101": 3, "POL104": 3}       # pick 1
CSE_GED_CHOICE_3 = {"SOC101": 3, "ANT101": 3, "ENV203": 3, "GEO205": 3}  # pick 1

CSE_GED_WAIVABLE = {
    "ENG102": 3,   # Waived if >=60% on English admission test
    "MAT112": 0,   # College Algebra, waived if >=60% on Math admission test
}

CSE_TOTAL_CREDITS = 130
CSE_MIN_CGPA = 2.0
CSE_MAJOR_CORE_CGPA = 2.0    # Major Core Courses CGPA requirement
CSE_MAJOR_ELECTIVE_CGPA = 2.0  # Major Elective Courses CGPA requirement
CSE_ELECTIVE_CREDITS = 9   # 3 CSE 400-level courses
CSE_OPEN_ELECTIVE_CREDITS = 3  # 1 course any department

# Combined "all core" for credit counting
CSE_ALL_CORE = {**CSE_MAJOR_CORE, **CSE_CAPSTONE, **CSE_SEPS_CORE}

# ─────────────────────────────────────────────────────
# BBA PROGRAM REQUIREMENTS — Curriculum 143 and Onwards
# Single Major: 41 courses / 124 credits (base)
#   +1 course if one waiver → 127cr
#   +2 courses if no waivers → 130cr
# ─────────────────────────────────────────────────────

# School Core (7 courses / 21 credits)
BBA_SCHOOL_CORE = {
    "ECO101": 3,                              # Intro to Microeconomics
    "ECO104": 3,                              # Intro to Macroeconomics
    "MIS107": 3,                              # Introduction to Computers
    "BUS251": 3,                              # Business Communication
    "BUS172": 3,                              # Introduction to Statistics
    "BUS173": 3,                              # Applied Statistics
    "BUS135": 3,                              # Business Mathematics
}

# BBA Core (12 courses / 36 credits)
BBA_CORE = {
    "ACT201": 3,                              # Intro to Financial Accounting
    "ACT202": 3,                              # Intro to Managerial Accounting
    "FIN254": 3,                              # Intro to Financial Management
    "LAW200": 3,                              # Legal Environment of Business
    "INB372": 3,                              # International Business
    "MKT202": 3,                              # Introduction to Marketing
    "MIS207": 3,                              # Management Information Systems
    "MGT212": 3,                              # Principles of Management
    "MGT351": 3,                              # Human Resource Management
    "MGT314": 3,                              # Production Management
    "MGT368": 3,                              # Entrepreneurship
    "MGT489": 3,                              # Strategic Management
}

# GED — General Education Courses
# 12/13/14 courses — 36/39/42 credits depending on waivers
# Waivable:
BBA_GED_WAIVABLE = {
    "ENG102": 3,   # Mandatory if not waived (English admission test)
    "BUS112": 3,   # Mandatory if not waived (Math admission test)
}

# Fixed GED (always required)
BBA_GED = {
    "ENG103": 3,                              # Intermediate Composition
    "ENG105": 3,                              # Advanced Composition
    "PHI401": 3,                              # Ethics / Philosophy
}

# GED Choice Groups
BBA_GED_CHOICE_LANG = {"BEN205": 3, "ENG115": 3, "CHN101": 3}  # pick 1

BBA_GED_CHOICE_HIS = {"HIS101": 3, "HIS102": 3, "HIS103": 3, "HIS205": 3}  # pick 2

BBA_GED_CHOICE_POL = {"POL101": 3, "POL104": 3, "PAD201": 3}  # pick 1

BBA_GED_CHOICE_SOC = {"SOC101": 3, "GEO205": 3, "ANT101": 3}  # pick 1

# Science: pick 3 from (BIO103, ENV107, PBH101, PSY101, PHY107, CHE101)
BBA_GED_CHOICE_SCI = {
    "BIO103": 3, "ENV107": 3, "PBH101": 3,
    "PSY101": 3, "PHY107": 3, "CHE101": 3,
}  # pick 3

# Science Lab: pick matching lab or any 3cr non-BBA course
BBA_GED_CHOICE_LAB = {
    "BIO103L": 1, "ENV107L": 1, "PBH101L": 1,
    "PSY101L": 1, "PHY107L": 1, "CHE101L": 1,
}  # pick 1 lab (or 3cr alternative — handled as open)

# Internship / Research Project (4 credits)
BBA_INTERNSHIP = {"BUS498": 4}  # or BUS499 if CGPA >= 3.30

BBA_TOTAL_CREDITS = 130   # with no waivers (127 with 1, 124 with 2)
BBA_MIN_CGPA = 2.0
BBA_CORE_CGPA = 2.0           # School & BBA Core CGPA requirement
BBA_CONCENTRATION_CGPA = 2.5  # Concentration/Major Area CGPA ≥ 2.5 to declare major
BBA_CONCENTRATION_CREDITS = 18  # 6 courses
BBA_FREE_ELECTIVE_CREDITS = 9   # 3 courses

# Combined School+BBA Core for CGPA computation
BBA_ALL_CORE = {**BBA_SCHOOL_CORE, **BBA_CORE}

# ─────────────────────────────────────────────────────
# BBA CONCENTRATION / MAJOR AREA COURSES (18 credits each)
# Each: 4 required (12cr) + 2 electives from pool (6cr)
# Source: NSU BBA Curriculum 143 Major Map
# ─────────────────────────────────────────────────────

# Accounting — Required: 310,320,360,370 | Elective: 380,460,430,410
BBA_CONC_ACT_REQUIRED = {"ACT310": 3, "ACT320": 3, "ACT360": 3, "ACT370": 3}
BBA_CONC_ACT_ELECTIVE = {"ACT380": 3, "ACT460": 3, "ACT430": 3, "ACT410": 3}

# Finance — Required: 433,440,435,444 | Elective: 455,464,470,480,410
BBA_CONC_FIN_REQUIRED = {"FIN433": 3, "FIN440": 3, "FIN435": 3, "FIN444": 3}
BBA_CONC_FIN_ELECTIVE = {"FIN455": 3, "FIN464": 3, "FIN470": 3, "FIN480": 3, "FIN410": 3}

# Marketing — Required: 337,344,460,470 | Elective: 412,465,382,417,330,450,355,445,475
BBA_CONC_MKT_REQUIRED = {"MKT337": 3, "MKT344": 3, "MKT460": 3, "MKT470": 3}
BBA_CONC_MKT_ELECTIVE = {"MKT412": 3, "MKT465": 3, "MKT382": 3, "MKT417": 3,
                          "MKT330": 3, "MKT450": 3, "MKT355": 3, "MKT445": 3, "MKT475": 3}

# Management — Required: MGT321,330, HRM370, MGT410 | Elective: MGT350,490, HRM470,450, MIS320
BBA_CONC_MGT_REQUIRED = {"MGT321": 3, "MGT330": 3, "HRM370": 3, "MGT410": 3}
BBA_CONC_MGT_ELECTIVE = {"MGT350": 3, "MGT490": 3, "HRM470": 3, "HRM450": 3, "MIS320": 3}

# HRM — Required: 340,360,380,450 | Elective: 370,499,470
BBA_CONC_HRM_REQUIRED = {"HRM340": 3, "HRM360": 3, "HRM380": 3, "HRM450": 3}
BBA_CONC_HRM_ELECTIVE = {"HRM370": 3, "HRM499": 3, "HRM470": 3}

# MIS — Required: 210,310,320,470 | Elective: 330/MKT330, 410, 450, MGT490, 499
BBA_CONC_MIS_REQUIRED = {"MIS210": 3, "MIS310": 3, "MIS320": 3, "MIS470": 3}
BBA_CONC_MIS_ELECTIVE = {"MIS330": 3, "MIS410": 3, "MIS450": 3, "MGT490": 3, "MIS499": 3}

# SCM — Required: SCM310,320,450, MGT460 | Elective: MGT360,390,470,490
BBA_CONC_SCM_REQUIRED = {"SCM310": 3, "SCM320": 3, "SCM450": 3, "MGT460": 3}
BBA_CONC_SCM_ELECTIVE = {"MGT360": 3, "MGT390": 3, "MGT470": 3, "MGT490": 3}

# Economics — Required: ECO201/203, ECO204, ECO348/349, ECO328/350/415
# Simplified: use one code per slot for audit; alternatives accepted
BBA_CONC_ECO_REQUIRED = {"ECO201": 3, "ECO204": 3, "ECO348": 3, "ECO328": 3}
# Large elective pool — including most listed options
BBA_CONC_ECO_ELECTIVE = {
    "ECO244": 3, "ECO301": 3, "ECO304": 3, "ECO317": 3, "ECO329": 3,
    "ECO343": 3, "ECO354": 3, "ECO360": 3, "ECO372": 3, "ECO380": 3,
    "ECO406": 3, "ECO410": 3, "ECO414": 3, "ECO415": 3, "ECO417": 3,
    "ECO430": 3, "ECO436": 3, "ECO441": 3, "ECO443": 3, "ECO450": 3,
    "ECO451": 3, "ECO460": 3, "ECO465": 3, "ECO472": 3, "ECO474": 3,
    "ECO475": 3, "ECO484": 3, "ECO485": 3, "ECO486": 3, "ECO492": 3,
}

# INB — Required: INB400,490,480, MKT382 | Elective: INB410,350,355,415,450,495, MKT417
BBA_CONC_INB_REQUIRED = {"INB400": 3, "INB490": 3, "INB480": 3, "MKT382": 3}
BBA_CONC_INB_ELECTIVE = {"INB410": 3, "INB350": 3, "INB355": 3, "INB415": 3,
                          "INB450": 3, "INB495": 3, "MKT417": 3}

# Lookup dict: concentration code → (required_dict, elective_dict, label)
BBA_CONCENTRATIONS = {
    "ACT": (BBA_CONC_ACT_REQUIRED, BBA_CONC_ACT_ELECTIVE, "Accounting"),
    "FIN": (BBA_CONC_FIN_REQUIRED, BBA_CONC_FIN_ELECTIVE, "Finance"),
    "MKT": (BBA_CONC_MKT_REQUIRED, BBA_CONC_MKT_ELECTIVE, "Marketing"),
    "MGT": (BBA_CONC_MGT_REQUIRED, BBA_CONC_MGT_ELECTIVE, "Management"),
    "HRM": (BBA_CONC_HRM_REQUIRED, BBA_CONC_HRM_ELECTIVE, "Human Resource Management"),
    "MIS": (BBA_CONC_MIS_REQUIRED, BBA_CONC_MIS_ELECTIVE, "Management Information Systems"),
    "SCM": (BBA_CONC_SCM_REQUIRED, BBA_CONC_SCM_ELECTIVE, "Supply Chain Management"),
    "ECO": (BBA_CONC_ECO_REQUIRED, BBA_CONC_ECO_ELECTIVE, "Economics"),
    "INB": (BBA_CONC_INB_REQUIRED, BBA_CONC_INB_ELECTIVE, "International Business"),
}

VALID_CONCENTRATIONS = set(BBA_CONCENTRATIONS.keys())

# ─────────────────────────────────────────────────────
# PREREQUISITE MAPPING
# ─────────────────────────────────────────────────────

from engine.prerequisites import PREREQUISITES_CSE, PREREQUISITES_BBA
import collections


def check_prerequisite_violations(program, records, waivers):
    """
    Check if any courses in records were taken before their prerequisites were passed.
    Returns a list of dicts: {"course": code, "missing": [missing_prereqs]}
    """
    # Group records by semester and sort semesters chronologically
    sem_map = {sem: i for i, sem in enumerate(SEMESTERS)}
    records_by_sem = collections.defaultdict(list)
    for r in records:
        records_by_sem[r.semester].append(r)
        
    sorted_sems = sorted(records_by_sem.keys(), key=lambda s: sem_map.get(s, 9999))
    
    prereq_map = PREREQUISITES_CSE if program.upper() == "CSE" else PREREQUISITES_BBA
    passed_so_far = set(k for k, v in waivers.items() if v)  # Only true waivers count
    violations = []
    
    # Track credits earned at each step for senior status check
    credits_at_step = 0
    first_sem = sorted_sems[0] if sorted_sems else None
    
    for current_sem in sorted_sems:
        sem_records = records_by_sem[current_sem]
        
        # FIRST SEMESTER EXCEPTION: Allow concurrent enrollment of prerequisites.
        # We add passed courses to the pool BEFORE checking them.
        if current_sem == first_sem:
            for r in sem_records:
                if r.grade not in ("F", "W", "I"):
                    passed_so_far.add(r.course_code)
                    credits_at_step += r.credits
                    
        # Verify prereqs for this semester's courses
        for r in sem_records:
            code = r.course_code
            if code in prereq_map:
                required = prereq_map[code]
                missing = []
                for req in required:
                    if req == "_SENIOR_":
                        if credits_at_step < 100:
                            missing.append("Senior Status (100+ Credits)")
                    elif req not in passed_so_far:
                        missing.append(req)
                
                if missing:
                    violations.append({
                        "course": code,
                        "semester": current_sem,
                        "missing": missing
                    })
        
        # NORMAL SEMESTERS: Add passed courses to the pool AFTER checking prereqs
        if current_sem != first_sem:
            for r in sem_records:
                if r.grade not in ("F", "W", "I"):
                    passed_so_far.add(r.course_code)
                    credits_at_step += r.credits
            
    return violations


def _get_passed_courses(records):
    """Return set of course codes that the student has passed (BEST or WAIVED status)."""
    passed = set()
    for r in records:
        if r.status in ("BEST", "WAIVED") and r.grade not in ("F", "I", "W"):
            passed.add(r.course_code)
    return passed


def _find_missing(required_dict, passed_set):
    """Return dict of {course: credits} for courses not yet passed."""
    return {c: cr for c, cr in required_dict.items() if c not in passed_set}


def _check_choice_group(choice_dict, passed_set):
    """Check if at least one course from a choice group is passed. Return missing info."""
    for c in choice_dict:
        if c in passed_set:
            return {}  # satisfied
    return choice_dict  # none passed — return all options


def audit_cse(records, waivers, credits_earned, cgpa, credit_reduction=0):
    """
    Perform CSE program audit (130-credit curriculum).
    Returns dict with: eligible, reasons, remaining_by_category, major_cgpa
    """
    passed = _get_passed_courses(records)
    remaining = {}
    reasons = []
    total_required = CSE_TOTAL_CREDITS - credit_reduction

    # CSE Major Core (42cr) — remove waived courses
    core_to_check = dict(CSE_MAJOR_CORE)
    missing_core = _find_missing(core_to_check, passed)
    if missing_core:
        remaining["CSE Major Core"] = missing_core

    # Capstone + Engineering Economics (7cr)
    missing_cap = _find_missing(CSE_CAPSTONE, passed)
    if missing_cap:
        remaining["Capstone"] = missing_cap

    # SEPS Core (41cr)
    seps_to_check = dict(CSE_SEPS_CORE)
    missing_seps = _find_missing(seps_to_check, passed)
    if missing_seps:
        remaining["SEPS Core"] = missing_seps

    # GED required (fixed courses)
    missing_ged = _find_missing(CSE_GED_REQUIRED, passed)
    if missing_ged:
        remaining["GED Required"] = missing_ged

    # GED choice groups
    missing_c1 = _check_choice_group(CSE_GED_CHOICE_1, passed)
    if missing_c1:
        remaining["GED Choice (ECO101 or ECO104)"] = missing_c1

    missing_c2 = _check_choice_group(CSE_GED_CHOICE_2, passed)
    if missing_c2:
        remaining["GED Choice (POL101 or POL104)"] = missing_c2

    missing_c3 = _check_choice_group(CSE_GED_CHOICE_3, passed)
    if missing_c3:
        remaining["GED Choice (SOC101/ANT101/ENV203/GEO205)"] = missing_c3

    # Waivable courses (ENG102, MAT112)
    waivable_remaining = {}
    for course, cr in CSE_GED_WAIVABLE.items():
        if not waivers.get(course, False) and course not in passed:
            waivable_remaining[course] = cr
    if waivable_remaining:
        remaining["Waivable Courses"] = waivable_remaining

    # Electives (CSE 400-level) — count passed CSE 4xx courses not in core
    cse_400_electives = [c for c in passed
                         if c.startswith("CSE4") and c not in CSE_MAJOR_CORE and c not in CSE_CAPSTONE]
    elective_credits = sum(3 for _ in cse_400_electives)  # assume 3 each
    if elective_credits < CSE_ELECTIVE_CREDITS:
        needed = (CSE_ELECTIVE_CREDITS - elective_credits) // 3
        remaining["CSE Electives (400-level)"] = {f"Any CSE 4xx ({needed} needed)": CSE_ELECTIVE_CREDITS - elective_credits}

    # Open electives — any courses not already counted
    all_required_codes = (set(CSE_ALL_CORE.keys()) |
                          set(CSE_CAPSTONE.keys()) |
                          set(CSE_GED_REQUIRED.keys()) |
                          set(CSE_GED_CHOICE_1.keys()) |
                          set(CSE_GED_CHOICE_2.keys()) |
                          set(CSE_GED_CHOICE_3.keys()) |
                          set(CSE_GED_WAIVABLE.keys()))
    counted_open = set()
    open_elec_credits = 0
    for r in records:
        if (r.course_code not in all_required_codes and
            r.course_code not in counted_open and
            not (r.course_code.startswith("CSE4") and r.course_code not in CSE_MAJOR_CORE and r.course_code not in CSE_CAPSTONE) and
            r.status in ("BEST", "WAIVED") and r.credits > 0 and
            r.grade not in ("F", "I", "W")):
            open_elec_credits += r.credits
            counted_open.add(r.course_code)

    if open_elec_credits < CSE_OPEN_ELECTIVE_CREDITS:
        needed_cr = CSE_OPEN_ELECTIVE_CREDITS - open_elec_credits
        remaining["Open Electives"] = {f"Any courses ({needed_cr} credits needed)": needed_cr}

    # Major Core CGPA — based on CSE Major Core courses
    major_core_codes = list(CSE_MAJOR_CORE.keys())
    major_core_cgpa = compute_major_cgpa(records, major_core_codes)

    # Major Elective CGPA — based on CSE 400-level electives
    elective_codes = [c for c in passed
                      if c.startswith("CSE4") and c not in CSE_MAJOR_CORE and c not in CSE_CAPSTONE]
    major_elective_cgpa = compute_major_cgpa(records, elective_codes) if elective_codes else 0.0

    # Graduation eligibility checks
    eligible = True

    if credits_earned < total_required:
        eligible = False
        reasons.append(f"Credits earned ({credits_earned}) < {total_required} required")

    if cgpa < CSE_MIN_CGPA:
        eligible = False
        reasons.append(f"Overall CGPA ({cgpa:.2f}) < {CSE_MIN_CGPA:.2f}")

    if major_core_cgpa < CSE_MAJOR_CORE_CGPA:
        eligible = False
        reasons.append(f"Major Core CGPA ({major_core_cgpa:.2f}) < {CSE_MAJOR_CORE_CGPA:.2f}")

    if elective_codes and major_elective_cgpa < CSE_MAJOR_ELECTIVE_CGPA:
        eligible = False
        reasons.append(f"Major Elective CGPA ({major_elective_cgpa:.2f}) < {CSE_MAJOR_ELECTIVE_CGPA:.2f}")

    # Check for unauthorized retakes
    for r in records:
        if r.status == "UNAUTHORIZED-RETAKE":
            eligible = False
            reasons.append(f"Invalid course: Unauthorized retake of {r.course_code} ({r.grade} in {r.semester})")

    if remaining:
        eligible = False
        total_missing = sum(len(v) for v in remaining.values())
        reasons.append(f"{total_missing} required course(s) still missing")

    result = {
        "eligible": eligible,
        "reasons": reasons,
        "remaining": remaining,
        "major_core_cgpa": major_core_cgpa,
        "major_elective_cgpa": major_elective_cgpa,
        "total_credits_required": total_required,
    }
    
    # ── Prerequisites ──
    result["prereq_violations"] = check_prerequisite_violations("CSE", records, waivers)

    return result


def audit_bba(records, waivers, credits_earned, cgpa, credit_reduction=0, concentration=None):
    """
    Perform BBA program audit — Curriculum 143 and Onwards.
    concentration: one of ACT/FIN/MKT/MGT/HRM/MIS/SCM/ECO/INB (or None)
    Returns dict with: eligible, reasons, remaining_by_category, cgpa info
    """
    passed = _get_passed_courses(records)
    remaining = {}
    reasons = []
    total_required = BBA_TOTAL_CREDITS - credit_reduction

    if not concentration:
        reasons.append("Major/Concentration not yet declared")
    
    # School Core (7 courses / 21 credits)
    missing_school = _find_missing(BBA_SCHOOL_CORE, passed)
    if missing_school:
        remaining["School Core"] = missing_school

    # BBA Core (12 courses / 36 credits)
    missing_core = _find_missing(BBA_CORE, passed)
    if missing_core:
        remaining["BBA Core"] = missing_core

    # GED fixed courses (ENG103, ENG105, PHI401)
    missing_ged = _find_missing(BBA_GED, passed)
    if missing_ged:
        remaining["GED"] = missing_ged

    # GED Choice: Language (BEN205/ENG115/CHN101 — pick 1)
    missing_lang = _check_choice_group(BBA_GED_CHOICE_LANG, passed)
    if missing_lang:
        remaining["GED Choice (Language)"] = missing_lang

    # GED Choice: History (HIS101/102/103/HIS205 — pick 2)
    his_passed = [c for c in BBA_GED_CHOICE_HIS if c in passed]
    his_needed = 2 - len(his_passed)
    if his_needed > 0:
        his_options = {c: cr for c, cr in BBA_GED_CHOICE_HIS.items() if c not in passed}
        remaining[f"GED Choice (History, pick {his_needed})"] = his_options

    # GED Choice: Political Science (POL101/POL104/PAD201 — pick 1)
    missing_pol = _check_choice_group(BBA_GED_CHOICE_POL, passed)
    if missing_pol:
        remaining["GED Choice (Political Science)"] = missing_pol

    # GED Choice: Social Science (SOC101/GEO205/ANT101 — pick 1)
    missing_soc = _check_choice_group(BBA_GED_CHOICE_SOC, passed)
    if missing_soc:
        remaining["GED Choice (Social Science)"] = missing_soc

    # GED Choice: Science (BIO103/ENV107/PBH101/PSY101/PHY107/CHE101 — pick 3)
    sci_passed = [c for c in BBA_GED_CHOICE_SCI if c in passed]
    sci_needed = 3 - len(sci_passed)
    if sci_needed > 0:
        sci_options = {c: cr for c, cr in BBA_GED_CHOICE_SCI.items() if c not in passed}
        remaining[f"GED Choice (Science, pick {sci_needed})"] = sci_options

    # GED Choice: Lab (pick 1 matching lab or 3cr alternative)
    lab_passed = [c for c in BBA_GED_CHOICE_LAB if c in passed]
    if len(lab_passed) == 0:
        remaining["GED Choice (Lab)"] = dict(BBA_GED_CHOICE_LAB)

    # Waivable courses (ENG102 3cr, BUS112 3cr)
    waivable_remaining = {}
    for course, cr in BBA_GED_WAIVABLE.items():
        if not waivers.get(course, False) and course not in passed:
            waivable_remaining[course] = cr
    if waivable_remaining:
        remaining["GED Waivable"] = waivable_remaining

    # Internship
    missing_intern = _find_missing(BBA_INTERNSHIP, passed)
    if missing_intern:
        remaining["Internship"] = missing_intern

    # ── Concentration courses (18cr: 4 required + 2 elective) ──
    conc_label = "Undeclared"
    conc_all_codes = []
    if concentration and concentration.upper() in BBA_CONCENTRATIONS:
        conc_key = concentration.upper()
        conc_req, conc_elec, conc_label = BBA_CONCENTRATIONS[conc_key]

        # Required concentration courses
        missing_conc_req = _find_missing(conc_req, passed)
        if missing_conc_req:
            remaining[f"{conc_label} Required"] = missing_conc_req

        # Elective concentration courses (need 2 from pool)
        elec_passed = [c for c in conc_elec if c in passed]
        elec_needed = 2 - len(elec_passed)
        if elec_needed > 0:
            elec_options = {c: cr for c, cr in conc_elec.items() if c not in passed}
            remaining[f"{conc_label} Elective (pick {elec_needed})"] = elec_options

        # All concentration course codes for CGPA computation
        conc_all_codes = list(conc_req.keys()) + [c for c in conc_elec if c in passed]
    else:
        conc_all_codes = []

    # Free Electives (3 courses / 9 credits)
    conc_code_set = set(conc_all_codes)
    all_required_codes = (set(BBA_SCHOOL_CORE.keys()) |
                          set(BBA_CORE.keys()) |
                          set(BBA_GED.keys()) |
                          set(BBA_GED_CHOICE_LANG.keys()) |
                          set(BBA_GED_CHOICE_HIS.keys()) |
                          set(BBA_GED_CHOICE_POL.keys()) |
                          set(BBA_GED_CHOICE_SOC.keys()) |
                          set(BBA_GED_CHOICE_SCI.keys()) |
                          set(BBA_GED_CHOICE_LAB.keys()) |
                          set(BBA_GED_WAIVABLE.keys()) |
                          set(BBA_INTERNSHIP.keys()) |
                          conc_code_set)
    counted_open = set()
    free_elec_credits = 0
    for r in records:
        if (r.course_code not in all_required_codes and
            r.course_code not in counted_open and
            r.status in ("BEST", "WAIVED") and r.credits > 0 and
            r.grade not in ("F", "I", "W")):
            free_elec_credits += r.credits
            counted_open.add(r.course_code)




    if free_elec_credits < BBA_FREE_ELECTIVE_CREDITS:
        needed_cr = BBA_FREE_ELECTIVE_CREDITS - free_elec_credits
        remaining["Free Electives"] = {f"Any courses ({needed_cr} credits needed)": needed_cr}

    # School & BBA Core CGPA (combined 19 courses / 57 credits)
    core_codes = list(BBA_ALL_CORE.keys())
    core_cgpa = compute_major_cgpa(records, core_codes)

    # Concentration/Major Area CGPA
    if conc_all_codes:
        concentration_cgpa = compute_major_cgpa(records, conc_all_codes)
    else:
        concentration_cgpa = core_cgpa  # fallback if no concentration specified

    # Eligibility checks
    eligible = True

    if credits_earned < total_required:
        eligible = False
        reasons.append(f"Credits earned ({credits_earned}) < {total_required} required")

    if cgpa < BBA_MIN_CGPA:
        eligible = False
        reasons.append(f"Overall CGPA ({cgpa:.2f}) < {BBA_MIN_CGPA:.2f}")

    if core_cgpa < BBA_CORE_CGPA:
        eligible = False
        reasons.append(f"School & BBA Core CGPA ({core_cgpa:.2f}) < {BBA_CORE_CGPA:.2f}")

    if concentration_cgpa < BBA_CONCENTRATION_CGPA:
        eligible = False
        reasons.append(f"Concentration CGPA ({concentration_cgpa:.2f}) < {BBA_CONCENTRATION_CGPA:.2f}")

    # Check for unauthorized retakes
    for r in records:
        if r.status == "UNAUTHORIZED-RETAKE":
            eligible = False
            reasons.append(f"Invalid course: Unauthorized retake of {r.course_code} ({r.grade} in {r.semester})")

    if remaining:
        eligible = False
        total_missing = sum(len(v) for v in remaining.values())
        reasons.append(f"{total_missing} required course(s) still missing")

    result = {
        "eligible": eligible,
        "reasons": reasons,
        "remaining": remaining,
        "core_cgpa": core_cgpa,
        "concentration_cgpa": concentration_cgpa,
        "concentration_label": conc_label,
        "total_credits_required": total_required,
    }
    
    # ── Prerequisites ──
    result["prereq_violations"] = check_prerequisite_violations("BBA", records, waivers)

    return result


def build_graduation_roadmap(program, records, credits_earned, cgpa, major_cgpa, audit_result, standing):
    """
    Build an actionable graduation roadmap — what the student must do to graduate.
    Returns a dict with steps, estimates, and actionable info.
    """
    total_req = audit_result["total_credits_required"]
    remaining = audit_result.get("remaining", {})
    eligible = audit_result["eligible"]

    roadmap = {
        "eligible": eligible,
        "steps": [],
        "credit_gap": 0,
        "missing_course_credits": 0,
        "estimated_courses_left": 0,
        "estimated_semesters": 0,
    }

    if eligible:
        roadmap["steps"].append({
            "category": "CONGRATULATIONS",
            "action": "You have met all graduation requirements!",
            "priority": "DONE",
            "detail": None,
        })
        return roadmap

    # ── Step 1: Credit gap analysis ──
    if credits_earned < total_req:
        gap = total_req - credits_earned
        roadmap["credit_gap"] = gap
        roadmap["steps"].append({
            "category": "CREDITS",
            "action": f"Earn {gap} more credits to reach the {total_req}-credit requirement",
            "priority": "HIGH",
            "detail": f"Currently at {credits_earned}/{total_req} credits.",
        })

    # ── Step 2: CGPA improvement ──
    min_cgpa = 2.0
    if cgpa < min_cgpa:
        detail_msg = f"You are on {standing}. Focus on higher grades in remaining courses. Retaking low-grade courses may help."
        if "P2" in standing:
            detail_msg = f"CRITICAL: You are on {standing}. This is your LAST consecutive semester on probation. Failure to reach 2.0 CGPA will lead to automatic dismissal."
        elif "DISMISSAL" in standing:
            detail_msg = f"CAUTION: You have exceeded the probation limit. You are at dismissal stage. Contact Academic Advising immediately."

        roadmap["steps"].append({
            "category": "CGPA",
            "action": f"Raise overall CGPA from {cgpa:.2f} to at least {min_cgpa:.2f}",
            "priority": "CRITICAL",
            "detail": detail_msg,
        })

    # ── Step 3: Major/Core CGPA ──
    # Threshold is 2.0 for CSE and BBA Core; 2.5 is only for BBA Concentrations (checked elsewhere)
    major_threshold = 2.0
    major_label = "Major CGPA" if program.upper() == "CSE" else "Core GPA"
    if major_cgpa < major_threshold:
        roadmap["steps"].append({
            "category": "MAJOR GPA",
            "action": f"Raise {major_label} from {major_cgpa:.2f} to at least {major_threshold:.2f}",
            "priority": "HIGH",
            "detail": f"Consider retaking core courses where you scored D/D+ to improve this.",
        })

    # ── Step 3.5: Undeclared Major (BBA only) ──
    if program.upper() == "BBA" and audit_result.get("concentration_label") == "Undeclared":
        prio = "CRITICAL" if credits_earned >= 60 else "LOW"
        roadmap["steps"].append({
            "category": "DECLARE MAJOR",
            "action": "Select and declare your Concentration/Major area",
            "priority": prio,
            "detail": f"You have {credits_earned} credits. " + 
                      ("It is critical to declare now to start major courses." if credits_earned >= 60 else 
                       "You should focus on core credits, but start thinking about your major.")
        })

    # ── Step 4: Missing courses by category ──
    total_missing_courses = 0
    total_missing_credits = 0
    for category, courses in remaining.items():
        course_list = list(courses.items())
        cat_credits = sum(cr for _, cr in course_list)
        total_missing_courses += len(course_list)
        total_missing_credits += cat_credits

        if "Choice" in category:
            # Choice group — pick one
            options = " or ".join(c for c, _ in course_list)
            roadmap["steps"].append({
                "category": category.upper(),
                "action": f"Complete 1 course from: {options}",
                "priority": "MEDIUM",
                "detail": f"Pick any one ({cat_credits} credits each).",
            })
        elif "Elective" in category or "Open" in category:
            roadmap["steps"].append({
                "category": category.upper(),
                "action": f"Complete {cat_credits} credits of electives",
                "priority": "MEDIUM",
                "detail": ", ".join(f"{c} ({cr}cr)" for c, cr in course_list),
            })
        elif "Waivable" in category:
            roadmap["steps"].append({
                "category": category.upper(),
                "action": f"Pass or get waiver for: {', '.join(c for c, _ in course_list)}",
                "priority": "LOW",
                "detail": "0-credit course - does not affect CGPA or credit total, but is required.",
            })
        else:
            # Regular required courses
            roadmap["steps"].append({
                "category": category.upper(),
                "action": f"Complete {len(course_list)} course(s) ({cat_credits} credits)",
                "priority": "HIGH",
                "detail": ", ".join(f"{c} ({cr}cr)" for c, cr in course_list),
            })

    roadmap["missing_course_credits"] = total_missing_credits
    roadmap["estimated_courses_left"] = total_missing_courses

    # ── Estimate semesters remaining ──
    # Assume average 15 credits/semester (5 courses)
    credits_still_needed = max(roadmap["credit_gap"], total_missing_credits)
    if credits_still_needed > 0:
        roadmap["estimated_semesters"] = max(1, -(-credits_still_needed // 15))  # ceiling division
    else:
        roadmap["estimated_semesters"] = 1 if not eligible else 0

    # ── Retake recommendations ──
    if cgpa < min_cgpa or major_cgpa < major_threshold:
        # Find courses with low grades that could be retaken
        low_grade_courses = []
        seen = set()
        for r in records:
            if (r.status == "BEST" and r.grade in ("D", "D+", "C-") and
                r.credits > 0 and r.course_code not in seen):
                low_grade_courses.append((r.course_code, r.grade, r.credits))
                seen.add(r.course_code)

        if low_grade_courses:
            # Sort by credits (retake high-credit courses for max GPA impact)
            low_grade_courses.sort(key=lambda x: -x[2])
            top_retakes = low_grade_courses[:5]
            detail = ", ".join(f"{c} (current: {g}, {cr}cr)" for c, g, cr in top_retakes)
            roadmap["steps"].append({
                "category": "RETAKE SUGGESTIONS",
                "action": f"Consider retaking {len(top_retakes)} course(s) to boost GPA",
                "priority": "RECOMMENDED",
                "detail": detail,
            })

    return roadmap


def run_audit(records, program, waivers, credits_earned, cgpa, credit_reduction=0, concentration=None):
    """Dispatch to the correct program audit."""
    if program.upper() == "CSE":
        return audit_cse(records, waivers, credits_earned, cgpa, credit_reduction)
    elif program.upper() == "BBA":
        return audit_bba(records, waivers, credits_earned, cgpa, credit_reduction, concentration)
    else:
        raise ValueError(f"Unknown program: {program}. Use 'CSE' or 'BBA'.")

