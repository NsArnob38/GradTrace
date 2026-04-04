"""
GradeTrace API — Transcript Routes
"""

import csv
import logging
import io
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from packages.api.deps import get_current_user, get_supabase_admin, success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post("/upload")
async def upload_transcript(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload a transcript (PDF, Image, or CSV), parse it, and store in Supabase."""
    filename = file.filename.lower()
    allowed_exts = {".csv", ".pdf", ".jpg", ".jpeg", ".png", ".webp"}
    if not any(filename.endswith(ext) for ext in allowed_exts):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Supported: {', '.join(allowed_exts)}"
        )

    content = await file.read()
    rows = []

    if not filename.endswith(".csv"):
        # Use Universal Vision Parser for all PDFs and Images
        from packages.core.pdf_parser import VisionParser
        from packages.api.config import get_settings
        settings = get_settings()
        try:
            rows = VisionParser.parse(
                content, 
                gemini_api_key=settings.gemini_api_key,
                filename=file.filename
            )
        except Exception as e:
            logger.error(f"Vision Parsing failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # CSV Parsing (standard logic)
        try:
            text = content.decode("utf-8-sig")
            reader = csv.reader(io.StringIO(text))
            for row in reader:
                if not row or len(row) < 5:
                    continue
                if row[0].strip().lower() == "course_code":
                    continue
                rows.append({
                    "course_code": row[0].strip(),
                    "course_name": row[1].strip(),
                    "credits": row[2].strip(),
                    "grade": row[3].strip(),
                    "semester": row[4].strip(),
                })
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    if not rows:
        raise HTTPException(status_code=400, detail="No valid course data found in file")

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


from pydantic import BaseModel
from typing import List, Any

class UpdateTranscriptRequest(BaseModel):
    raw_data: List[Any]

@router.put("/{transcript_id}")
async def update_transcript(
    transcript_id: str,
    req: UpdateTranscriptRequest,
    user: dict = Depends(get_current_user)
):
    """Update the raw_data of a transcript (used for manual OCR corrections)."""
    db = get_supabase_admin()
    
    # Verify ownership
    existing = db.table("transcripts") \
        .select("id") \
        .eq("id", transcript_id) \
        .eq("user_id", user["id"]) \
        .single() \
        .execute()
        
    if not existing.data:
        raise HTTPException(status_code=404, detail="Transcript not found")
        
    # Update raw data
    result = db.table("transcripts") \
        .update({"raw_data": req.raw_data}) \
        .eq("id", transcript_id) \
        .eq("user_id", user["id"]) \
        .execute()
        
    return success_response({"updated": True})

