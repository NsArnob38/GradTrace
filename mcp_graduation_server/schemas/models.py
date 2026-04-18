from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


VALID_GRADES = {
    "A",
    "A-",
    "B+",
    "B",
    "B-",
    "C+",
    "C",
    "C-",
    "D+",
    "D",
    "F",
    "P",
    "T",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CourseRecord(StrictModel):
    course_code: str = Field(..., min_length=2, max_length=20)
    credits: int = Field(..., ge=0, le=12)
    grade: str = Field(...)

    @field_validator("course_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "")

    @field_validator("grade")
    @classmethod
    def normalize_grade(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in VALID_GRADES:
            raise ValueError(f"Invalid grade '{value}'. Allowed: {sorted(VALID_GRADES)}")
        return normalized


class StudentRecord(StrictModel):
    student_id: str = Field(..., min_length=1, max_length=64)
    courses: list[CourseRecord] = Field(default_factory=list, max_length=1200)


class ProgramRequirements(StrictModel):
    program_code: str = Field(..., min_length=1, max_length=32)
    total_credits_required: int = Field(..., ge=0, le=250)
    core_courses_required: list[str] = Field(default_factory=list, max_length=400)
    elective_credit_required: int = Field(default=0, ge=0, le=100)
    elective_pool: list[str] = Field(default_factory=list, max_length=800)

    @field_validator("core_courses_required", "elective_pool")
    @classmethod
    def normalize_course_list(cls, value: list[str]) -> list[str]:
        normalized = [item.strip().upper().replace(" ", "") for item in value if item.strip()]
        return sorted(set(normalized))

    @model_validator(mode="after")
    def validate_credit_policy(self) -> "ProgramRequirements":
        if self.elective_credit_required > self.total_credits_required:
            raise ValueError("elective_credit_required cannot exceed total_credits_required")
        return self


class ToolAuditStudentInput(StrictModel):
    student_record: StudentRecord
    program_requirements: ProgramRequirements


class AuditIssueType(str, Enum):
    CORE_MISSING = "CORE_MISSING"
    CREDIT_DEFICIT = "CREDIT_DEFICIT"
    ELECTIVE_SHORTAGE = "ELECTIVE_SHORTAGE"


class AuditIssue(StrictModel):
    issue_type: AuditIssueType
    detail: str
    requirement_key: str


class AuditResult(StrictModel):
    eligible: bool
    missing_requirements: list[str] = Field(max_length=2000)
    credit_deficit: int = Field(ge=0)
    missing_core_courses: list[str] = Field(default_factory=list)
    elective_credit_deficit: int = Field(default=0, ge=0)
    earned_total_credits: int = Field(default=0, ge=0)
    earned_elective_credits: int = Field(default=0, ge=0)


class ExplainAuditInput(StrictModel):
    audit_result: AuditResult


class ExplainAuditResult(StrictModel):
    summary: str
    structured_issues: list[AuditIssue]


class AvailableCourse(StrictModel):
    course_code: str = Field(..., min_length=2, max_length=20)
    credits: int = Field(..., ge=0, le=12)
    term: str | None = Field(default=None, max_length=32)
    category: Literal["CORE", "ELECTIVE", "GENERAL"] = "GENERAL"

    @field_validator("course_code")
    @classmethod
    def normalize_available_code(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "")


class PlanPathInput(StrictModel):
    student_record: StudentRecord
    program_requirements: ProgramRequirements
    available_courses: list[AvailableCourse] = Field(max_length=1200)


class PlanPathResult(StrictModel):
    recommended_courses: list[str] = Field(max_length=1200)
    reasoning: str = Field(max_length=300)


class SimulateChangesInput(StrictModel):
    student_record: StudentRecord
    hypothetical_courses: list[CourseRecord] = Field(max_length=400)
    program_requirements: ProgramRequirements


class SimulateChangesResult(StrictModel):
    eligible_after: bool
    remaining_requirements: list[str] = Field(max_length=2000)


class OptimizeGraduationPathInput(StrictModel):
    student_record: StudentRecord
    program_requirements: ProgramRequirements
    available_courses: list[AvailableCourse] = Field(max_length=1200)


class OptimizeGraduationPathResult(StrictModel):
    minimum_course_set: list[str] = Field(max_length=1200)
    estimated_remaining_credits: int = Field(ge=0)
    rationale: str = Field(max_length=400)
