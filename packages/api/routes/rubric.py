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
import pandas as pd
import io

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
        from packages.core.pdf_parser import PDFParser
        rows = PDFParser.parse(content)
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
        content = await file.read()
        debug_pages = []
        
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for i, page in enumerate(pdf.pages):
                words = page.extract_words()
                if not words:
                    debug_pages.append({"page": i + 1, "text": ""})
                    continue
                    
                width = page.width
                left_col_words = []
                right_col_words = []
                for w in words:
                    if w['x0'] < width / 2.0:
                        left_col_words.append(w)
                    else:
                        right_col_words.append(w)
                        
                def group_words_into_lines(word_list: list, tolerance: float = 5.0) -> list[str]:
                    if not word_list:
                        return []
                    word_list.sort(key=lambda w: w['top'])
                    lines = []
                    current_line = []
                    current_top = word_list[0]['top']
                    for w in word_list:
                        if abs(w['top'] - current_top) <= tolerance:
                            current_line.append(w)
                        else:
                            current_line.sort(key=lambda x: x['x0'])
                            lines.append(" ".join([x['text'] for x in current_line]))
                            current_line = [w]
                            current_top = w['top']
                    if current_line:
                        current_line.sort(key=lambda x: x['x0'])
                        lines.append(" ".join([x['text'] for x in current_line]))
                    return lines
                
                left_lines = group_words_into_lines(left_col_words)
                right_lines = group_words_into_lines(right_col_words)
                all_lines = left_lines + right_lines
                
                debug_pages.append({
                    "page": i + 1,
                    "text": "\n".join(all_lines)
                })
                
        return {"status": "success", "pages": debug_pages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
