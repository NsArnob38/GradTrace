from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


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


class CourseRecord(BaseModel):
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


class StudentRecord(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=64)
    courses: list[CourseRecord] = Field(default_factory=list)


class ProgramRequirements(BaseModel):
    program_code: str = Field(..., min_length=1, max_length=32)
    total_credits_required: int = Field(..., ge=0, le=250)
    core_courses_required: list[str] = Field(default_factory=list)
    elective_credit_required: int = Field(default=0, ge=0, le=100)
    elective_pool: list[str] = Field(default_factory=list)

    @field_validator("core_courses_required", "elective_pool")
    @classmethod
    def normalize_course_list(cls, value: list[str]) -> list[str]:
        normalized = [item.strip().upper().replace(" ", "") for item in value if item.strip()]
        return sorted(set(normalized))


class ToolAuditStudentInput(BaseModel):
    student_record: StudentRecord
    program_requirements: ProgramRequirements


class AuditIssueType(str, Enum):
    CORE_MISSING = "CORE_MISSING"
    CREDIT_DEFICIT = "CREDIT_DEFICIT"
    ELECTIVE_SHORTAGE = "ELECTIVE_SHORTAGE"


class AuditIssue(BaseModel):
    issue_type: AuditIssueType
    detail: str
    requirement_key: str


class AuditResult(BaseModel):
    eligible: bool
    missing_requirements: list[str]
    credit_deficit: int
    missing_core_courses: list[str] = Field(default_factory=list)
    elective_credit_deficit: int = 0
    earned_total_credits: int = 0
    earned_elective_credits: int = 0


class ExplainAuditInput(BaseModel):
    audit_result: AuditResult


class ExplainAuditResult(BaseModel):
    summary: str
    structured_issues: list[AuditIssue]


class AvailableCourse(BaseModel):
    course_code: str = Field(..., min_length=2, max_length=20)
    credits: int = Field(..., ge=0, le=12)
    term: str | None = None
    category: Literal["CORE", "ELECTIVE", "GENERAL"] = "GENERAL"

    @field_validator("course_code")
    @classmethod
    def normalize_available_code(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "")


class PlanPathInput(BaseModel):
    student_record: StudentRecord
    program_requirements: ProgramRequirements
    available_courses: list[AvailableCourse]


class PlanPathResult(BaseModel):
    recommended_courses: list[str]
    reasoning: str


class SimulateChangesInput(BaseModel):
    student_record: StudentRecord
    hypothetical_courses: list[CourseRecord]
    program_requirements: ProgramRequirements


class SimulateChangesResult(BaseModel):
    eligible_after: bool
    remaining_requirements: list[str]


class OptimizeGraduationPathInput(BaseModel):
    student_record: StudentRecord
    program_requirements: ProgramRequirements
    available_courses: list[AvailableCourse]


class OptimizeGraduationPathResult(BaseModel):
    minimum_course_set: list[str]
    estimated_remaining_credits: int
    rationale: str
