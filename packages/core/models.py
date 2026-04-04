"""
GradeTrace Core — Data Models

CourseRecord represents a single course attempt from an academic transcript.
All grade constants and lookup tables are centralized here.
"""

import re
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════
# Grade Constants
# ═══════════════════════════════════════════════════════

GRADE_POINTS = {
    "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0,
    "F": 0.0,
    "I": 0.0,  # Incomplete treated as F
}

PASSING_GRADES = {"A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "T"}
NON_GPA_GRADES = {"W", "T"}
GPA_EXCLUDED_GRADES = {"W", "T"}

GRADE_ORDER = {
    "A": 12, "A-": 11, "B+": 10, "B": 9, "B-": 8,
    "C+": 7, "C": 6, "C-": 5, "D+": 4, "D": 3,
    "F": 1, "I": 0, "W": -1, "T": 13,
}


def grade_to_points(grade: str) -> float | None:
    """Convert a letter grade to GPA points. Returns None if excluded from GPA."""
    if grade in GPA_EXCLUDED_GRADES:
        return None
    return GRADE_POINTS.get(grade, None)


def grade_rank(grade: str) -> int:
    """Return numeric rank for a grade (higher is better). I treated as F."""
    if grade == "I":
        return GRADE_ORDER.get("F", 0)
    return GRADE_ORDER.get(grade, -2)


# ═══════════════════════════════════════════════════════
# Academic Timeline
# ═══════════════════════════════════════════════════════

SEMESTERS = [
    "Spring2005", "Summer2005", "Fall2005",
    "Spring2006", "Summer2006", "Fall2006",
    "Spring2007", "Summer2007", "Fall2007",
    "Spring2008", "Summer2008", "Fall2008",
    "Spring2009", "Summer2009", "Fall2009",
    "Spring2010", "Summer2010", "Fall2010",
    "Spring2011", "Summer2011", "Fall2011",
    "Spring2012", "Summer2012", "Fall2012",
    "Spring2013", "Summer2013", "Fall2013",
    "Spring2014", "Summer2014", "Fall2014",
    "Spring2015", "Summer2015", "Fall2015",
    "Spring2016", "Summer2016", "Fall2016",
    "Spring2017", "Summer2017", "Fall2017",
    "Spring2018", "Summer2018", "Fall2018",
    "Spring2019", "Summer2019", "Fall2019",
    "Spring2020", "Summer2020", "Fall2020",
    "Spring2021", "Summer2021", "Fall2021",
    "Spring2022", "Summer2022", "Fall2022",
    "Spring2023", "Summer2023", "Fall2023",
    "Spring2024", "Summer2024", "Fall2024",
    "Spring2025", "Summer2025", "Fall2025",
    "Spring2026", "Summer2026", "Fall2026",
    "Spring2027", "Summer2027", "Fall2027",
    "Spring2028", "Summer2028", "Fall2028",
    "Spring2029", "Summer2029", "Fall2029",
    "Spring2030", "Summer2030", "Fall2030",
]


# ═══════════════════════════════════════════════════════
# CourseRecord
# ═══════════════════════════════════════════════════════

class CourseRecord:
    """Represents a single course attempt from the transcript."""

    def __init__(self, course_code: str, course_name: str, credits: str | int,
                 grade: str, semester: str, *, all_courses: dict | None = None):
        # 1. Sanitize course code
        raw_code = course_code.strip().upper()
        self.course_code = re.sub(r'\s+', '', raw_code)

        # 2. Sanitize course name
        self.course_name = course_name.strip()

        # 3. Normalize semester string
        raw_sem = semester.strip()
        sem_match = re.match(
            r'(Spring|Summer|Fall|Spr|Sum|Fal)[\s\'-]*(\d{2,4})',
            raw_sem, re.IGNORECASE,
        )
        if sem_match:
            term = sem_match.group(1).capitalize()
            if term == 'Spr': term = 'Spring'
            elif term == 'Sum': term = 'Summer'
            elif term == 'Fal': term = 'Fall'
            year_str = sem_match.group(2)
            if len(year_str) == 2:
                year_str = "20" + year_str
            self.semester = f"{term}{year_str}"
        else:
            self.semester = raw_sem

        # 4. Parse credits & enforce curriculum map
        parsed_credits = int(float(str(credits).strip()))
        if all_courses and self.course_code in all_courses:
            expected = all_courses[self.course_code][1]
            self.credits = expected if parsed_credits != expected else parsed_credits
        else:
            self.credits = parsed_credits

        # 5. Grade
        self.grade = grade.strip().upper()

        # 6. Status — set by the engine later
        self.status = ""

    @property
    def is_passing(self) -> bool:
        return self.grade in PASSING_GRADES

    @property
    def is_withdrawn(self) -> bool:
        return self.grade == "W"

    @property
    def is_transfer(self) -> bool:
        return self.grade == "T"

    @property
    def is_incomplete(self) -> bool:
        return self.grade == "I"

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict."""
        return {
            "course_code": self.course_code,
            "course_name": self.course_name,
            "credits": self.credits,
            "grade": self.grade,
            "semester": self.semester,
            "status": self.status,
        }

    def __repr__(self) -> str:
        return f"<{self.course_code} | {self.grade} | {self.semester} | {self.credits}cr | {self.status}>"
