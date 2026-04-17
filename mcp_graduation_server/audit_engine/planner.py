from __future__ import annotations

from audit_engine.engine import audit_student_record
from schemas.models import (
    AvailableCourse,
    OptimizeGraduationPathResult,
    PlanPathResult,
    ProgramRequirements,
    StudentRecord,
)


def _index_available_courses(available_courses: list[AvailableCourse]) -> dict[str, AvailableCourse]:
    indexed: dict[str, AvailableCourse] = {}
    for course in available_courses:
        if course.course_code not in indexed:
            indexed[course.course_code] = course
    return indexed


def plan_path_to_graduation(
    student_record: StudentRecord,
    program_requirements: ProgramRequirements,
    available_courses: list[AvailableCourse],
) -> PlanPathResult:
    audit = audit_student_record(student_record, program_requirements)
    indexed = _index_available_courses(available_courses)

    recommendations: list[str] = []

    for core_code in audit.missing_core_courses:
        if core_code in indexed:
            recommendations.append(core_code)

    elective_deficit = audit.elective_credit_deficit
    if elective_deficit > 0:
        elective_candidates = [
            course
            for code, course in indexed.items()
            if code in set(program_requirements.elective_pool)
            and code not in recommendations
        ]
        elective_candidates.sort(key=lambda course: (-course.credits, course.course_code))

        for course in elective_candidates:
            if elective_deficit <= 0:
                break
            recommendations.append(course.course_code)
            elective_deficit -= course.credits

    remaining_total_deficit = audit.credit_deficit
    if remaining_total_deficit > 0:
        filler_candidates = [course for code, course in indexed.items() if code not in recommendations]
        filler_candidates.sort(key=lambda course: (-course.credits, course.course_code))
        for course in filler_candidates:
            if remaining_total_deficit <= 0:
                break
            recommendations.append(course.course_code)
            remaining_total_deficit -= course.credits

    recommendations = list(dict.fromkeys(recommendations))

    if not recommendations and audit.eligible:
        reasoning = "Student is already eligible. No additional courses are required."
    else:
        reasoning = (
            "Recommendations prioritize missing core courses, then elective deficit coverage, "
            "then remaining total credit deficit."
        )

    return PlanPathResult(recommended_courses=recommendations, reasoning=reasoning)


def optimize_graduation_path(
    student_record: StudentRecord,
    program_requirements: ProgramRequirements,
    available_courses: list[AvailableCourse],
) -> OptimizeGraduationPathResult:
    audit = audit_student_record(student_record, program_requirements)
    indexed = _index_available_courses(available_courses)

    selected: list[str] = []
    selected_credits = 0

    unavailable_core: list[str] = []
    for core_code in audit.missing_core_courses:
        course = indexed.get(core_code)
        if not course:
            unavailable_core.append(core_code)
            continue
        selected.append(core_code)
        selected_credits += course.credits

    elective_needed = audit.elective_credit_deficit
    total_needed = max(0, audit.credit_deficit - selected_credits)

    elective_candidates = [
        course
        for course in indexed.values()
        if course.course_code in set(program_requirements.elective_pool)
        and course.course_code not in selected
    ]
    elective_candidates.sort(key=lambda course: (-course.credits, course.course_code))

    for course in elective_candidates:
        if elective_needed <= 0 and total_needed <= 0:
            break
        selected.append(course.course_code)
        selected_credits += course.credits
        elective_needed = max(0, elective_needed - course.credits)
        total_needed = max(0, total_needed - course.credits)

    if total_needed > 0:
        filler_candidates = [course for course in indexed.values() if course.course_code not in selected]
        filler_candidates.sort(key=lambda course: (-course.credits, course.course_code))
        for course in filler_candidates:
            if total_needed <= 0:
                break
            selected.append(course.course_code)
            selected_credits += course.credits
            total_needed = max(0, total_needed - course.credits)

    selected = list(dict.fromkeys(selected))

    blocking = []
    if unavailable_core:
        blocking.append(f"Unavailable missing core courses: {', '.join(sorted(unavailable_core))}")
    if elective_needed > 0:
        blocking.append(f"Unmet elective credits after optimization: {elective_needed}")
    if total_needed > 0:
        blocking.append(f"Unmet total credits after optimization: {total_needed}")

    if blocking:
        rationale = "Optimization completed with unresolved constraints. " + " | ".join(blocking)
    else:
        rationale = (
            "Optimization found a minimum-course greedy path that satisfies current deficits "
            "using available offerings."
        )

    return OptimizeGraduationPathResult(
        minimum_course_set=selected,
        estimated_remaining_credits=total_needed,
        rationale=rationale,
    )
