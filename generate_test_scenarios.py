import csv
import os
import random
from engine.course_db import *
from engine.credit_engine import SEMESTERS

# Ensure ALL_COURSES is fully populated
for d in [CSE_MAJOR_CORE, CSE_CAPSTONE, CSE_SEPS_CORE, CSE_GED, CSE_GED_CHOICE_1, CSE_GED_CHOICE_2,
          CSE_GED_CHOICE_3, CSE_ELECTIVES_400, OPEN_ELECTIVES, BBA_SCHOOL_CORE, BBA_CORE, BBA_GED,
          BBA_GED_CHOICE_LANG, BBA_GED_CHOICE_HIS, BBA_GED_CHOICE_POL, BBA_GED_CHOICE_SOC,
          BBA_GED_CHOICE_SCI, BBA_GED_CHOICE_LAB, BBA_INTERNSHIP, WAIVER_COURSES]:
    ALL_COURSES.update(d)
for conc_data in BBA_CONC_COURSES.values():
    ALL_COURSES.update(conc_data["required"])
    ALL_COURSES.update(conc_data["elective"])

OUTPUT_DIR = "test_scenarios"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_transcript(filename, rows):
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["course_code", "course_name", "credits", "grade", "semester"])
        for row in rows:
            writer.writerow(row)

def create_row(code, grade, semester):
    if code not in ALL_COURSES:
        return [code, "Unknown Course", "3", grade, semester]
    name, credits = ALL_COURSES[code]
    return [code, name, str(credits), grade, semester]

# --- CSE Scenarios ---

def gen_eligible_cse():
    rows = []
    # Sem 0 (Waivers)
    rows.append(create_row("ENG102", "T", SEMESTERS[0]))
    rows.append(create_row("MAT112", "T", SEMESTERS[0]))
    # Sem 1: Foundations
    for code in ["MAT116", "CSE115", "CSE115L", "CHE101", "CHE101L"]:
        rows.append(create_row(code, "A-", SEMESTERS[1]))
    # Sem 2: Chain 1
    for code in ["MAT120", "CSE173", "BIO103", "BIO103L", "CEE110"]:
        rows.append(create_row(code, "A-", SEMESTERS[2]))
    # Sem 3: Chain 2
    for code in ["MAT130", "PHY107", "PHY107L", "CSE215", "CSE215L", "ENG103"]:
        rows.append(create_row(code, "A-", SEMESTERS[3]))
    # Sem 4: Chain 3
    for code in ["MAT250", "PHY108", "PHY108L", "CSE225", "CSE225L", "ENG105"]:
        rows.append(create_row(code, "A-", SEMESTERS[4]))
    # Sem 5: Chain 4
    for code in ["MAT350", "CSE311", "CSE311L", "CSE373", "CSE231", "CSE231L"]:
        rows.append(create_row(code, "A-", SEMESTERS[5]))
    # Sem 6: Chain 5
    for code in ["MAT125", "CSE332", "CSE327", "CSE299", "MAT361"]:
        rows.append(create_row(code, "A-", SEMESTERS[6]))
    # Sem 7: Chain 6
    for code in ["CSE323", "CSE331", "CSE331L", "EEE141", "EEE141L", "CSE425"]:
        rows.append(create_row(code, "A-", SEMESTERS[7]))
    # Sem 8: Others & GEDs
    for code in ["EEE111", "EEE111L", "PHI104", "HIS101", "HIS102"]:
        rows.append(create_row(code, "A-", SEMESTERS[8]))
    # Sem 9: Choices & Electives
    for code in ["ECO101", "POL101", "SOC101", "CSE101", "CSE145"]:
        rows.append(create_row(code, "A-", SEMESTERS[9]))
    # Sem 10: Advanced Electives
    for code in ["CSE421", "CSE423", "CSE445", "SOC201", "PHI201"]:
        rows.append(create_row(code, "A-", SEMESTERS[10]))
    # Sem 11: Senior (Capstone)
    rows.append(create_row("CSE499A", "A", SEMESTERS[11]))
    rows.append(create_row("CSE226", "A", SEMESTERS[11]))
    rows.append(create_row("ENG111", "A", SEMESTERS[11]))
    # Sem 12: Final
    rows.append(create_row("CSE499B", "A", SEMESTERS[12]))
    rows.append(create_row("EEE452", "A", SEMESTERS[12]))
    save_transcript("cse_eligible.csv", rows)

def gen_ineligible_cse():
    rows = []
    # Tier 0 only
    for i, code in enumerate(["MAT116", "CSE115", "CHE101", "HIS101", "SOC101"]):
        rows.append(create_row(code, "B", SEMESTERS[0]))
    save_transcript("cse_ineligible_credits.csv", rows)

