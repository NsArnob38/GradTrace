"""Verify: 1) Zero unrecognized courses across all CSVs. 2) Full audit pipeline works."""
import csv, json, glob, traceback

from packages.core.course_catalog import ALL_COURSES
from packages.core.unified import UnifiedAuditor

# --- Part 1: Check for unrecognized courses ---
all_missing = {}
for pattern in ["test_scenarios/*.csv", "transcripts/*.csv"]:
    for fpath in glob.glob(pattern):
        with open(fpath, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 5: continue
                if row[0].strip().lower() == "course_code": continue
                code = row[0].strip()
                if code not in ALL_COURSES:
                    all_missing[code] = row[1].strip()

if all_missing:
    print(f"FAIL: {len(all_missing)} unrecognized courses: {all_missing}")
else:
    print("PASS: All course codes recognized across all test CSVs")

# --- Part 2: Test audit on cse_eligible.csv ---
rows = []
with open("test_scenarios/cse_eligible.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    for row in reader:
        if not row or len(row) < 5: continue
        if row[0].strip().lower() == "course_code": continue
        rows.append({
            "course_code": row[0].strip(), "course_name": row[1].strip(),
            "credits": row[2].strip(), "grade": row[3].strip(), "semester": row[4].strip(),
        })

try:
    result = UnifiedAuditor.run_from_rows(rows, "CSE")
    if result["meta"]["fake_transcript"]:
        print(f"FAIL: Fake transcript detected: {result['meta']['unrecognized_courses']}")
    else:
        print(f"PASS: Audit succeeded — CGPA={result['level_2']['cgpa']:.2f}, Credits={result['level_1']['credits_earned']}, Eligible={result['level_3']['eligible']}")
        json_str = json.dumps(result, default=str)
        print(f"PASS: JSON serialization OK ({len(json_str)} bytes)")
except Exception:
    print("FAIL: Audit pipeline crashed:")
    traceback.print_exc()

# --- Part 3: Test BBA audit ---
bba_files = glob.glob("test_scenarios/bba_eligible_FIN.csv")
if bba_files:
    rows = []
    with open(bba_files[0], "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 5: continue
            if row[0].strip().lower() == "course_code": continue
            rows.append({
                "course_code": row[0].strip(), "course_name": row[1].strip(),
                "credits": row[2].strip(), "grade": row[3].strip(), "semester": row[4].strip(),
            })
    try:
        result = UnifiedAuditor.run_from_rows(rows, "BBA")
        if result["meta"]["fake_transcript"]:
            print(f"FAIL: BBA fake transcript: {result['meta']['unrecognized_courses']}")
        else:
            print(f"PASS: BBA audit — CGPA={result['level_2']['cgpa']:.2f}, Conc={result['meta']['concentration']}, Eligible={result['level_3']['eligible']}")
    except Exception:
        print("FAIL: BBA audit crashed:")
        traceback.print_exc()
