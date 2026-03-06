"""
GradeTrace API — Admin Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from packages.api.deps import require_admin, get_supabase_admin, success_response

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/students")
async def list_students(admin: dict = Depends(require_admin)):
    """List all students with their latest audit status."""
    db = get_supabase_admin()

    # Get all student profiles
    profiles = db.table("profiles") \
        .select("id, full_name, student_id, email, program, bba_concentration, created_at") \
        .eq("role", "student") \
        .order("created_at", desc=True) \
        .execute()

    students = profiles.data or []

    # Attach latest scan summary to each student
    for student in students:
        history = db.table("scan_history") \
            .select("summary, scanned_at") \
            .eq("user_id", student["id"]) \
            .order("scanned_at", desc=True) \
            .limit(1) \
            .execute()
        student["latest_audit"] = history.data[0] if history.data else None

    return success_response(students)


@router.get("/students/{student_id}")
async def get_student_detail(student_id: str, admin: dict = Depends(require_admin)):
    """Get a student's full profile and all audit history."""
    db = get_supabase_admin()

    profile = db.table("profiles") \
        .select("*") \
        .eq("id", student_id) \
        .single() \
        .execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Student not found")

    history = db.table("scan_history") \
        .select("*") \
        .eq("user_id", student_id) \
        .order("scanned_at", desc=True) \
        .execute()

    latest_audit = None
    if history.data:
        latest = db.table("audit_results") \
            .select("*") \
            .eq("id", history.data[0].get("audit_result_id")) \
            .single() \
            .execute()
        latest_audit = latest.data

    return success_response({
        "profile": profile.data,
        "history": history.data or [],
        "latest_audit": latest_audit,
    })


@router.get("/programs")
async def list_programs(admin: dict = Depends(require_admin)):
    """Get all curriculum data."""
    db = get_supabase_admin()
    result = db.table("programs").select("*").execute()
    return success_response(result.data)


@router.put("/programs")
async def update_programs(
    entries: list[dict] = Body(...),
    admin: dict = Depends(require_admin),
):
    """Update/insert curriculum entries."""
    db = get_supabase_admin()
    for entry in entries:
        required = {"program_code", "course_code", "course_name", "credits", "category"}
        if not required.issubset(entry.keys()):
            raise HTTPException(status_code=400, detail=f"Missing fields in entry: {entry}")

    # Upsert: delete existing, re-insert
    if entries:
        program_codes = list(set(e["program_code"] for e in entries))
        for pc in program_codes:
            db.table("programs").delete().eq("program_code", pc).execute()
        db.table("programs").insert(entries).execute()

    return success_response({"updated": len(entries)})
