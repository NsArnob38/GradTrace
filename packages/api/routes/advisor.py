"""
GradeTrace API - Advisor Routes

Grounded advisor chat backed by deterministic MCP tool results.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Literal

import google.generativeai as genai
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field

from packages.api.config import get_settings
from packages.api.deps import get_current_user, success_response


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advisor", tags=["advisor"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CourseRecordInput(StrictModel):
    course_code: str = Field(..., min_length=2, max_length=20)
    credits: int = Field(..., ge=0, le=12)
    grade: str = Field(..., min_length=1, max_length=4)


class StudentRecordInput(StrictModel):
    student_id: str = Field(..., min_length=1, max_length=64)
    courses: list[CourseRecordInput] = Field(default_factory=list, max_length=1200)


class ProgramRequirementsInput(StrictModel):
    program_code: str = Field(..., min_length=1, max_length=32)
    total_credits_required: int = Field(..., ge=0, le=250)
    core_courses_required: list[str] = Field(default_factory=list, max_length=400)
    elective_credit_required: int = Field(default=0, ge=0, le=100)
    elective_pool: list[str] = Field(default_factory=list, max_length=800)


class AvailableCourseInput(StrictModel):
    course_code: str = Field(..., min_length=2, max_length=20)
    credits: int = Field(..., ge=0, le=12)
    category: Literal["CORE", "ELECTIVE", "GENERAL"] = "GENERAL"
    term: str | None = Field(default=None, max_length=32)


class ConversationTurn(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=1000)


class AdvisorRequest(StrictModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_history: list[ConversationTurn] = Field(default_factory=list, max_length=8)
    student_record: StudentRecordInput
    program_requirements: ProgramRequirementsInput
    available_courses: list[AvailableCourseInput] = Field(default_factory=list, max_length=1200)
    hypothetical_courses: list[CourseRecordInput] = Field(default_factory=list, max_length=60)


def _extract_text_response(response: Any) -> str:
    direct_text = getattr(response, "text", "") or ""
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text.strip()

    parts: list[str] = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            text = getattr(part, "text", None)
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())

    return "\n".join(parts).strip()


async def _call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    base_url = settings.mcp_server_url.strip().rstrip("/")
    if not base_url:
        raise HTTPException(status_code=503, detail="MCP server is not configured.")

    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(f"{base_url}/v1/mcp", json=payload)

    try:
        body = response.json() if response.content else {}
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"MCP returned invalid JSON for '{tool_name}'.") from exc

    if not response.is_success:
        raise HTTPException(status_code=502, detail=f"MCP call failed for '{tool_name}' ({response.status_code}).")

    if isinstance(body, dict) and body.get("error"):
        error = body["error"]
        message = error.get("message", "Unknown MCP error") if isinstance(error, dict) else "Unknown MCP error"
        raise HTTPException(status_code=502, detail=f"MCP tool '{tool_name}' failed: {message}")

    result = body.get("result", {}) if isinstance(body, dict) else {}
    structured = result.get("structuredContent", {}) if isinstance(result, dict) else {}
    return structured if isinstance(structured, dict) else {}


def _build_prompt(request: AdvisorRequest, tool_results: dict[str, Any]) -> str:
    chat_history = [turn.model_dump() for turn in request.conversation_history[-6:]]
    transcript_context = {
        "student_record": request.student_record.model_dump(),
        "program_requirements": request.program_requirements.model_dump(),
        "available_courses_count": len(request.available_courses),
        "hypothetical_courses": request.hypothetical_courses.model_dump(),
    }

    return (
        "You are the GradeTrace academic advisor.\n"
        "Rules:\n"
        "- Use only the MCP tool results provided below for any claim about eligibility, missing requirements, or plans.\n"
        "- Do not invent courses, deficits, or policies.\n"
        "- If the provided tool results are insufficient for the user's question, clearly say what is missing.\n"
        "- Keep the answer concise, student-friendly, and practical.\n"
        "- When referring to eligibility, cite the exact MCP outcome in plain language.\n\n"
        f"Conversation history: {json.dumps(chat_history, separators=(',', ':'))}\n"
        f"Latest user question: {request.message}\n"
        f"Request context: {json.dumps(transcript_context, separators=(',', ':'))}\n"
        f"Grounding MCP results: {json.dumps(tool_results, separators=(',', ':'))}\n\n"
        "Write a direct answer to the student."
    )


def _generate_grounded_answer(prompt: str) -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="Gemini API key is not configured.")

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.advisor_model)
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 700,
        },
    )

    text = _extract_text_response(response)
    if text:
        return text

    raise HTTPException(status_code=502, detail="Gemini returned an empty advisor response.")


@router.post("/chat")
async def advisor_chat(request: AdvisorRequest, user: dict = Depends(get_current_user)):
    tool_results: dict[str, Any] = {}

    base_tool_args = {
        "student_record": request.student_record.model_dump(),
        "program_requirements": request.program_requirements.model_dump(),
    }

    tool_results["audit_student"] = await _call_mcp_tool("audit_student", base_tool_args)

    if request.available_courses:
        planning_args = {
            **base_tool_args,
            "available_courses": [course.model_dump() for course in request.available_courses],
        }
        tool_results["plan_path"] = await _call_mcp_tool("plan_path", planning_args)
        tool_results["optimize_graduation_path"] = await _call_mcp_tool(
            "optimize_graduation_path",
            planning_args,
        )

    if request.hypothetical_courses:
        simulation_args = {
            **base_tool_args,
            "hypothetical_courses": [course.model_dump() for course in request.hypothetical_courses],
        }
        tool_results["simulate_changes"] = await _call_mcp_tool("simulate_changes", simulation_args)

    prompt = _build_prompt(request, tool_results)
    answer = await run_in_threadpool(_generate_grounded_answer, prompt)

    logger.info(
        "advisor_chat_completed user_id=%s tools=%s",
        user.get("id", "unknown"),
        sorted(tool_results.keys()),
    )

    return success_response(
        {
            "answer": answer,
            "tool_results": tool_results,
            "model": get_settings().advisor_model,
        }
    )
