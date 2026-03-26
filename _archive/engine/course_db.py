# Centralized Course Database
# ─── Course Pools (Post-Fall 2014, 130-credit curriculum) ───

# CSE Major Core (42 credits)
CSE_MAJOR_CORE = {
    "CSE173": ("Discrete Mathematics", 3),
    "CSE215": ("Programming Language II", 3),
    "CSE215L": ("Programming Language II Lab", 1),
    "CSE225": ("Data Structures & Algorithms", 3),
    "CSE225L": ("Data Structures & Algorithms Lab", 1),
    "CSE231": ("Digital Logic Design", 3),
    "CSE231L": ("Digital Logic Design Lab", 1),
    "CSE299": ("Junior Design Project", 1),
    "CSE311": ("Database Management Systems", 3),
    "CSE311L": ("Database Management Systems Lab", 1),
    "CSE323": ("Operating Systems Design", 3),
    "CSE327": ("Software Engineering", 3),
    "CSE331": ("Microprocessor Interfacing", 3),
    "CSE331L": ("Microprocessor Interfacing Lab", 1),
    "CSE332": ("Computer Organization & Architecture", 3),
    "CSE373": ("Design & Analysis of Algorithms", 3),
    "CSE425": ("Concepts of Programming Languages", 3),
    "EEE141": ("Electrical Circuits I", 3),
    "EEE141L": ("Electrical Circuits I Lab", 1),
    "EEE111": ("Analog Electronics I", 3),
    "EEE111L": ("Analog Electronics I Lab", 1),
}

# CSE Capstone + Engineering Economics (7 credits)
CSE_CAPSTONE = {
    "CSE499A": ("Senior Capstone Design I", 2),
    "CSE499B": ("Senior Capstone Design II", 2),
    "EEE452": ("Engineering Economics", 3),
}

# SEPS Core (41 credits)
CSE_SEPS_CORE = {
    "CSE115": ("Programming Language I", 3),
    "CSE115L": ("Programming Language I Lab", 1),
    "MAT116": ("Pre-Calculus", 3),
    "MAT120": ("Calculus I", 3),
    "MAT125": ("Linear Algebra", 3),
    "MAT130": ("Calculus II", 3),
    "MAT250": ("Calculus III", 3),
    "MAT350": ("Complex Variables", 3),
    "MAT361": ("Discrete Mathematics II", 3),
    "PHY107": ("Physics I", 3),
    "PHY107L": ("Physics I Lab", 1),
    "PHY108": ("Physics II", 3),
    "PHY108L": ("Physics II Lab", 1),
    "CHE101": ("Chemistry I", 3),
    "CHE101L": ("Chemistry I Lab", 1),
    "BIO103": ("Biology I", 3),
    "BIO103L": ("Biology I Lab", 1),
    "CEE110": ("Engineering Drawing", 1),
}

# CSE GED (University Core)
CSE_GED = {
    "ENG103": ("Intermediate Composition", 3),
    "ENG105": ("Advanced Writing Skills", 3),
    "ENG111": ("Public Speaking", 3),
    "PHI104": ("Introduction to Ethics", 3),
    "HIS101": ("Bangladesh History & Culture", 3),
    "HIS102": ("World Civilization", 3),
    "CSE101": ("Introduction to Python Programming", 3),
    "CSE145": ("Introduction to Artificial Intelligence", 3),
    "CSE226": ("Fundamentals of Vibe Coding", 3),
}

CSE_GED_CHOICE_1 = {"ECO101": ("Intro to Microeconomics", 3), "ECO104": ("Intro to Macroeconomics", 3)}
CSE_GED_CHOICE_2 = {"POL101": ("Intro to Political Science", 3), "POL104": ("Political Science", 3)}
CSE_GED_CHOICE_3 = {"SOC101": ("Intro to Sociology", 3), "ANT101": ("Anthropology", 3),
                     "ENV203": ("Environmental Studies", 3), "GEO205": ("Geography", 3)}

CSE_ELECTIVES_400 = {
    "CSE421": ("Machine Learning", 3),
    "CSE423": ("Data Mining", 3),
    "CSE445": ("Computer Vision", 3),
    "CSE461": ("Robotics", 3),
    "CSE471": ("Compiler Design", 3),
}

OPEN_ELECTIVES = {
    "SOC201": ("Social Theory", 3),
    "PHI201": ("Logic", 3),
    "HIS201": ("Modern History", 3),
    # Legacy/Department Transition Permitted Equivalents
    "ETE115": ("Introduction to Telecommunications", 3),
    "MAT120": ("Calculus I", 3),
    "DEV101": ("Development Studies", 3)
}

