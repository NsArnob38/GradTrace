from audit_engine.engine import simulate_changes_result
from schemas.models import SimulateChangesInput, SimulateChangesResult


def run_tool(payload: SimulateChangesInput) -> SimulateChangesResult:
    audit = simulate_changes_result(
        student_record=payload.student_record,
        hypothetical_courses=payload.hypothetical_courses,
        program_requirements=payload.program_requirements,
    )
    return SimulateChangesResult(
        eligible_after=audit.eligible,
        remaining_requirements=audit.missing_requirements,
    )
