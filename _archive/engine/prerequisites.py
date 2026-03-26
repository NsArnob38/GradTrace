"""
Centralized Course Prerequisite Definitions for NSU Audit System.
Used by both the Audit Engine and the Transcript Generator.
"""

PREREQUISITES_CSE = {
    "MAT120": ["MAT116"],
    "MAT130": ["MAT120"],
    "PHY107": ["MAT120"],
    "MAT250": ["MAT130"],
    "MAT350": ["MAT250"],
    "MAT361": ["CSE173"],
    "CSE173": ["CSE115"],
    "CSE215": ["CSE173"],
    "CSE225": ["CSE215"],
    "CSE311": ["CSE225"],
    "CSE373": ["CSE225"],
    "CSE231": ["CSE225", "CSE173"],
    "CSE332": ["CSE231"],
    "CSE323": ["CSE332"],
    "CSE499A": ["_SENIOR_"],
    "CSE499B": ["CSE499A"],
}

PREREQUISITES_BBA = {
    "BUS135": ["BUS112"],
    "BUS172": ["BUS135"],
    "BUS173": ["BUS172"],
    "ENG103": ["ENG102"],
    "ENG105": ["ENG103"],
    "ACT202": ["ACT201"],
    "FIN254": ["ACT201", "BUS172"],
    "ECO104": ["ECO101"],
    "MGT351": ["MGT212"],
    "MGT314": ["MGT212"],
    "MGT368": ["MGT212"],
    "MGT489": ["_SENIOR_", "FIN254", "MKT202", "MGT212"],
}