def gen_probation_cse(level):
    rows = []
    # Sem 0: 2 D's -> CGPA 1.0 (P1)
    # Tier 0 (No Prereqs)
    rows.append(create_row("MAT116", "D", SEMESTERS[0]))
    rows.append(create_row("CSE115", "D", SEMESTERS[0]))
    
    if level >= 2:
        # Sem 1: 2 F's -> CGPA < 2.0 (P2)
        # Still Tier 0 to avoid violations
        rows.append(create_row("CHE101", "F", SEMESTERS[1]))
        rows.append(create_row("HIS101", "F", SEMESTERS[1]))
        
    if level >= 3:
        # Sem 2: 2 F's -> (Dismissal)
        rows.append(create_row("SOC101", "F", SEMESTERS[2]))
        rows.append(create_row("ECO101", "F", SEMESTERS[2]))
        
    filenames = {1: "cse_probation_1.csv", 2: "cse_probation_2.csv", 3: "cse_dismissal.csv"}
    save_transcript(filenames[level], rows)

# --- BBA Scenarios ---

def gen_eligible_bba():
    rows = []
    # Tier 0 (Waivers)
    rows.append(create_row("ENG102", "T", SEMESTERS[0]))
    rows.append(create_row("BUS112", "T", SEMESTERS[0]))
    # Tier 1: Foundations
    for code in ["BUS135", "ECO101", "MIS107", "ENG103", "HIS101"]:
        rows.append(create_row(code, "A-", SEMESTERS[1]))
    # Tier 2:
    for code in ["BUS172", "ECO104", "ACT201", "ENG105", "HIS102", "PHI401"]:
        rows.append(create_row(code, "A-", SEMESTERS[2]))
    # Tier 3:
    for code in ["BUS173", "ACT202", "FIN254", "MKT202", "MGT212", "LAW200"]:
        rows.append(create_row(code, "A-", SEMESTERS[3]))
    # Tier 4:
    for code in ["INB372", "MIS207", "MGT351", "MGT314", "MGT368", "BUS251"]:
        rows.append(create_row(code, "A-", SEMESTERS[4]))
    # Tier 5: GEDs & Electives
    for code in ["BEN205", "POL101", "SOC101", "ENV107", "PSY101", "PBH101"]:
        rows.append(create_row(code, "A-", SEMESTERS[5]))
    # Tier 6: More GEDs & Free Elec
    for code in ["BIO103", "BIO103L", "SOC201", "PHI201", "HIS201"]:
        rows.append(create_row(code, "A-", SEMESTERS[6]))
    # Tier 7: Concentration (Finance)
    for code in ["FIN433", "FIN435", "FIN440", "FIN444", "FIN455", "FIN464"]:
        rows.append(create_row(code, "A-", SEMESTERS[7]))
    # Tier 8: Strategic Management & Internship (Senior)
    rows.append(create_row("MGT489", "A", SEMESTERS[12]))
    rows.append(create_row("BUS498", "A", SEMESTERS[13]))
    save_transcript("bba_eligible_FIN.csv", rows)

def gen_undeclared_bba():
    rows = []
    # Waivers first
    rows.append(create_row("ENG102", "T", SEMESTERS[0]))
    rows.append(create_row("BUS112", "T", SEMESTERS[0]))
    # Tier 0/1 courses only
    for i, code in enumerate(["ECO101", "MIS107", "HIS101", "SOC101", "BUS135"]):
        rows.append(create_row(code, "B", SEMESTERS[1]))
    for i, code in enumerate(["POL101", "PSY101", "ENV107", "HIS102", "ENG103"]):
        rows.append(create_row(code, "B", SEMESTERS[2]))
    save_transcript("bba_undeclared.csv", rows)

def gen_probation_bba(level):
    rows = []
    # Tier 0 only
    rows.append(create_row("ECO101", "D", SEMESTERS[0]))
    rows.append(create_row("MIS107", "F", SEMESTERS[0]))
    # (P1)
    
    if level >= 2:
        # Tier 0
        rows.append(create_row("HIS101", "F", SEMESTERS[1]))
        rows.append(create_row("SOC101", "F", SEMESTERS[1]))
        # (P2)
        
    if level >= 3:
        # Tier 0
        rows.append(create_row("POL101", "F", SEMESTERS[2]))
        rows.append(create_row("PSY101", "F", SEMESTERS[2]))
        # (Dismissal)

    filenames = {1: "bba_probation_1.csv", 2: "bba_probation_2.csv", 3: "bba_dismissal.csv"}
    save_transcript(filenames[level], rows)

if __name__ == "__main__":
    gen_eligible_cse()
    gen_ineligible_cse()
    gen_probation_cse(1)
    gen_probation_cse(2)
    gen_probation_cse(3)
    gen_eligible_bba()
    gen_undeclared_bba()
    gen_probation_bba(1)
    gen_probation_bba(2)
    gen_probation_bba(3)
    print(f"Forced all test scenarios to follow prerequisite protocols in {OUTPUT_DIR}/")
