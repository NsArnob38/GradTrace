"""
GradeTrace Core — PDF Parser

Parses NSU transcript PDF files into uniform dictionaries compatible with our audit engines.
Extracts graded rows and forward-fills semester data. Also extracts waiver/transfer courses with a 'T' grade.
"""

import pdfplumber
import io

class PDFParser:
    """Parses PDF transcripts generated from rds3.northsouth.edu."""

    @staticmethod
    def parse(file_bytes: bytes) -> list[dict]:
        """
        Extracts course records from PDF bytes and maps them to standard dicts:
        [{course_code, course_name, credits, grade, semester}]
        """
        records = []
        
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
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
                            
                            # Filter out footers like 'Semester Credit', 'TGPA', etc.
                            # These usually span columns or sit in the first cell
                            first_col = str(row[0]).strip().lower() if row[0] else ""
                            if "semester credit" in first_col or "tgpa" in first_col or "cgpa" in first_col:
                                continue
                                
                            # Forward-fill Semester metadata if present in row
                            if sem_name_idx != -1 and row[sem_name_idx] and str(row[sem_name_idx]).strip():
                                current_semester = str(row[sem_name_idx]).strip()
                            if sem_year_idx != -1 and row[sem_year_idx] and str(row[sem_year_idx]).strip():
                                current_year = str(row[sem_year_idx]).strip()
                                
                            code = str(row[code_idx]).strip().replace('\n', '') if len(row) > code_idx and row[code_idx] else ""
                            
                            # Skip if no course code is present (e.g., blank row under semester header)
                            if not code:
                                continue
                                
                            name = str(row[name_idx]).strip().replace('\n', ' ') if name_idx != -1 and len(row) > name_idx and row[name_idx] else ""
                            credit = str(row[credit_idx]).strip() if credit_idx != -1 and len(row) > credit_idx and row[credit_idx] else "0"
                            grade = str(row[grade_idx]).strip() if len(row) > grade_idx and row[grade_idx] else ""
                            
                            # Remove decimals (.0) if credit is captured as text float
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
                            
                            # Skip footers if any
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
