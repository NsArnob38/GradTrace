from audit_engine.engine import audit_student_record
from schemas.models import AuditResult, ToolAuditStudentInput


def run_tool(payload: ToolAuditStudentInput) -> AuditResult:
    return audit_student_record(payload.student_record, payload.program_requirements)
