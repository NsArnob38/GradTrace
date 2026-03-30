"""
GradeTrace Core — Universal Vision Parser

All non-CSV uploads (PDF, JPG, PNG, WEBP) are parsed through a single
coordinate-aware OCR pipeline using Google Cloud Vision API.

PDF pages are rendered to 300 DPI PNG images using pypdfium2 (no poppler needed).
Images are sent directly to Vision DOCUMENT_TEXT_DETECTION.
Words with bounding boxes are grouped into lines, then classified.

pdfplumber is kept as an import-safe dependency but is NOT used for parsing.
"""

import io
import re
import json
import logging
from typing import Optional

from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------
SEM_PATTERN    = re.compile(r"^(Spring|Summer|Fall)\s+(20\d{2})$", re.IGNORECASE)
COURSE_PATTERN = re.compile(r"^([A-Z]{2,4}\d{3})$")
GRADE_PATTERN  = re.compile(r"^(A\+?|A-|B\+|B|B-|C\+|C|C-|D\+|D|D-|F|I|W|WV|X|T)$", re.IGNORECASE)
CREDIT_PATTERN = re.compile(r"^\d+(\.\d+)?$")
SKIP_PATTERNS  = [
    re.compile(r"Semester\s*Credit", re.IGNORECASE),
    re.compile(r"TGPA|CGPA",          re.IGNORECASE),
    re.compile(r"Grade\s*History\s*of",re.IGNORECASE),
    re.compile(r"Student\s*(Name|ID)", re.IGNORECASE),
    re.compile(r"Grading\s*(System|Legend|Scale)", re.IGNORECASE),
    re.compile(r"Degree\s*Conferred",  re.IGNORECASE),
    re.compile(r"North\s*South\s*University", re.IGNORECASE),
    re.compile(r"Controller\s*of\s*Exam", re.IGNORECASE),
    re.compile(r"Official\s*Transcript", re.IGNORECASE),
]
WAIVER_PATTERN = re.compile(r"Waiver|Transfer\s*Course", re.IGNORECASE)


