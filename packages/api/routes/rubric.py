"""
CSE226 Rubric specific Endpoints
These endpoints strictly fulfill the project rubric requirements:
POST /audit/level1
POST /audit/level2
POST /audit/level3
POST /audit/full
Each accepts a CSV file and a program string, and returns structured JSON.
"""

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from typing import Any
import io
import logging
import pandas as pd

from packages.core.level1 import run_level1
from packages.core.level2 import run_level2
from packages.core.level3 import run_level3
from packages.core.audit_core import run_full_audit

from pydantic import BaseModel
from typing import List, Dict, Any, Set, Optional

class Level1Response(BaseModel):
    status: str
    data: Dict[str, Any]  # credits_attempted, credits_earned, unrecognized

class Level2Response(BaseModel):
    status: str
    data: Dict[str, Any]  # cgpa, quality_points, standing, etc

class Level3Response(BaseModel):
    status: str
    data: Dict[str, Any]  # eligible, roadmap, missing courses

class FullAuditResponse(BaseModel):
    status: str
    data: Dict[str, Any]  # Combined metadata


async def get_dataframe_from_upload(file: UploadFile) -> pd.DataFrame:
    content = await file.read()
    if file.filename.lower().endswith(".pdf"):
        from packages.core.pdf_parser import VisionParser
        from packages.api.config import get_settings
        settings = get_settings()
        rows = VisionParser.parse(content, gemini_api_key=settings.gemini_api_key, filename=file.filename)
        return pd.DataFrame(rows)
    elif file.filename.lower().endswith(".csv"):
        # Use utf-8-sig to handle BOM correctly if present
        return pd.read_csv(io.StringIO(content.decode("utf-8-sig")))
    else:
        raise ValueError("Unsupported file extension. Please upload .csv or .pdf")


router = APIRouter(prefix="/audit", tags=["rubric_endpoints"])

@router.post("/level1", summary="CSE226 Rubric: Level 1 (Credit Tallying)", response_model=Level1Response)
async def api_level1(
    file: UploadFile = File(..., description="The student's transcript CSV or PDF file"),
    program: str = Form(..., description="The student's major (e.g., 'CSE' or 'BBA')")
):
    try:
        df = await get_dataframe_from_upload(file)
        result = run_level1(df, program)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/level2", summary="CSE226 Rubric: Level 2 (CGPA & Probation)", response_model=Level2Response)
async def api_level2(
    file: UploadFile = File(...),
    program: str = Form(...)
):
    try:
        df = await get_dataframe_from_upload(file)
        result = run_level2(df, program)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/level3", summary="CSE226 Rubric: Level 3 (Graduation Check)", response_model=Level3Response)
async def api_level3(
    file: UploadFile = File(...),
    program: str = Form(...)
):
    try:
        df = await get_dataframe_from_upload(file)
        result = run_level3(df, program)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/full", summary="CSE226 Rubric: Full Unified Audit", response_model=FullAuditResponse)
async def api_full_audit(
    file: UploadFile = File(...),
    program: str = Form(...)
):
    try:
        df = await get_dataframe_from_upload(file)
        result = run_full_audit(df, program)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/debug-pdf", summary="Debug: Output raw coordinate-text from PDF")
async def api_debug_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDFs are supported for debug")
        
    try:
        import pdfplumber
        from packages.api.config import get_settings
        from packages.core.pdf_parser import VisionParser
        
        settings = get_settings()
        content = await file.read()
        debug_pages = []
        
        # Check if Google Vision is available
        has_vision = bool(settings.gemini_api_key)
        
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for i, page in enumerate(pdf.pages):
                # Diagnostic metadata
                objects = page.objects
                char_count = len(objects.get('char', []))
                image_count = len(objects.get('image', []))
                rect_count = len(objects.get('rect', []))
                
                # Raw extraction
                raw_extracted = page.extract_text() or ""
                
                debug_pages.append({
                    "page": i + 1,
                    "metadata": {
                        "chars": char_count,
                        "images": image_count,
                        "rects": rect_count,
                        "width": page.width,
                        "height": page.height
                    },
                    "raw_text": raw_extracted,
                    "vision_enabled": has_vision,
                })
        
        # If vision is enabled, try an OCR sample
        if has_vision:
            try:
                # We reuse the logic from VisionParser to show what the final extracted text looks like
                ocr_rows = VisionParser.parse(content, gemini_api_key=settings.gemini_api_key, filename=file.filename)
                return {
                    "status": "success", 
                    "ocr_engine": "Google Vision AI",
                    "sample_records": ocr_rows[:5] if ocr_rows else [],
                    "total_records": len(ocr_rows),
                    "pages": debug_pages
                }
            except Exception as ocr_err:
                return {
                    "status": "partial_success",
                    "ocr_error": str(ocr_err),
                    "pages": debug_pages
                }
                
        return {"status": "success", "engine": "pdfplumber (Digital Only)", "pages": debug_pages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
