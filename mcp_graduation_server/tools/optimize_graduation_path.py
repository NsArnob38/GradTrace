from audit_engine.planner import optimize_graduation_path
from schemas.models import OptimizeGraduationPathInput, OptimizeGraduationPathResult


def run_tool(payload: OptimizeGraduationPathInput) -> OptimizeGraduationPathResult:
    return optimize_graduation_path(
        student_record=payload.student_record,
        program_requirements=payload.program_requirements,
        available_courses=payload.available_courses,
    )
