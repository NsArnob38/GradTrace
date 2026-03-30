"""
GradeTrace Core — PDF Parser

Parses NSU transcript PDF files into uniform dictionaries compatible with our audit engines.
Extracts graded rows and forward-fills semester data. Also extracts waiver/transfer courses with a 'T' grade.
"""

import pdfplumber
import io
import re
import json
from google.cloud import vision
from google.oauth2 import service_account

class PDFParser:
    """Parses PDF transcripts generated from rds3.northsouth.edu (Format 1) OR Official Transcripts (Format 2)."""

    @classmethod
    def _get_vision_client(cls, credentials_json: str = None):
        if not credentials_json:
            return None
        try:
            info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(info)
            return vision.ImageAnnotatorClient(credentials=credentials)
        except Exception:
            return None

    @classmethod
    def parse(cls, file_bytes: bytes, google_creds: str = None) -> list[dict]:
        """
        Detects the format of the PDF and delegates to the appropriate parser.
        Uses Google Vision OCR if Format 2 is detected or if pdfplumber fails.
        """
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not pdf.pages:
                raise ValueError("Empty PDF transcript")

            # Try digital extraction first
            words = pdf.pages[0].extract_words()
            p1_text = " ".join([w['text'] for w in words]) if words else ""
            
            # Format 2 Detection (Robust)
            is_format_2 = False
            if re.search(r"Official\s*Transcript|Controller\s*of\s*Examinations", p1_text, re.IGNORECASE):
                is_format_2 = True
            elif re.search(r"Student\s*ID.*Date\s*of\s*Birth.*Degree\s*Conferred", p1_text, re.IGNORECASE):
                is_format_2 = True
            elif re.search(r"(Spring|Summer|Fall)\s*20\d\d.*?[A-Za-z]{2,4}\s*\d{3}", p1_text, re.IGNORECASE):
                is_format_2 = True
            elif len(pdf.pages) > 1:
                p2_words = pdf.pages[1].extract_words()
                p2_text = " ".join([w['text'] for w in p2_words]) if p2_words else ""
                if re.search(r"(Spring|Summer|Fall)\s*20\d\d.*?[A-Za-z]{2,4}\s*\d{3}", p2_text, re.IGNORECASE):
                    is_format_2 = True

            if is_format_2:
                # Use Google Vision for Format 2 to ensure accuracy on scans/watermarks
                client = cls._get_vision_client(google_creds)
                if client:
                    return cls._parse_with_google_vision(file_bytes, client)
                return cls._parse_format_2(pdf) # Fallback to pdfplumber if no creds
                
            # Format 1 Detection
            if re.search(r"Grade\s*History|rds3", p1_text, re.IGNORECASE):
                return cls._parse_format_1(pdf)

            # Final Fallback: If no text at all, try Google Vision anyway as it might be a scan we missed
            if not p1_text:
                client = cls._get_vision_client(google_creds)
                if client:
                    return cls._parse_with_google_vision(file_bytes, client)

            raise ValueError("Unrecognized transcript format. Please upload an NSU grade history PDF or official transcript PDF.")

    @classmethod
    def _parse_with_google_vision(cls, file_bytes: bytes, client: vision.ImageAnnotatorClient) -> list[dict]:
        """Uses Google Vision annotate_image per page to parse scanned PDFs."""
        records = []
        sem_pattern = re.compile(r"^\s*(Spring|Summer|Fall)\s+(\d{4})\s*$", re.IGNORECASE)
        course_pattern = re.compile(
            r"^\s*([A-Za-z]{2,4}\s*\d{3})\s*[|]?\s*(.+?)\s+[|]?\s*(\d+\.\d+)\s*[|]?\s*([A-Za-z][+-]?|I|W|WV|X)\s*[|]?\s*(\d+\.\d+)\s*[|]?\s*(\d+\.\d+)\s*$"
        )

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            # Skip Page 1 (Certificate)
            for page in pdf.pages[1:]:
                # Convert PDF page to Image bytes for Google Vision
                # pdfplumber uses pypdfium2 (standalone) which works on Render
                img = page.to_image(resolution=200).original 
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                content = img_byte_arr.getvalue()

                image = vision.Image(content=content)
                response = client.document_text_detection(image=image)
                annotation = response.full_text_annotation
                
                if not annotation:
                    continue
                    
                # In pixel coordinates, width is annotation.pages[0].width
                vision_page = annotation.pages[0]
                width = vision_page.width
                
                # Extract words with coordinates
                words_data = []
                for block in vision_page.blocks:
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            text = "".join([symbol.text for symbol in word.symbols])
                            v = word.bounding_box.vertices
                            words_data.append({
                                'text': text,
                                'x0': v[0].x,
                                'top': v[0].y
                            })
                
                if not words_data:
                    continue

                # 2-Column Logic
                left_col = [w for w in words_data if w['x0'] < width / 2.0]
                right_col = [w for w in words_data if w['x0'] >= width / 2.0]
                
                def group_words(word_list, tolerance=10.0): # User requested 10px
                    if not word_list: return []
                    word_list.sort(key=lambda w: w['top'])
                    lines, current_line = [], []
                    current_top = word_list[0]['top']
                    for w in word_list:
                        if abs(w['top'] - current_top) <= tolerance:
                            current_line.append(w)
                        else:
                            current_line.sort(key=lambda x: x['x0'])
                            lines.append(" ".join([x['text'] for x in current_line]))
                            current_line, current_top = [w], w['top']
                    if current_line:
                        current_line.sort(key=lambda x: x['x0'])
                        lines.append(" ".join([x['text'] for x in current_line]))
                    return lines

                all_lines = group_words(left_col) + group_words(right_col)
                
                current_semester, current_year = "", ""
                for line in all_lines:
                    sem_match = sem_pattern.match(line)
                    if sem_match:
                        current_semester, current_year = sem_match.group(1).title(), sem_match.group(2)
                        continue
                    course_match = course_pattern.match(line)
                    if course_match:
                        code = course_match.group(1).replace(" ", "").upper()
                        credit = course_match.group(3).strip()
                        if credit.endswith(".0"): credit = credit[:-2]
                        elif credit.endswith(".00"): credit = credit[:-3]
                        records.append({
                            "course_code": code,
                            "course_name": course_match.group(2).strip(),
                            "credits": credit,
                            "grade": course_match.group(4).strip().upper(),
                            "semester": f"{current_semester}{current_year}"
                        })
        return records

    @classmethod
    def _parse_format_1(cls, pdf: pdfplumber.PDF) -> list[dict]:
        """Format 1: Web Export (Table-based extraction with forward filling)"""
        records = []
        current_semester = ""
        current_year = ""
        
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or not table[0]:
                    continue
                
                # Normalize table headers
                headers = [str(h).replace('\n', ' ').strip().lower() for h in table[0] if h]
                
                # DETECT: Main Grade Table
                if "course code" in headers and "course grade" in headers:
                    sem_name_idx = next((i for i, h in enumerate(headers) if "semester name" in h), -1)
                    sem_year_idx = next((i for i, h in enumerate(headers) if "semester year" in h), -1)
                    code_idx = next((i for i, h in enumerate(headers) if "course code" in h), -1)
                    name_idx = next((i for i, h in enumerate(headers) if "course title" in h), -1)
                    credit_idx = next((i for i, h in enumerate(headers) if "course credit" in h or "crs.credit" in h), -1)
                    grade_idx = next((i for i, h in enumerate(headers) if "course grade" in h), -1)
                    
                    if code_idx == -1 or grade_idx == -1:
                        continue
                        
                    for row in table[1:]:
                        if not row or not any(row):
                            continue
                        
                        first_col = str(row[0]).strip().lower() if row[0] else ""
                        if "semester credit" in first_col or "tgpa" in first_col or "cgpa" in first_col:
                            continue
                            
                        # Forward-fill Semester metadata if present in row
                        if sem_name_idx != -1 and row[sem_name_idx] and str(row[sem_name_idx]).strip():
                            current_semester = str(row[sem_name_idx]).strip()
                        if sem_year_idx != -1 and row[sem_year_idx] and str(row[sem_year_idx]).strip():
                            current_year = str(row[sem_year_idx]).strip()
                            
                        code = str(row[code_idx]).strip().replace('\n', '') if len(row) > code_idx and row[code_idx] else ""
                        
                        if not code:
                            continue
                            
                        name = str(row[name_idx]).strip().replace('\n', ' ') if name_idx != -1 and len(row) > name_idx and row[name_idx] else ""
                        credit = str(row[credit_idx]).strip() if credit_idx != -1 and len(row) > credit_idx and row[credit_idx] else "0"
                        grade = str(row[grade_idx]).strip() if len(row) > grade_idx and row[grade_idx] else ""
                        
                        if credit.endswith(".0"):
                            credit = credit[:-2]
                            
                        semester_str = f"{current_semester}{current_year}".replace(" ", "")
                        
                        records.append({
                            "course_code": code,
                            "course_name": name,
                            "credits": credit,
                            "grade": grade,
                            "semester": semester_str
                        })
                
                # DETECT: Waiver / Transfer Table (Has codes and title, but NO grade)
                elif "course code" in headers and "course grade" not in headers and ("course title" in headers or "title" in headers):
                    code_idx = next((i for i, h in enumerate(headers) if "course code" in h), -1)
                    name_idx = next((i for i, h in enumerate(headers) if "course title" in h or "title" in h), -1)
                    credit_idx = next((i for i, h in enumerate(headers) if "credit" in h), -1)
                    
                    for row in table[1:]:
                        if not row or not any(row):
                            continue
                        
                        first_col = str(row[0]).strip().lower() if row[0] else ""
                        if "total" in first_col:
                            continue
                        
                        code = str(row[code_idx]).strip().replace('\n', '') if code_idx != -1 and len(row) > code_idx and row[code_idx] else ""
                        if not code:
                            continue
                            
                        name = str(row[name_idx]).strip().replace('\n', ' ') if name_idx != -1 and len(row) > name_idx and row[name_idx] else ""
                        credit = str(row[credit_idx]).strip() if credit_idx != -1 and len(row) > credit_idx and row[credit_idx] else "0"
                        
                        if credit.endswith(".0"):
                            credit = credit[:-2]
                            
                        records.append({
                            "course_code": code,
                            "course_name": name,
                            "credits": credit,
                            "grade": "T",  # explicitly assign T for waiver/transfer
                            "semester": "Waiver"
                        })
                        
        return records

    @classmethod
    def _parse_format_2(cls, pdf: pdfplumber.PDF) -> list[dict]:
        """Format 2 Fallback: pdfplumber coordinate extraction (if Google Vision disabled/unavailable)"""
        records = []
        sem_pattern = re.compile(r"^\s*(Spring|Summer|Fall)\s+(\d{4})\s*$", re.IGNORECASE)
        course_pattern = re.compile(
            r"^\s*([A-Za-z]{2,4}\s*\d{3})\s*[|]?\s*(.+?)\s+[|]?\s*(\d+\.\d+)\s*[|]?\s*([A-Za-z][+-]?|I|W|WV|X)\s*[|]?\s*(\d+\.\d+)\s*[|]?\s*(\d+\.\d+)\s*$"
        )
        
        for page in pdf.pages[1:]:
            words = page.extract_words()
            if not words: continue
            page_text = " ".join([w['text'] for w in words]).lower()
            if "grading system" in page_text or "grading legend" in page_text: continue
            
            width = page.width
            left_col_words = [w for w in words if w['x0'] < width / 2.0]
            right_col_words = [w for w in words if w['x0'] >= width / 2.0]
                    
            def group_words_into_lines(word_list, tolerance=5.0):
                if not word_list: return []
                word_list.sort(key=lambda w: w['top'])
                lines, current_line = [], []
                current_top = word_list[0]['top']
                for w in word_list:
                    if abs(w['top'] - current_top) <= tolerance:
                        current_line.append(w)
                    else:
                        current_line.sort(key=lambda x: x['x0'])
                        lines.append(" ".join([x['text'] for x in current_line]))
                        current_line, current_top = [w], w['top']
                if current_line:
                    current_line.sort(key=lambda x: x['x0'])
                    lines.append(" ".join([x['text'] for x in current_line]))
                return lines

            all_lines = group_words_into_lines(left_col_words) + group_words_into_lines(right_col_words)
            current_semester, current_year = "", ""
            for line in all_lines:
                sem_match = sem_pattern.match(line)
                if sem_match:
                    current_semester, current_year = sem_match.group(1).title(), sem_match.group(2)
                    continue
                course_match = course_pattern.match(line)
                if course_match:
                    code = course_match.group(1).replace(" ", "").upper()
                    credit = course_match.group(3).strip()
                    if credit.endswith(".0"): credit = credit[:-2]
                    elif credit.endswith(".00"): credit = credit[:-3]
                    records.append({
                        "course_code": code,
                        "course_name": course_match.group(2).strip(),
                        "credits": credit,
                        "grade": course_match.group(4).strip().upper(),
                        "semester": f"{current_semester}{current_year}"
                    })
        return records

