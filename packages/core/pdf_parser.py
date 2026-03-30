"""
GradeTrace Core — PDF Parser

Parses NSU transcript PDF files into uniform dictionaries compatible with our audit engines.
Extracts graded rows and forward-fills semester data. Also extracts waiver/transfer courses with a 'T' grade.
"""

import pdfplumber
import io
import re

class PDFParser:
    """Parses PDF transcripts generated from rds3.northsouth.edu (Format 1) OR Official Transcripts (Format 2)."""

    @classmethod
    def parse(cls, file_bytes: bytes) -> list[dict]:
        """
        Detects the format of the PDF and delegates to the appropriate parser.
        """
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not pdf.pages:
                raise ValueError("Empty PDF transcript")

            # Peek at page 1 text to determine format
            p1_text = pdf.pages[0].extract_text()
            if not p1_text:
                p1_text = ""
                
            p1_text_lower = p1_text.lower()
            
            if "controller of examinations" in p1_text_lower or "official transcript" in p1_text_lower:
                return cls._parse_format_2(pdf)
            elif "grade history" in p1_text_lower or "rds3" in p1_text_lower:
                return cls._parse_format_1(pdf)
            else:
                raise ValueError("Unrecognized transcript format. Please upload an NSU grade history PDF or official transcript PDF.")

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
        """Format 2: Official Transcript (2-Column text extraction with Regex)"""
        records = []
        
        # Matches: "Spring 2007", "Fall 2008" etc. Handles optional padding.
        sem_pattern = re.compile(r"^\s*(Spring|Summer|Fall)\s+(\d{4})\s*$", re.IGNORECASE)
        
        # Matches: COURSE_CODE | Course Title | Cr. | Gr. | CC | CP
        # Example: ACT201 | Introduction to Financial Accounting | 3.0 | A- | 3.0 | 3.0
        # Pipes might be present literally or missing/translated as spaces by pdfplumber.
        course_pattern = re.compile(
            r"^\s*([A-Za-z]{3,4}\s*\d{3})\s*(?:\|)?\s+(.+?)\s+(?:\|)?\s+(\d+\.\d+)\s+(?:\|)?\s+([A-Za-z][+-]?|I|W|WV|X)\s+(?:\|)?\s+(\d+\.\d+)\s+(?:\|)?\s+(\d+\.\d+)\s*$"
        )
        
        # Start scanning from Page 2 (skip the degree certificate on Page 1)
        for page in pdf.pages[1:]:
            # Check if we've hit the details/grading legend page (meaning transcript is over)
            page_text_raw = page.extract_text() or ""
            if "grading system" in page_text_raw.lower() or "details" in page_text_raw.lower():
                # We optionally continue, but officially page 3 is skipped. 
                # Let's break if it's strictly a legend page, or just keep scanning (regex is safe enough).
                pass
            
            width = page.width
            height = page.height
            
            # Explicitly crop the page into the left column and right column vertically
            left_col = page.crop((0, 0, width / 2.0, height))
            right_col = page.crop((width / 2.0, 0, width, height))
            
            left_text = left_col.extract_text() or ""
            right_text = right_col.extract_text() or ""
            
            # Create a sequential array to preserve chronological order (Left Semesters first, then Right Semesters)
            lines = left_text.split('\n') + right_text.split('\n')
            
            current_semester = ""
            current_year = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Try matching semester header
                sem_match = sem_pattern.match(line)
                if sem_match:
                    current_semester = sem_match.group(1).title()
                    current_year = sem_match.group(2)
                    continue
                    
                # Try matching course record row
                course_match = course_pattern.match(line)
                if course_match:
                    code = course_match.group(1).replace(" ", "").upper()
                    title = course_match.group(2).strip()
                    credit_str = course_match.group(3).strip()
                    grade = course_match.group(4).strip().upper()
                    
                    # Normalizing to matching expected Credit format (e.g. 3.0 -> 3)
                    if credit_str.endswith(".0"):
                        credit_str = credit_str[:-2]
                    elif credit_str.endswith(".00"):
                        credit_str = credit_str[:-3]
                        
                    semester_str = f"{current_semester}{current_year}"
                    
                    records.append({
                        "course_code": code,
                        "course_name": title,
                        "credits": credit_str,
                        "grade": grade,
                        "semester": semester_str
                    })
                    
        return records
