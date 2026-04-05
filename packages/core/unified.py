"""
GradeTrace Core — Unified Auditor

Runs the full audit pipeline (Level 1 → Level 2 → Level 3 → Roadmap)
and returns a combined report.

This is the primary entry point for the API, CLI, and mobile apps.
"""

import os
from packages.core.models import CourseRecord
from packages.core.credit_engine import CreditAuditor
from packages.core.cgpa_engine import CGPAAuditor
from packages.core.audit_engine import GraduationAuditor
from packages.core.course_catalog import CourseCatalog
from packages.core.pdf_parser import VisionParser


class UnifiedAuditor:
    """Runs all three audit levels and produces a combined report + roadmap."""

    @staticmethod
    def run_from_file(filepath: str, program: str,
                      concentration: str | None = None,
                      user_waivers: dict | None = None,
                      custom_mappings: dict | None = None,
                      ignored_courses: list[str] | None = None) -> dict:
        """
        Full audit pipeline from a file path (CSV, PDF, or Image).
        """
        ext = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""
        
        if ext in ("pdf", "jpg", "jpeg", "png", "webp"):
            # Vision path (requires GEMINI_API_KEY)
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required for PDF/Image parsing.")
            
            with open(filepath, "rb") as f:
                file_bytes = f.read()
            
            parse_result = VisionParser.parse(file_bytes, api_key, filename=filepath)
            rows = parse_result["courses"]
            detected_prog = parse_result["program"]
            
            # If program is CSE (the default) or UNKNOWN, but AI detected BBA, switch to BBA
            if (program.upper() == "CSE" or program.upper() == "UNKNOWN") and detected_prog == "BBA":
                program = "BBA"
            # Vice-versa (though less likely)
            elif (program.upper() == "BBA" or program.upper() == "UNKNOWN") and detected_prog == "CSE":
                program = "CSE"

            return UnifiedAuditor.run_from_rows(
                rows, program, concentration, user_waivers, 
                custom_mappings, ignored_courses
            )
            
        # Standard CSV path
        level_1 = CreditAuditor.process(filepath, custom_mappings, ignored_courses)
        records = level_1["records"]
        credits_earned = level_1["credits_earned"]

        # Bail on fake transcripts
        if level_1["unrecognized"]:
            return {
                "meta": {
                    "program": program.upper(),
                    "concentration": concentration,
                    "fake_transcript": True,
                    "unrecognized_courses": list(level_1["unrecognized"]),
                },
                "level_1": {
                    "credits_attempted": level_1["credits_attempted"],
                    "credits_earned": credits_earned,
                },
                "level_2": None,
                "level_3": None,
                "roadmap": None,
            }

        return UnifiedAuditor._run_pipeline(
            records, program, credits_earned,
            level_1["credits_attempted"], concentration, user_waivers,
        )

    @staticmethod
    def run_from_rows(rows: list[dict], program: str,
                      concentration: str | None = None,
                      user_waivers: dict | None = None,
                      custom_mappings: dict | None = None,
                      ignored_courses: list[str] | None = None) -> dict:
        """
        Full audit pipeline from pre-parsed dict rows (API/DB path).

        Each row must have: course_code, course_name, credits, grade, semester.
        Returns dict with: level_1, level_2, level_3, roadmap, meta.
        """
        level_1 = CreditAuditor.process_rows(rows, custom_mappings, ignored_courses)
        records = level_1["records"]
        credits_earned = level_1["credits_earned"]

        if level_1["unrecognized"]:
            return {
                "meta": {
                    "program": program.upper(),
                    "concentration": concentration,
                    "fake_transcript": True,
                    "unrecognized_courses": list(level_1["unrecognized"]),
                },
                "level_1": {
                    "credits_attempted": level_1["credits_attempted"],
                    "credits_earned": credits_earned,
                },
                "level_2": None,
                "level_3": None,
                "roadmap": None,
            }

        return UnifiedAuditor._run_pipeline(
            records, program, credits_earned,
            level_1["credits_attempted"], concentration, user_waivers,
        )

    @staticmethod
    def _run_pipeline(records: list[CourseRecord], program: str,
                      credits_earned: int, credits_attempted: int,
                      concentration: str | None = None,
                      user_waivers: dict | None = None) -> dict:
        """Internal: run Level 2 + Level 3 + Roadmap on resolved records."""
        program = program.upper()

        # Auto-detect BBA concentration from records if not specified
        if program == "BBA" and concentration is None:
            concentration = UnifiedAuditor._detect_concentration(records)

        # Level 2: CGPA + standing
        cgpa_data = CGPAAuditor.process(records, program, user_waivers)

        # Level 3: Graduation audit
        audit_result = GraduationAuditor.audit(
            records, program,
            cgpa_data["waivers"],
            credits_earned,
            cgpa_data["cgpa"],
            cgpa_data.get("credit_reduction", 0),
            concentration=concentration,
        )

        # Roadmap
        if program == "CSE":
            major_cgpa = audit_result.get("major_core_cgpa", 0.0)
        else:
            major_cgpa = audit_result.get("core_cgpa", 0.0)

        roadmap = GraduationAuditor.build_graduation_roadmap(
            program, records, credits_earned,
            cgpa_data["cgpa"], major_cgpa,
            audit_result, cgpa_data["standing"],
        )

        # Serialize records for JSON output
        records_serialized = [r.to_dict() for r in records]

        return {
            "meta": {
                "program": program,
                "concentration": concentration,
                "fake_transcript": False,
                "unrecognized_courses": [],
            },
            "level_1": {
                "credits_attempted": credits_attempted,
                "credits_earned": credits_earned,
                "records": records_serialized,
            },
            "level_2": {
                "cgpa": cgpa_data["cgpa"],
                "quality_points": cgpa_data["quality_points"],
                "gpa_credits": cgpa_data["gpa_credits"],
                "standing": cgpa_data["standing"],
                "probation_count": cgpa_data["probation_count"],
                "waivers": cgpa_data["waivers"],
                "credit_reduction": cgpa_data["credit_reduction"],
            },
            "level_3": {
                "eligible": audit_result["eligible"],
                "reasons": audit_result["reasons"],
                "remaining": audit_result.get("remaining", {}),
                "total_credits_required": audit_result["total_credits_required"],
                "prereq_violations": audit_result.get("prereq_violations", []),
                # Program-specific CGPAs
                **({"major_core_cgpa": audit_result.get("major_core_cgpa", 0.0),
                    "major_elective_cgpa": audit_result.get("major_elective_cgpa", 0.0)}
                   if program == "CSE" else
                   {"core_cgpa": audit_result.get("core_cgpa", 0.0),
                    "concentration_cgpa": audit_result.get("concentration_cgpa", 0.0),
                    "concentration_label": audit_result.get("concentration_label", "Undeclared")}),
            },
            "roadmap": roadmap,
        }

    @staticmethod
    def _detect_concentration(records: list[CourseRecord]) -> str | None:
        """Attempt to detect BBA concentration from course codes in transcript."""
        passed_codes = {r.course_code for r in records
                        if r.status in ("BEST", "WAIVED") and r.grade not in ("F", "I", "W")}
        best_match = None
        best_count = 0
        for code, (req, elec, label) in CourseCatalog.BBA_CONCENTRATIONS.items():
            all_conc = set(req.keys()) | set(elec.keys())
            count = len(passed_codes & all_conc)
            if count > best_count:
                best_count = count
                best_match = code
        return best_match if best_count >= 2 else None
