"""
GradeTrace API — Transcript Routes
"""

import csv
import io
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from packages.api.deps import get_current_user, get_supabase_admin, success_response

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post("/upload")
async def upload_transcript(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload a CSV transcript, parse it, and store in Supabase."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported currently")

    content = await file.read()
    text = content.decode("utf-8-sig")

    # Parse CSV into list of dicts
    reader = csv.reader(io.StringIO(text))
    rows = []
    headers = None
    for row in reader:
        if not row or len(row) < 5:
            continue
        if row[0].strip().lower() == "course_code":
            headers = [h.strip().lower() for h in row]
            continue
        rows.append({
            "course_code": row[0].strip(),
            "course_name": row[1].strip(),
            "credits": row[2].strip(),
            "grade": row[3].strip(),
            "semester": row[4].strip(),
        })

    if not rows:
        raise HTTPException(status_code=400, detail="No valid course data found in CSV")

    # Store in Supabase
    db = get_supabase_admin()

    result = db.table("transcripts").insert({
        "user_id": user["id"],
        "file_name": file.filename,
        "raw_data": rows,
    }).execute()

    transcript = result.data[0] if result.data else None
    return success_response(transcript)


@router.get("")
async def list_transcripts(user: dict = Depends(get_current_user)):
    """List all transcripts for the current user."""
    db = get_supabase_admin()
    result = db.table("transcripts") \
        .select("id, file_name, uploaded_at") \
        .eq("user_id", user["id"]) \
        .order("uploaded_at", desc=True) \
        .execute()
    return success_response(result.data)


@router.get("/{transcript_id}")
async def get_transcript(transcript_id: str, user: dict = Depends(get_current_user)):
    """Get a single transcript with raw data."""
    db = get_supabase_admin()
    result = db.table("transcripts") \
        .select("*") \
        .eq("id", transcript_id) \
        .eq("user_id", user["id"]) \
        .single() \
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return success_response(result.data)
