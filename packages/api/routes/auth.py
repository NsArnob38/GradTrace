"""
GradeTrace API — Auth Routes
"""

from fastapi import APIRouter, Depends
from packages.api.deps import get_current_user, get_supabase_admin, success_response

router = APIRouter(tags=["auth"])


@router.get("/me")
async def get_profile(user: dict = Depends(get_current_user)):
    """Returns current user's profile."""
    db = get_supabase_admin()
    result = db.table("profiles").select("*").eq("id", user["id"]).single().execute()
    return success_response(result.data)


@router.put("/me")
async def update_profile(updates: dict, user: dict = Depends(get_current_user)):
    """Update current user's profile (program, concentration, etc.)."""
    allowed = {"full_name", "student_id", "program", "bba_concentration"}
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if not filtered:
        return success_response(None)

    db = get_supabase_admin()
    result = db.table("profiles").update(filtered).eq("id", user["id"]).execute()
    return success_response(result.data[0] if result.data else None)
