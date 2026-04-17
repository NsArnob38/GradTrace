from __future__ import annotations

from dataclasses import dataclass

from schemas.models import (
    AuditIssue,
    AuditIssueType,
    AuditResult,
    CourseRecord,
    ExplainAuditResult,
    ProgramRequirements,
    StudentRecord,
)


GRADE_POINTS: dict[str, float] = {
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "C-": 1.7,
    "D+": 1.3,
    "D": 1.0,
    "F": 0.0,
    "P": 2.0,
    "T": 2.0,
}

PASSING_GRADES = {"A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "P", "T"}


@dataclass(frozen=True)
class NormalizedStudent:
    student_id: str
    courses: list[CourseRecord]
    deduped_courses: list[str]


def _is_passing(grade: str) -> bool:
    return grade in PASSING_GRADES


def _normalize_student_record(student_record: StudentRecord) -> NormalizedStudent:
    best_by_code: dict[str, CourseRecord] = {}
    seen_duplicates: set[str] = set()

    for course in student_record.courses:
        code = course.course_code
        current = best_by_code.get(code)
        if current is None:
            best_by_code[code] = course
            continue

        seen_duplicates.add(code)
        current_points = GRADE_POINTS.get(current.grade, -1.0)
        new_points = GRADE_POINTS.get(course.grade, -1.0)

        if new_points > current_points:
            best_by_code[code] = course
        elif new_points == current_points and course.credits > current.credits:
            best_by_code[code] = course

    normalized_courses = sorted(best_by_code.values(), key=lambda course: course.course_code)
    return NormalizedStudent(
        student_id=student_record.student_id,
        courses=normalized_courses,
        deduped_courses=sorted(seen_duplicates),
    )


def audit_student_record(student_record: StudentRecord, program_requirements: ProgramRequirements) -> AuditResult:
    normalized = _normalize_student_record(student_record)

    passed_courses = {
        course.course_code
        for course in normalized.courses
        if _is_passing(course.grade)
    }

    missing_core = [
        code
        for code in program_requirements.core_courses_required
        if code not in passed_courses
    ]

    earned_total_credits = sum(
        course.credits for course in normalized.courses if _is_passing(course.grade)
    )
    total_credit_deficit = max(0, program_requirements.total_credits_required - earned_total_credits)

    core_set = set(program_requirements.core_courses_required)
    elective_pool = set(program_requirements.elective_pool)
    earned_elective_credits = sum(
        course.credits
        for course in normalized.courses
        if _is_passing(course.grade)
        and course.course_code in elective_pool
        and course.course_code not in core_set
    )
    elective_credit_deficit = max(0, program_requirements.elective_credit_required - earned_elective_credits)

    missing_requirements: list[str] = []
    missing_requirements.extend(f"CORE:{code}" for code in missing_core)

    if total_credit_deficit > 0:
        missing_requirements.append(f"CREDIT_DEFICIT:{total_credit_deficit}")
    if elective_credit_deficit > 0:
        missing_requirements.append(f"ELECTIVE_CREDIT_DEFICIT:{elective_credit_deficit}")
    if normalized.deduped_courses:
        missing_requirements.append("DUPLICATES_RESOLVED:" + ",".join(normalized.deduped_courses))

    eligible = not missing_core and total_credit_deficit == 0 and elective_credit_deficit == 0

    return AuditResult(
        eligible=eligible,
        missing_requirements=missing_requirements,
        credit_deficit=total_credit_deficit,
        missing_core_courses=missing_core,
        elective_credit_deficit=elective_credit_deficit,
        earned_total_credits=earned_total_credits,
        earned_elective_credits=earned_elective_credits,
    )


def explain_audit_result(audit_result: AuditResult) -> ExplainAuditResult:
    issues: list[AuditIssue] = []

    for core_code in audit_result.missing_core_courses:
        issues.append(
            AuditIssue(
                issue_type=AuditIssueType.CORE_MISSING,
                detail=f"Required core course {core_code} has not been completed.",
                requirement_key=core_code,
            )
        )

    if audit_result.credit_deficit > 0:
        issues.append(
            AuditIssue(
                issue_type=AuditIssueType.CREDIT_DEFICIT,
                detail=f"Student is short by {audit_result.credit_deficit} total credits.",
                requirement_key="total_credits_required",
            )
        )

    if audit_result.elective_credit_deficit > 0:
        issues.append(
            AuditIssue(
                issue_type=AuditIssueType.ELECTIVE_SHORTAGE,
                detail=f"Student is short by {audit_result.elective_credit_deficit} elective credits.",
                requirement_key="elective_credit_required",
            )
        )

    if audit_result.eligible:
        summary = "Student is eligible for graduation. No unresolved requirement gaps were found."
    else:
        summary = f"Student is not yet eligible for graduation. Found {len(issues)} blocking issue(s)."

    return ExplainAuditResult(summary=summary, structured_issues=issues)


def simulate_changes_result(
    student_record: StudentRecord,
    hypothetical_courses: list[CourseRecord],
    program_requirements: ProgramRequirements,
) -> AuditResult:
    merged = StudentRecord(
        student_id=student_record.student_id,
        courses=[*student_record.courses, *hypothetical_courses],
    )
    return audit_student_record(merged, program_requirements)
