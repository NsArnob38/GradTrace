"""
GradeTrace API — Audit Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from packages.api.curriculum_sync import sync_course_catalog_with_supabase
from packages.api.deps import get_current_user, get_supabase_admin, success_response

router = APIRouter(prefix="/audit", tags=["audit"])


from pydantic import BaseModel, Field

class AuditRequest(BaseModel):
    program: str = Field(default="CSE", description="e.g. 'CSE' or 'BBA'")
    concentration: str | None = Field(default=None, description="Major concentration for BBA")
    custom_mappings: dict[str, str] | None = Field(default=None, description="Overrides for legacy courses")
    ignored_courses: list[str] | None = Field(default=None, description="Courses to exclude from processing")

@router.post("/{transcript_id}")
def run_audit(
    transcript_id: str,
    req: AuditRequest,
    user: dict = Depends(get_current_user),
):
    """Run the audit engine on a transcript and store the result."""
    program = req.program
    concentration = req.concentration
    db = get_supabase_admin()
    user_id = user["id"]

    # Fetch transcript (owned by this user)
    transcript = db.table("transcripts") \
        .select("*") \
        .eq("id", transcript_id) \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    if not transcript.data:
        raise HTTPException(status_code=404, detail="Transcript not found")

    raw_data = transcript.data.get("raw_data", [])
    if not raw_data:
        raise HTTPException(status_code=400, detail="Transcript has no course data")

    sync_course_catalog_with_supabase(db)

    # Run audit engine
    from packages.core.unified import UnifiedAuditor
    result = UnifiedAuditor.run_from_rows(
        raw_data, 
        program, 
        concentration=concentration,
        custom_mappings=req.custom_mappings,
        ignored_courses=req.ignored_courses
    )

    if result["meta"]["fake_transcript"]:
        raise HTTPException(
            status_code=400,
            detail=f"Fake transcript detected. Unrecognized courses: {', '.join(result['meta']['unrecognized_courses'])}"
        )

    # Store audit result
    audit_record = db.table("audit_results").insert({
        "transcript_id": transcript_id,
        "user_id": user_id,
        "level_1": result["level_1"],
        "level_2": result["level_2"],
        "level_3": result["level_3"],
        "roadmap": result["roadmap"],
    }).execute()

    audit_data = audit_record.data[0] if audit_record.data else {}

    # Prepare summary
    summary = {
        "cgpa": float(result["level_2"]["cgpa"]),
        "earned_credits": result["level_1"]["credits_earned"],
        "probation_phase": result["level_2"]["standing"],
        "graduation_eligible": result["level_3"]["eligible"],
    }

    # Save to scan history (Non-critical, wrap in try/except)
    try:
        db.table("scan_history").insert({
            "user_id": user_id,
            "transcript_id": transcript_id,
            "audit_result_id": audit_data.get("id"),
            "input_type": "csv",
            "file_name": transcript.data.get("file_name", ""),
            "summary": summary,
        }).execute()
    except Exception as e:
        print(f"DEBUG: Warning: Failed to save scan history: {str(e)}")

    return success_response({
        "audit_result_id": audit_data.get("id"),
        **result,
    })


@router.get("/{transcript_id}")
def get_audit_result(
    transcript_id: str,
    user: dict = Depends(get_current_user),
):
    """Get cached audit result for a transcript."""
    db = get_supabase_admin()

    result = db.table("audit_results") \
        .select("*") \
        .eq("transcript_id", transcript_id) \
        .eq("user_id", user["id"]) \
        .order("generated_at", desc=True) \
        .limit(1) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="No audit result found. Run POST /audit/{transcript_id} first.")

    return success_response(result.data[0])


@router.get("")
def list_scan_history(user: dict = Depends(get_current_user)):
    """List audit/scan history for the current user."""
    db = get_supabase_admin()
    result = db.table("scan_history") \
        .select("*") \
        .eq("user_id", user["id"]) \
        .order("scanned_at", desc=True) \
        .execute()
    return success_response(result.data)


@router.delete("/{transcript_id}")
def delete_audit(
    transcript_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete an audit result, its history, and the transcript."""
    db = get_supabase_admin()
    user_id = user["id"]

    db.table("scan_history").delete().eq("transcript_id", transcript_id).eq("user_id", user_id).execute()
    db.table("audit_results").delete().eq("transcript_id", transcript_id).eq("user_id", user_id).execute()
    db.table("transcripts").delete().eq("id", transcript_id).eq("user_id", user_id).execute()

    return success_response({"deleted": True})
