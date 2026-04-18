from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel

from schemas.models import (
    AuditResult,
    ExplainAuditInput,
    ExplainAuditResult,
    OptimizeGraduationPathInput,
    OptimizeGraduationPathResult,
    PlanPathInput,
    PlanPathResult,
    SimulateChangesInput,
    SimulateChangesResult,
    ToolAuditStudentInput,
)
from tools import audit_student, explain_audit, optimize_graduation_path, plan_path, simulate_changes


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    handler: Callable[[BaseModel], BaseModel]
    safe_for_agent: bool = True
    mutates_state: bool = False

    def to_mcp_descriptor(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_model.model_json_schema(),
            "outputSchema": self.output_model.model_json_schema(),
            "annotations": {
                "safeForAgent": self.safe_for_agent,
                "readOnlyHint": not self.mutates_state,
            },
        }


def get_tool_registry() -> dict[str, ToolSpec]:
    return {
        "audit_student": ToolSpec(
            name="audit_student",
            description="Evaluate graduation eligibility using student record and program requirements.",
            input_model=ToolAuditStudentInput,
            output_model=AuditResult,
            handler=audit_student.run_tool,
        ),
        "explain_audit": ToolSpec(
            name="explain_audit",
            description="Convert audit output into typed, agent-friendly issue list.",
            input_model=ExplainAuditInput,
            output_model=ExplainAuditResult,
            handler=explain_audit.run_tool,
        ),
        "plan_path": ToolSpec(
            name="plan_path",
            description="Recommend an ordered set of courses to close graduation gaps.",
            input_model=PlanPathInput,
            output_model=PlanPathResult,
            handler=plan_path.run_tool,
        ),
        "simulate_changes": ToolSpec(
            name="simulate_changes",
            description="Apply hypothetical courses and return updated eligibility and remaining requirements.",
            input_model=SimulateChangesInput,
            output_model=SimulateChangesResult,
            handler=simulate_changes.run_tool,
        ),
        "optimize_graduation_path": ToolSpec(
            name="optimize_graduation_path",
            description="Compute minimum-course greedy path to satisfy deficits from available courses.",
            input_model=OptimizeGraduationPathInput,
            output_model=OptimizeGraduationPathResult,
            handler=optimize_graduation_path.run_tool,
        ),
    }
