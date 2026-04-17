# Graduation Audit MCP Server

Deterministic MCP server for graduation audit logic used by AI agents.

## Structure

```text
mcp_graduation_server/
  audit_engine/
  schemas/
  tools/
  server.py
  requirements.txt
```

## Run

```bash
cd mcp_graduation_server
pip install -r requirements.txt
uvicorn server:app --reload --port 8100
```

## MCP endpoints

- `POST /mcp` (JSON-RPC)
  - `initialize`
  - `tools/list`
  - `tools/call`

## Tool examples

### `audit_student`

```json
{
  "name": "audit_student",
  "arguments": {
    "student_record": {
      "student_id": "S-1001",
      "courses": [
        {"course_code": "CSE101", "credits": 3, "grade": "A"},
        {"course_code": "MAT120", "credits": 3, "grade": "B"}
      ]
    },
    "program_requirements": {
      "program_code": "BSCS",
      "total_credits_required": 12,
      "core_courses_required": ["CSE101", "CSE102"],
      "elective_credit_required": 3,
      "elective_pool": ["HUM101", "SOC101"]
    }
  }
}
```

```json
{
  "eligible": false,
  "missing_requirements": ["CORE:CSE102", "CREDIT_DEFICIT:6", "ELECTIVE_CREDIT_DEFICIT:3"],
  "credit_deficit": 6,
  "missing_core_courses": ["CSE102"],
  "elective_credit_deficit": 3,
  "earned_total_credits": 6,
  "earned_elective_credits": 0
}
```

### `explain_audit`

```json
{
  "name": "explain_audit",
  "arguments": {
    "audit_result": {
      "eligible": false,
      "missing_requirements": ["CORE:CSE102", "CREDIT_DEFICIT:6", "ELECTIVE_CREDIT_DEFICIT:3"],
      "credit_deficit": 6,
      "missing_core_courses": ["CSE102"],
      "elective_credit_deficit": 3,
      "earned_total_credits": 6,
      "earned_elective_credits": 0
    }
  }
}
```

```json
{
  "summary": "Student is not yet eligible for graduation. Found 3 blocking issue(s).",
  "structured_issues": [
    {"issue_type": "CORE_MISSING", "detail": "Required core course CSE102 has not been completed.", "requirement_key": "CSE102"},
    {"issue_type": "CREDIT_DEFICIT", "detail": "Student is short by 6 total credits.", "requirement_key": "total_credits_required"},
    {"issue_type": "ELECTIVE_SHORTAGE", "detail": "Student is short by 3 elective credits.", "requirement_key": "elective_credit_required"}
  ]
}
```

### `plan_path`

```json
{
  "name": "plan_path",
  "arguments": {
    "student_record": {"student_id": "S-1001", "courses": [{"course_code": "CSE101", "credits": 3, "grade": "A"}]},
    "program_requirements": {
      "program_code": "BSCS",
      "total_credits_required": 9,
      "core_courses_required": ["CSE101", "CSE102"],
      "elective_credit_required": 3,
      "elective_pool": ["SOC101"]
    },
    "available_courses": [
      {"course_code": "CSE102", "credits": 3, "category": "CORE", "term": "Fall"},
      {"course_code": "SOC101", "credits": 3, "category": "ELECTIVE", "term": "Fall"}
    ]
  }
}
```

```json
{
  "recommended_courses": ["CSE102", "SOC101"],
  "reasoning": "Recommendations prioritize missing core courses, then elective deficit coverage, then remaining total credit deficit."
}
```

### `simulate_changes`

```json
{
  "name": "simulate_changes",
  "arguments": {
    "student_record": {"student_id": "S-1001", "courses": [{"course_code": "CSE101", "credits": 3, "grade": "A"}]},
    "hypothetical_courses": [
      {"course_code": "CSE102", "credits": 3, "grade": "B"},
      {"course_code": "SOC101", "credits": 3, "grade": "B"}
    ],
    "program_requirements": {
      "program_code": "BSCS",
      "total_credits_required": 9,
      "core_courses_required": ["CSE101", "CSE102"],
      "elective_credit_required": 3,
      "elective_pool": ["SOC101"]
    }
  }
}
```

```json
{
  "eligible_after": true,
  "remaining_requirements": []
}
```

### `optimize_graduation_path`

```json
{
  "name": "optimize_graduation_path",
  "arguments": {
    "student_record": {"student_id": "S-1001", "courses": [{"course_code": "CSE101", "credits": 3, "grade": "A"}]},
    "program_requirements": {
      "program_code": "BSCS",
      "total_credits_required": 9,
      "core_courses_required": ["CSE101", "CSE102"],
      "elective_credit_required": 3,
      "elective_pool": ["SOC101"]
    },
    "available_courses": [
      {"course_code": "CSE102", "credits": 3, "category": "CORE"},
      {"course_code": "SOC101", "credits": 3, "category": "ELECTIVE"}
    ]
  }
}
```

```json
{
  "minimum_course_set": ["CSE102", "SOC101"],
  "estimated_remaining_credits": 0,
  "rationale": "Optimization found a minimum-course greedy path that satisfies current deficits using available offerings."
}
```
