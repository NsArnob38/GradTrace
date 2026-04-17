from audit_engine.engine import explain_audit_result
from schemas.models import ExplainAuditInput, ExplainAuditResult


def run_tool(payload: ExplainAuditInput) -> ExplainAuditResult:
    return explain_audit_result(payload.audit_result)
