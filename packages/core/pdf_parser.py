"""
GradeTrace Core — Universal LLM Parser (Gemini 1.5 Flash)

Replaces the legacy Google Cloud Vision OCR parser. Parses complex PDFs
and images using Gemini 1.5 Flash natively, returning clean JSON.
"""

import io
import json
import logging
import re
from typing import Optional

import google.generativeai as genai
from PIL import Image
import gc

logger = logging.getLogger(__name__)

# Validate course codes (allow 2-4 letters, 3 digits)
COURSE_VALIDATOR = re.compile(r"^[A-Z]{2,4}\d{3}$", re.IGNORECASE)

class VisionParser:
    """
    LLM transcript parser using Gemini 1.5 Flash.
    Keeps the name `VisionParser` for backward compatibility with existing route imports.
    """

    @classmethod
    def parse(cls, file_bytes: bytes, gemini_api_key: str = "", filename: str = "", google_creds: str = "") -> list[dict]:
        """
        Parse any supported file (PDF, JPG, PNG, WEBP) into a list of course dicts.
        Uses Gemini 1.5 Flash to automatically extract tabular data into JSON.
        """
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for transcript parsing.")

        genai.configure(api_key=gemini_api_key)

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext == "pdf":
            images = cls._pdf_to_images(file_bytes)
        else:
            images = [Image.open(io.BytesIO(file_bytes)).convert("RGB")]

        if not images:
            raise ValueError("Could not extract any pages from the uploaded file.")

        pages_to_process = cls._select_pages(images)
        logger.info(f"[GeminiLLM] Processing {len(pages_to_process)} page(s) out of {len(images)} total.")

        prompt = """You are a high-precision transcript parser for North South University (NSU) Bangladesh.
Extract ALL course data from this image.

### CRITICAL RULES:
1. ROW STABILITY: A grade listed on the same vertical line as a course code MUST stay with that course. Do not shift grades between rows.
2. PROGRAM DETECTION: Look for the degree name (e.g., "Bachelor of Business Administration" or "Bachelor of Science in Computer Science and Engineering").
3. OUTPUT FORMAT: Return ONLY a valid JSON object (no markdown, no explanation) with exactly two keys:
   - "program": The detected degree name (string, e.g., "BBA" or "CSE")
   - "courses": An array of objects, each with:
     - course_code (string, e.g. "CSE115")
     - course_name (string)
     - credits (float)
     - grade (string, null if no grade)
     - semester (string, e.g. "Summer")
     - year (integer)

### DETECTION HINTS:
- If you see courses like ACT, FIN, MKT, BUS, MGT -> Program is "BBA".
- If you see courses like CSE, MAT116, EEE, PHY -> Program is "CSE"."""

        # Using gemini-3.1-flash-lite-preview per user request
        model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
        
        contents = [prompt] + pages_to_process
        
        logger.info("[GeminiLLM] Calling Gemini API...")
        response = model.generate_content(contents)
        
        raw_text = response.text.strip()
        
        # Clean up possible markdown wrappers if Gemini ignores instructions
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()
        
        try:
            full_data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.error(f"[GeminiLLM] Failed to decode JSON from Gemini output. Raw response: {raw_text[:200]}...")
            raise ValueError("Failed to parse transcript data (invalid format returned by AI).")
            
        if not isinstance(full_data, dict) or "courses" not in full_data:
            # Fallback if Gemini ignored structure but gave an array
            if isinstance(full_data, list):
                parsed_courses = full_data
                detected_program = "UNKNOWN"
            else:
                raise ValueError("Failed to parse transcript data (invalid structure).")
        else:
            parsed_courses = full_data["courses"]
            detected_program = str(full_data.get("program", "")).upper()
            if "COMPUTER" in detected_program or "SCIENCE" in detected_program:
                detected_program = "CSE"
            elif "BUSINESS" in detected_program or "BBA" in detected_program:
                detected_program = "BBA"
            else:
                detected_program = "UNKNOWN"

        # Validation and formatting mapping
        processed_records = []
        for item in parsed_courses:
            course_code = str(item.get("course_code", "")).replace(" ", "").upper()
            
            # Post-parsing regex validation to fix hallucinations
            if not COURSE_VALIDATOR.match(course_code):
                continue
                
            code = course_code
            name = str(item.get("course_name", ""))
            
            # Credits
            try:
                credit_val = float(item.get("credits", 3.0))
                credits_str = str(int(credit_val)) if credit_val.is_integer() else str(credit_val)
            except (ValueError, TypeError):
                credits_str = "3"
                
            grade = str(item.get("grade", "")) if item.get("grade") and str(item.get("grade")).strip().lower() != "null" else "T"
            
            semester = str(item.get("semester", "")).title()
            year = str(item.get("year", ""))
            sem_str = f"{semester}{year}".strip() if semester else "Unknown"

            processed_records.append({
                "course_code": code,
                "course_name": name,
                "credits": credits_str,
                "grade": grade,
                "semester": sem_str,
            })
            
        # Deduplication
        seen = {}
        for rec in processed_records:
            key = (rec["course_code"], rec["semester"])
            seen[key] = rec
        records_deduped = list(seen.values())

        if not records_deduped:
            raise ValueError(
                "No course data could be extracted. "
                "Ensure the transcript is clear and in a supported NSU format."
            )

        logger.info(f"[GeminiLLM] Extracted {len(records_deduped)} validated courses. Detected Program: {detected_program}")
        return {
            "program": detected_program,
            "courses": records_deduped
        }

    @classmethod
    def _pdf_to_images(cls, file_bytes: bytes) -> list[Image.Image]:
        try:
            import pypdfium2 as pdfium
        except ImportError:
            raise ValueError("pypdfium2 is not installed.")

        pdf = pdfium.PdfDocument(file_bytes)
        images = []
        scale = 300 / 72  # 300 DPI
        for page in pdf:
            bitmap = page.render(scale=scale, rotation=0)
            pil_img = bitmap.to_pil()
            images.append(pil_img.convert("RGB"))
            bitmap.close()
            page.close()
        pdf.close()
        
        del pdf
        gc.collect()
        
        return images

    @classmethod
    def _select_pages(cls, images: list[Image.Image]) -> list[Image.Image]:
        if len(images) == 1:
            return images
        return images[1:]
