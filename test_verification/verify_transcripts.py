import sys
import os

# Add the project root to sys.path to allow imports from 'packages'
sys.path.append(os.getcwd())

from packages.core.unified import UnifiedAuditor

def run_verify():
    test_cases = [
        {"path": "test_verification/cse_eligible.csv", "program": "CSE", "expected": True, "label": "CSE Eligible"},
        {"path": "test_verification/cse_ineligible.csv", "program": "CSE", "expected": False, "label": "CSE Ineligible"},
        {"path": "test_verification/bba_eligible.csv", "program": "BBA", "expected": True, "label": "BBA Eligible", "conc": "INB"},
        {"path": "test_verification/bba_ineligible.csv", "program": "BBA", "expected": False, "label": "BBA Ineligible", "conc": "FIN"},
    ]

    print("\n" + "="*80)
    print(f"{'Test Case':<20} | {'Program':<8} | {'Expected':<10} | {'Actual':<10} | {'Status':<10}")
    print("-" * 80)

    pass_count = 0
    for case in test_cases:
        try:
            # Full audit pipeline
            result = UnifiedAuditor.run_from_file(
                case["path"], 
                case["program"], 
                concentration=case.get("conc")
            )
            
            actual = result["level_3"]["eligible"]
            status = "PASS" if actual == case["expected"] else "FAIL"
            if status == "PASS": pass_count += 1

            print(f"{case['label']:<20} | {case['program']:<8} | {str(case['expected']):<10} | {str(actual):<10} | {status:<10}")
            
            if not actual and case["expected"]:
                print(f"   [!] Audit failed unnecessarily. Reasons: {result['level_3']['reasons']}")
                print(f"   [!] Missing Courses: {result['level_3'].get('remaining', {})}")
            elif actual and not case["expected"]:
                print(f"   [!] Audit passed despite being ineligible!")
            elif not actual:
                # Expected failure, just print the top reason for info
                first_reason = result["level_3"]["reasons"][0] if result["level_3"]["reasons"] else "Unknown"
                print(f"   (Info) Rejection Reason: {first_reason}")

        except Exception as e:
            print(f"{case['label']:<20} | {case['program']:<8} | ERROR: {str(e)}")

    print("-" * 80)
    print(f"FINAL RESULT: {pass_count}/{len(test_cases)} tests passed.")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_verify()