# BBA School Core (7 courses / 21 credits)
BBA_SCHOOL_CORE = {
    "ECO101": ("Intro to Microeconomics", 3),
    "ECO104": ("Intro to Macroeconomics", 3),
    "MIS107": ("Introduction to Computers", 3),
    "BUS251": ("Business Communication", 3),
    "BUS172": ("Introduction to Statistics", 3),
    "BUS173": ("Applied Statistics", 3),
    "BUS135": ("Business Mathematics", 3),
}

# BBA Core (12 courses / 36 credits)
BBA_CORE = {
    "ACT201": ("Intro to Financial Accounting", 3),
    "ACT202": ("Intro to Managerial Accounting", 3),
    "FIN254": ("Intro to Financial Management", 3),
    "LAW200": ("Legal Environment of Business", 3),
    "INB372": ("International Business", 3),
    "MKT202": ("Introduction to Marketing", 3),
    "MIS207": ("Management Information Systems", 3),
    "MGT212": ("Principles of Management", 3),
    "MGT351": ("Human Resource Management", 3),
    "MGT314": ("Production Management", 3),
    "MGT368": ("Entrepreneurship", 3),
    "MGT489": ("Strategic Management", 3),
}

# BBA GED — Fixed (always required)
BBA_GED = {
    "ENG103": ("Intermediate Composition", 3),
    "ENG105": ("Advanced Composition", 3),
    "PHI401": ("Ethics / Philosophy", 3),
}

# GED Choice Groups
BBA_GED_CHOICE_LANG = {"BEN205": ("Bengali Literature", 3), "ENG115": ("English Literature", 3), "CHN101": ("Chinese Language", 3)}
BBA_GED_CHOICE_HIS = {"HIS101": ("Bangladesh History", 3), "HIS102": ("World Civilization", 3),
                       "HIS103": ("History of South Asia", 3), "HIS205": ("Modern History", 3)}  # pick 2
BBA_GED_CHOICE_POL = {"POL101": ("Intro to Political Science", 3), "POL104": ("Political Science", 3),
                       "PAD201": ("Public Administration", 3)}
BBA_GED_CHOICE_SOC = {"SOC101": ("Intro to Sociology", 3), "GEO205": ("Geography", 3), "ANT101": ("Anthropology", 3)}
BBA_GED_CHOICE_SCI = {"BIO103": ("Biology I", 3), "ENV107": ("Environmental Science", 3), "PBH101": ("Public Health", 3),
                       "PSY101": ("Intro to Psychology", 3), "PHY107": ("Physics I", 3), "CHE101": ("Chemistry I", 3)}  # pick 3
BBA_GED_CHOICE_LAB = {"BIO103L": ("Biology I Lab", 1), "ENV107L": ("Environmental Science Lab", 1),
                       "PBH101L": ("Public Health Lab", 1), "PSY101L": ("Psychology Lab", 1),
                       "PHY107L": ("Physics I Lab", 1), "CHE101L": ("Chemistry I Lab", 1)}  # pick 1

BBA_INTERNSHIP = {"BUS498": ("Internship", 4)}

