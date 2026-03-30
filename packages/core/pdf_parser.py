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

            # Extract words from page 1 and join to bypass watermark chunking issues
            words = pdf.pages[0].extract_words()
            p1_text = " ".join([w['text'] for w in words]) if words else ""
            
            # Format 2 Detection (Robust)
            if re.search(r"Official\s*Transcript|Controller\s*of\s*Examinations", p1_text, re.IGNORECASE):
                return cls._parse_format_2(pdf)
            if re.search(r"Student\s*ID.*Date\s*of\s*Birth.*Degree\s*Conferred", p1_text, re.IGNORECASE):
                return cls._parse_format_2(pdf)
            if re.search(r"(Spring|Summer|Fall)\s*20\d\d.*?[A-Za-z]{2,4}\s*\d{3}", p1_text, re.IGNORECASE):
                return cls._parse_format_2(pdf)
                
            # 4th Fallback: Scan Page 2 for Format 2 semester pattern if Page 1 is heavily watermarked
            if len(pdf.pages) > 1:
                p2_words = pdf.pages[1].extract_words()
                p2_text = " ".join([w['text'] for w in p2_words]) if p2_words else ""
                if re.search(r"(Spring|Summer|Fall)\s*20\d\d.*?[A-Za-z]{2,4}\s*\d{3}", p2_text, re.IGNORECASE):
                    return cls._parse_format_2(pdf)
                
            # Format 1 Detection
            if re.search(r"Grade\s*History|rds3", p1_text, re.IGNORECASE):
                return cls._parse_format_1(pdf)

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
        """Format 2: Official Transcript (Coordinate-based word extraction to bypass watermarks)"""
        records = []
        
        sem_pattern = re.compile(r"^\s*(Spring|Summer|Fall)\s+(\d{4})\s*$", re.IGNORECASE)
        # Matches: COURSE_CODE | Course Title | Cr. | Gr. | CC | CP
        # Example: ACT201 | Introduction to Financial Accounting | 3.0 | A- | 3.0 | 3.0
        # This regex is flexible with spaces and pipes.
        course_pattern = re.compile(
            r"^\s*([A-Za-z]{2,4}\s*\d{3})\s*[|]?\s*(.+?)\s+[|]?\s*(\d+\.\d+)\s*[|]?\s*([A-Za-z][+-]?|I|W|WV|X)\s*[|]?\s*(\d+\.\d+)\s*[|]?\s*(\d+\.\d+)\s*$"
        )
        
        # Start scanning from Page 2
        for page in pdf.pages[1:]:
            words = page.extract_words()
            if not words:
                continue
                
            page_text = " ".join([w['text'] for w in words]).lower()
            if "grading system" in page_text or "grading legend" in page_text or "transcript details" in page_text:
                continue  # Skip legend pages entirely
            
            # Split words into Left and Right columns mathematically
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
                    
                # Sort vertically
                word_list.sort(key=lambda w: w['top'])
                lines = []
                current_line = []
                current_top = word_list[0]['top']
                
                for w in word_list:
                    if abs(w['top'] - current_top) <= tolerance:
                        current_line.append(w)
                    else:
                        # Flush current line, sorted horizontally
                        current_line.sort(key=lambda x: x['x0'])
                        lines.append(" ".join([x['text'] for x in current_line]))
                        current_line = [w]
                        current_top = w['top']
                
                # Flush remainder
                if current_line:
                    current_line.sort(key=lambda x: x['x0'])
                    lines.append(" ".join([x['text'] for x in current_line]))
                    
                return lines

            # Parse lines chronologically
            left_lines = group_words_into_lines(left_col_words)
            right_lines = group_words_into_lines(right_col_words)
            all_lines = left_lines + right_lines
            
            current_semester = ""
            current_year = ""
            
            for line in all_lines:
                line = line.strip()
                if not line:
                    continue
                
                sem_match = sem_pattern.match(line)
                if sem_match:
                    current_semester = sem_match.group(1).title()
                    current_year = sem_match.group(2)
                    continue
                    
                course_match = course_pattern.match(line)
                if course_match:
                    code = course_match.group(1).replace(" ", "").upper()
                    title = course_match.group(2).strip()
                    credit_str = course_match.group(3).strip()
                    grade = course_match.group(4).strip().upper()
                    
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