class VisionParser:
    """
    Universal transcript parser: every non-CSV file goes through Google Vision OCR.
    PDF → pypdfium2 → 300 DPI PNG → Vision → coordinate-aware lines → records.
    Image → Vision directly → coordinate-aware lines → records.
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    @classmethod
    def parse(cls, file_bytes: bytes, google_creds: str, filename: str = "") -> list[dict]:
        """
        Parse any supported file (PDF, JPG, PNG, WEBP) into a list of course dicts.
        Raises ValueError if credentials are missing or parsing fails.
        """
        if not google_creds:
            raise ValueError("Google Vision credentials are required for PDF/image parsing.")

        client = cls._build_client(google_creds)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext == "pdf":
            images = cls._pdf_to_images(file_bytes)
        else:
            # Raw image upload
            images = [Image.open(io.BytesIO(file_bytes)).convert("RGB")]

        if not images:
            raise ValueError("Could not extract any pages from the uploaded file.")

        pages_to_process = cls._select_pages(images)
        logger.info(f"[VisionParser] Processing {len(pages_to_process)} page(s) out of {len(images)} total.")

        all_records: list[dict] = []
        for page_img in pages_to_process:
            records = cls._process_image(page_img, client)
            all_records.extend(records)

        # Deduplicate: keep last occurrence of each (course_code, semester) pair
        seen: dict[tuple, dict] = {}
        for rec in all_records:
            key = (rec["course_code"], rec["semester"])
            seen[key] = rec
        records_deduped = list(seen.values())

        if not records_deduped:
            raise ValueError(
                "No course data could be extracted. "
                "Ensure the transcript is clear and in a supported NSU format."
            )

        logger.info(f"[VisionParser] Extracted {len(records_deduped)} unique course rows.")
        return records_deduped

    # ------------------------------------------------------------------
    # PDF → Images
    # ------------------------------------------------------------------

    @classmethod
    def _pdf_to_images(cls, file_bytes: bytes) -> list[Image.Image]:
        """Render every PDF page to a 300 DPI PIL Image using pypdfium2."""
        try:
            import pypdfium2 as pdfium
        except ImportError:
            raise ValueError("pypdfium2 is not installed. Add it to requirements.txt.")

        pdf = pdfium.PdfDocument(file_bytes)
        images = []
        scale = 300 / 72  # 300 DPI
        for page in pdf:
            bitmap = page.render(scale=scale, rotation=0)
            pil_img = bitmap.to_pil()
            images.append(pil_img.convert("RGB"))
        pdf.close()
        return images

    # ------------------------------------------------------------------
    # Page selection
    # ------------------------------------------------------------------

    @classmethod
    def _select_pages(cls, images: list[Image.Image]) -> list[Image.Image]:
        """
        Determine which pages to OCR.
        - 1 page total → process it regardless.
        - 2+ pages → skip page 1 (certificate) and process page 2.
          If page 2 looks empty, fall back to page 1.
          All remaining pages also processed.
        """
        if len(images) == 1:
            return images

        # For multi-page: skip page 1 (index 0), process from page 2 onward.
        return images[1:]

    # ------------------------------------------------------------------
    # Vision client
    # ------------------------------------------------------------------

    @classmethod
    def _build_client(cls, credentials_json: str) -> vision.ImageAnnotatorClient:
        info = json.loads(credentials_json)
        creds = service_account.Credentials.from_service_account_info(info)
        return vision.ImageAnnotatorClient(credentials=creds)

    # ------------------------------------------------------------------
    # Single-image OCR + line reconstruction
    # ------------------------------------------------------------------

    @classmethod
    def _process_image(cls, img: Image.Image, client: vision.ImageAnnotatorClient) -> list[dict]:
        """OCR a single PIL image and return extracted course records."""
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        content = buf.getvalue()

        response = client.document_text_detection(image=vision.Image(content=content))
        if response.error.message:
            logger.warning(f"[VisionParser] Vision API error: {response.error.message}")
            return []

        annotation = response.full_text_annotation
        if not annotation or not annotation.pages:
            return []

        vision_page = annotation.pages[0]
        page_width  = vision_page.width

        # Collect all words with positions
        words_data: list[dict] = []
        for block in vision_page.blocks:
            for para in block.paragraphs:
                for word in para.words:
                    text = "".join(s.text for s in word.symbols)
                    v    = word.bounding_box.vertices
                    x0   = v[0].x
                    y0   = v[0].y
                    words_data.append({"text": text, "x0": x0, "top": y0})

        if not words_data:
            return []

        # Decide: single-column or two-column?
        rightmost_x = max(w["x0"] for w in words_data)
        split_x     = page_width * 0.55
        has_right   = any(w["x0"] >= split_x for w in words_data)

        if has_right and rightmost_x > split_x:
            left_words  = [w for w in words_data if w["x0"] <  split_x]
            right_words = [w for w in words_data if w["x0"] >= split_x]
            lines = cls._group_into_lines(left_words) + cls._group_into_lines(right_words)
        else:
            lines = cls._group_into_lines(words_data)

        return cls._extract_records(lines)

    # ------------------------------------------------------------------
    # Group words into text lines (15 px Y-tolerance)
    # ------------------------------------------------------------------

    @classmethod
    def _group_into_lines(cls, words: list[dict], tolerance: float = 15.0) -> list[str]:
        if not words:
            return []
        words = sorted(words, key=lambda w: w["top"])
        lines: list[str] = []
        current: list[dict] = [words[0]]
        current_top: float   = words[0]["top"]

        for w in words[1:]:
            if abs(w["top"] - current_top) <= tolerance:
                current.append(w)
            else:
                current.sort(key=lambda x: x["x0"])
                lines.append(" ".join(x["text"] for x in current).strip())
                current     = [w]
                current_top = w["top"]

        if current:
            current.sort(key=lambda x: x["x0"])
            lines.append(" ".join(x["text"] for x in current).strip())

        return [l for l in lines if l]

    # ------------------------------------------------------------------
    # Classify lines → course records
    # ------------------------------------------------------------------

    @classmethod
    def _extract_records(cls, lines: list[str]) -> list[dict]:
        records: list[dict] = []
        current_semester = ""
        current_year     = ""
        in_waiver        = False

        for line in lines:
            # --- Skip footers / metadata ---
            if any(p.search(line) for p in SKIP_PATTERNS):
                continue

            # --- Waiver / Transfer section header ---
            if WAIVER_PATTERN.search(line):
                in_waiver = True
                continue

            # --- Semester header ---
            tokens = line.strip().split()
            # Try adjacent tokens: "Spring 2024", "Fall 2025"
            sem_match = SEM_PATTERN.match(line.strip())
            if sem_match:
                current_semester = sem_match.group(1).title()
                current_year     = sem_match.group(2)
                in_waiver        = False
                continue

            # Two-token semester split across a combined line like "Spring2024"
            combined = re.match(r"^(Spring|Summer|Fall)(20\d{2})$", line.strip(), re.IGNORECASE)
            if combined:
                current_semester = combined.group(1).title()
                current_year     = combined.group(2)
                in_waiver        = False
                continue

            # --- Course row extraction ---
            # Scan tokens to find: course_code, credit, grade (in any order after code)
            course_code: Optional[str] = None
            credit:      Optional[str] = None
            grade:       Optional[str] = None
            name_parts:  list[str]     = []

            i = 0
            while i < len(tokens):
                tok = tokens[i]
                # Normalise OCR artefacts: "CSE3I1" → won't match; that's intentional
                if COURSE_PATTERN.match(tok.upper()):
                    course_code = tok.upper()
                elif GRADE_PATTERN.match(tok.upper()) and course_code is not None and grade is None:
                    grade = tok.upper()
                elif CREDIT_PATTERN.match(tok) and course_code is not None and credit is None:
                    credit = tok
                elif course_code is not None and grade is None and credit is None:
                    # Looks like part of the course name
                    name_parts.append(tok)
                i += 1

            if course_code and grade:
                # Normalise credit
                cr = credit or "3"
                if cr.endswith(".0"):  cr = cr[:-2]
                if cr.endswith(".00"): cr = cr[:-3]

                sem_str = f"{current_semester}{current_year}" if current_semester else "Unknown"

                records.append({
                    "course_code": course_code,
                    "course_name": " ".join(name_parts).strip(),
                    "credits":     cr,
                    "grade":       grade,
                    "semester":    sem_str,
                })
                continue

            # Waiver rows: course code only, no grade required
            if in_waiver and course_code and not grade:
                cr = credit or "3"
                if cr.endswith(".0"):  cr = cr[:-2]
                records.append({
                    "course_code": course_code,
                    "course_name": " ".join(name_parts).strip(),
                    "credits":     cr,
                    "grade":       "T",
                    "semester":    "Waiver",
                })

        return records