# BBA Concentration Course Pools — Curriculum 143 Major Map
BBA_CONC_COURSES = {
    "ACT": {
        "required": {"ACT310": ("Intermediate Accounting I", 3), "ACT320": ("Intermediate Accounting II", 3),
                     "ACT360": ("Advanced Managerial Accounting", 3), "ACT370": ("Taxation", 3)},
        "elective": {"ACT380": ("Audit and Assurance", 3), "ACT460": ("Advanced Financial Accounting", 3),
                     "ACT430": ("Accounting Information Systems", 3), "ACT410": ("Financial Statement Analysis", 3)},
    },
    "FIN": {
        "required": {"FIN433": ("Financial Markets and Institutions", 3), "FIN440": ("Corporate Finance", 3),
                     "FIN435": ("Investment Theory", 3), "FIN444": ("International Financial Management", 3)},
        "elective": {"FIN455": ("Financial Modelling Using Excel", 3), "FIN464": ("Derivatives", 3),
                     "FIN470": ("Insurance and Risk Management", 3), "FIN480": ("Behavioural Finance", 3),
                     "FIN410": ("Financial Statement Analysis", 3)},
    },
    "MKT": {
        "required": {"MKT337": ("Promotional Management", 3), "MKT344": ("Consumer Behaviour", 3),
                     "MKT460": ("Strategic Marketing", 3), "MKT470": ("Marketing Research", 3)},
        "elective": {"MKT412": ("Services Marketing", 3), "MKT465": ("Brand Management", 3),
                     "MKT382": ("International Marketing", 3), "MKT417": ("Export-Import Management", 3),
                     "MKT330": ("Retail Management", 3), "MKT450": ("Marketing Channels", 3),
                     "MKT355": ("Agricultural Marketing", 3), "MKT445": ("Sales Management", 3),
                     "MKT475": ("Marketing Analytics", 3)},
    },
    "MGT": {
        "required": {"MGT321": ("Organizational Behavior", 3), "MGT330": ("Designing Effective Organizations", 3),
                     "HRM370": ("Managerial Skill Development", 3), "MGT410": ("Entrepreneurship II", 3)},
        "elective": {"MGT350": ("Managing Quality", 3), "MGT490": ("Project Management", 3),
                     "HRM470": ("Negotiations", 3), "HRM450": ("Industrial Relations", 3),
                     "MIS320": ("IT for Managers", 3)},
    },
    "HRM": {
        "required": {"HRM340": ("Training and Development", 3), "HRM360": ("Planning and Staffing", 3),
                     "HRM380": ("Compensation Theory and Practice", 3), "HRM450": ("Industrial Relations", 3)},
        "elective": {"HRM370": ("Managerial Skill Development", 3), "HRM499": ("Special Topics in HRM", 3),
                     "HRM470": ("Negotiations", 3)},
    },
    "MIS": {
        "required": {"MIS210": ("Computer Programming", 3), "MIS310": ("Systems Analysis", 3),
                     "MIS320": ("IT for Managers", 3), "MIS470": ("IT Project Management", 3)},
        "elective": {"MIS330": ("Database Systems", 3), "MIS410": ("Systems Design", 3),
                     "MIS450": ("IS Security", 3), "MGT490": ("Project Management", 3),
                     "MIS499": ("Special Topics in MIS", 3)},
    },
    "SCM": {
        "required": {"SCM310": ("Supply Chain Management", 3), "SCM320": ("Procurement and Inventory", 3),
                     "SCM450": ("Supply Chain Analytics", 3), "MGT460": ("Logistics Management", 3)},
        "elective": {"MGT360": ("Global Supply Chain", 3), "MGT390": ("Warehouse Management", 3),
                     "MGT470": ("Quality Management", 3), "MGT490": ("Project Management", 3)},
    },
    "ECO": {
        "required": {"ECO201": ("Intermediate Microeconomics", 3), "ECO204": ("Intermediate Macroeconomics", 3),
                     "ECO348": ("Mathematical Economics", 3), "ECO328": ("Econometrics", 3)},
        "elective": {"ECO244": ("Economic Development", 3), "ECO301": ("Monetary Economics", 3),
                     "ECO304": ("International Economics", 3), "ECO317": ("Public Economics", 3),
                     "ECO354": ("Advanced Microeconomics", 3), "ECO410": ("Development Economics", 3),
                     "ECO415": ("Public Finance", 3), "ECO441": ("Labor Economics", 3),
                     "ECO450": ("Game Theory", 3), "ECO460": ("International Trade", 3)},
    },
    "INB": {
        "required": {"INB400": ("International Trade and Finance", 3), "INB490": ("Cross-Cultural Management", 3),
                     "INB480": ("Global Business Strategy", 3), "MKT382": ("International Marketing", 3)},
        "elective": {"INB410": ("International Competitiveness", 3), "INB350": ("International Business Negotiation", 3),
                     "INB355": ("Country Risk Analysis", 3), "INB415": ("Emerging Markets", 3),
                     "INB450": ("Global Entrepreneurship", 3), "INB495": ("Special Topics in INB", 3),
                     "MKT417": ("Export-Import Management", 3)},
    },
}

BBA_CONC_NAMES = list(BBA_CONC_COURSES.keys())  # ["ACT", "FIN", ...]

# Pre-university / Foundation Courses (Waivers)
WAIVER_COURSES = {
    "ENG102": ("Introduction to Composition", 3),
    "MAT112": ("College Algebra", 0),
    "BUS112": ("Intro to Business Mathematics", 3)
}

ALL_COURSES = {}

# Populate ALL_COURSES
dicts_to_merge = [
    CSE_MAJOR_CORE, CSE_CAPSTONE, CSE_SEPS_CORE, CSE_GED,
    CSE_GED_CHOICE_1, CSE_GED_CHOICE_2, CSE_GED_CHOICE_3,
    CSE_ELECTIVES_400, OPEN_ELECTIVES, WAIVER_COURSES,
    BBA_SCHOOL_CORE, BBA_CORE, BBA_GED, BBA_GED_CHOICE_LANG,
    BBA_GED_CHOICE_HIS, BBA_GED_CHOICE_POL, BBA_GED_CHOICE_SOC,
    BBA_GED_CHOICE_SCI, BBA_GED_CHOICE_LAB, BBA_INTERNSHIP
]

for d in dicts_to_merge:
    ALL_COURSES.update(d)

for conc in BBA_CONC_COURSES.values():
    ALL_COURSES.update(conc['required'])
    ALL_COURSES.update(conc['elective'])

