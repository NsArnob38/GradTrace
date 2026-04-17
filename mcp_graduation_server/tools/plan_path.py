from audit_engine.planner import plan_path_to_graduation
from schemas.models import PlanPathInput, PlanPathResult


def run_tool(payload: PlanPathInput) -> PlanPathResult:
    return plan_path_to_graduation(
        student_record=payload.student_record,
        program_requirements=payload.program_requirements,
        available_courses=payload.available_courses,
    )
