import os

def create_cse_eligible():
    courses = [
        # Major Core (51cr)
        ("CSE173", "Discrete Mathematics", 3, "A", "Spring 2021"),
        ("CSE215", "Programming Language II", 3, "A-", "Summer 2021"),
        ("CSE215L", "Programming Language II Lab", 1, "A", "Summer 2021"),
        ("CSE225", "Data Structures & Algorithms", 3, "B+", "Autumn 2021"),
        ("CSE225L", "Data Structures & Algorithms Lab", 1, "A", "Autumn 2021"),
        ("CSE231", "Digital Logic Design", 3, "B", "Spring 2022"),
        ("CSE231L", "Digital Logic Design Lab", 1, "A", "Spring 2022"),
        ("CSE299", "Junior Design Project", 1, "A", "Spring 2022"),
        ("CSE311", "Database Management Systems", 3, "A", "Summer 2022"),
        ("CSE311L", "Database Management Systems Lab", 1, "A", "Summer 2022"),
        ("CSE323", "Operating Systems Design", 3, "B+", "Autumn 2022"),
        ("CSE325", "Operating Systems", 3, "B", "Autumn 2022"),
        ("CSE327", "Software Engineering", 3, "A-", "Spring 2023"),
        ("CSE331", "Microprocessor Interfacing & Embedded", 3, "B+", "Summer 2023"),
        ("CSE331L", "Microprocessor Interfacing Lab", 1, "A", "Summer 2023"),
        ("CSE332", "Computer Organization & Architecture", 3, "B", "Summer 2023"),
        ("CSE373", "Design & Analysis of Algorithms", 3, "A", "Autumn 2023"),
        ("CSE425", "Concepts of Programming Languages", 3, "A-", "Spring 2024"),
        ("EEE141", "Electrical Circuits I", 3, "B", "Autumn 2021"),
        ("EEE141L", "Electrical Circuits I Lab", 1, "A", "Autumn 2021"),
        ("EEE111", "Analog Electronics I", 3, "B+", "Spring 2022"),
        ("EEE111L", "Analog Electronics I Lab", 1, "A", "Spring 2022"),
        # Capstone (7cr)
        ("CSE499A", "Senior Capstone Design I", 2, "A", "Summer 2024"),
        ("CSE499B", "Senior Capstone Design II", 2, "A", "Autumn 2024"),
        ("EEE452", "Engineering Economics", 3, "B+", "Autumn 2023"),
        # SEPS Core (45cr)
        ("CSE115", "Programming Language I", 3, "A", "Spring 2021"),
        ("CSE115L", "Programming Language I Lab", 1, "A", "Spring 2021"),
        ("MAT116", "Pre-Calculus", 3, "A", "Spring 2021"),
        ("MAT120", "Calculus I", 3, "A-", "Summer 2021"),
        ("MAT125", "Linear Algebra", 3, "B+", "Summer 2021"),
        ("MAT130", "Calculus II", 3, "B", "Autumn 2021"),
        ("MAT250", "Calculus III", 3, "B+", "Spring 2022"),
        ("MAT350", "Complex Variables", 3, "A-", "Summer 2022"),
        ("MAT361", "Discrete Mathematics II", 3, "B+", "Autumn 2022"),
        ("PHY107", "Physics I", 3, "B", "Summer 2021"),
        ("PHY107L", "Physics I Lab", 1, "A", "Summer 2021"),
        ("PHY108", "Physics II", 3, "B+", "Autumn 2021"),
        ("PHY108L", "Physics II Lab", 1, "A", "Autumn 2021"),
        ("CHE101", "Chemistry I", 3, "B", "Spring 2022"),
        ("CHE101L", "Chemistry I Lab", 1, "A", "Spring 2022"),
        ("BIO103", "Biology I", 3, "A-", "Summer 2022"),
        ("BIO103L", "Biology I Lab", 1, "A", "Summer 2022"),
        ("CEE110", "Engineering Drawing", 1, "A", "Autumn 2022"),
        # GED (21cr)
        ("ENG103", "Intermediate Composition", 3, "A", "Spring 2021"),
        ("ENG105", "Advanced Writing Skills", 3, "A", "Summer 2021"),
        ("ENG111", "Public Speaking", 3, "A-", "Autumn 2021"),
        ("PHI101", "Introduction to Philosophy", 3, "B+", "Spring 2022"),
        ("PHI104", "Introduction to Ethics", 3, "B", "Summer 2022"),
        ("HIS101", "Bangladesh History & Culture", 3, "A", "Autumn 2022"),
        ("HIS102", "World Civilization", 3, "A-", "Spring 2023"),
        # Choice (9cr)
        ("ECO101", "Intro to Microeconomics", 3, "A", "Autumn 2023"),
        ("POL101", "Intro to Political Science", 3, "A", "Spring 2024"),
        ("SOC101", "Intro to Sociology", 3, "A", "Summer 2024"),
        # Waivable (3cr)
        ("ENG102", "Intro to Composition", 3, "A", "Spring 2021"),
        ("MAT112", "College Algebra", 0, "A", "Spring 2021"),
        # Electives (12cr)
        ("CSE421", "Machine Learning", 3, "A", "Spring 2024"),
        ("CSE422", "Simulation and Modeling", 3, "A", "Summer 2024"),
        ("CSE472", "Advanced Algorithms", 3, "A", "Autumn 2024"),
        ("CSE473", "Parallel Processing", 3, "A", "Autumn 2024"),
        # Open Elective (3cr)
        ("CSE101", "Intro to Python Programming", 3, "A", "Autumn 2023"),
    ]
    write_csv("test_verification/cse_eligible.csv", courses)

def create_cse_ineligible():
    # Same as eligible, but remove CSE327 and HIS102
    courses = [
        ("CSE173", "Discrete Mathematics", 3, "A", "Spring 2021"),
        ("CSE215", "Programming Language II", 3, "A-", "Summer 2021"),
        ("CSE215L", "Programming Language II Lab", 1, "A", "Summer 2021"),
        ("CSE225", "Data Structures & Algorithms", 3, "B+", "Autumn 2021"),
        ("CSE225L", "Data Structures & Algorithms Lab", 1, "A", "Autumn 2021"),
        ("CSE231", "Digital Logic Design", 3, "B", "Spring 2022"),
        ("CSE231L", "Digital Logic Design Lab", 1, "A", "Spring 2022"),
        ("CSE299", "Junior Design Project", 1, "A", "Spring 2022"),
        ("CSE311", "Database Management Systems", 3, "A", "Summer 2022"),
        ("CSE311L", "Database Management Systems Lab", 1, "A", "Summer 2022"),
        ("CSE323", "Operating Systems Design", 3, "B+", "Autumn 2022"),
        ("CSE325", "Operating Systems", 3, "B", "Autumn 2022"),
        # CSE327 REMOVED
        ("CSE331", "Microprocessor Interfacing & Embedded", 3, "B+", "Summer 2023"),
        ("CSE331L", "Microprocessor Interfacing Lab", 1, "A", "Summer 2023"),
        ("CSE332", "Computer Organization & Architecture", 3, "B", "Summer 2023"),
        ("CSE373", "Design & Analysis of Algorithms", 3, "A", "Autumn 2023"),
        ("CSE425", "Concepts of Programming Languages", 3, "A-", "Spring 2024"),
        ("EEE141", "Electrical Circuits I", 3, "B", "Autumn 2021"),
        ("EEE141L", "Electrical Circuits I Lab", 1, "A", "Autumn 2021"),
        ("EEE111", "Analog Electronics I", 3, "B+", "Spring 2022"),
        ("EEE111L", "Analog Electronics I Lab", 1, "A", "Spring 2022"),
        ("CSE499A", "Senior Capstone Design I", 2, "A", "Summer 2024"),
        ("CSE499B", "Senior Capstone Design II", 2, "A", "Autumn 2024"),
        ("EEE452", "Engineering Economics", 3, "B+", "Autumn 2023"),
        ("CSE115", "Programming Language I", 3, "A", "Spring 2021"),
        ("CSE115L", "Programming Language I Lab", 1, "A", "Spring 2021"),
        ("MAT116", "Pre-Calculus", 3, "A", "Spring 2021"),
        ("MAT120", "Calculus I", 3, "A-", "Summer 2021"),
        ("MAT125", "Linear Algebra", 3, "B+", "Summer 2021"),
        ("MAT130", "Calculus II", 3, "B", "Autumn 2021"),
        ("MAT250", "Calculus III", 3, "B+", "Spring 2022"),
        ("MAT350", "Complex Variables", 3, "A-", "Summer 2022"),
        ("MAT361", "Discrete Mathematics II", 3, "B+", "Autumn 2022"),
        ("PHY107", "Physics I", 3, "B", "Summer 2021"),
        ("PHY107L", "Physics I Lab", 1, "A", "Summer 2021"),
        ("PHY108", "Physics II", 3, "B+", "Autumn 2021"),
        ("PHY108L", "Physics II Lab", 1, "A", "Autumn 2021"),
        ("CHE101", "Chemistry I", 3, "B", "Spring 2022"),
        ("CHE101L", "Chemistry I Lab", 1, "A", "Spring 2022"),
        ("BIO103", "Biology I", 3, "A-", "Summer 2022"),
        ("BIO103L", "Biology I Lab", 1, "A", "Summer 2022"),
        ("CEE110", "Engineering Drawing", 1, "A", "Autumn 2022"),
        ("ENG103", "Intermediate Composition", 3, "A", "Spring 2021"),
        ("ENG105", "Advanced Writing Skills", 3, "A", "Summer 2021"),
        ("ENG111", "Public Speaking", 3, "A-", "Autumn 2021"),
        ("PHI101", "Introduction to Philosophy", 3, "B+", "Spring 2022"),
        ("PHI104", "Introduction to Ethics", 3, "B", "Summer 2022"),
        ("HIS101", "Bangladesh History & Culture", 3, "A", "Autumn 2022"),
        # HIS102 REMOVED
        ("ECO101", "Intro to Microeconomics", 3, "A", "Autumn 2023"),
        ("POL101", "Intro to Political Science", 3, "A", "Spring 2024"),
        ("SOC101", "Intro to Sociology", 3, "A", "Summer 2024"),
        ("CSE421", "Machine Learning", 3, "A", "Spring 2024"),
        ("CSE422", "Simulation and Modeling", 3, "A", "Summer 2024"),
        ("CSE472", "Advanced Algorithms", 3, "A", "Autumn 2024"),
        ("CSE101", "Intro to Python Programming", 3, "A", "Autumn 2023"),
    ]
    write_csv("test_verification/cse_ineligible.csv", courses)

def create_bba_eligible():
    courses = [
        # School Core (21cr)
        ("ECO101", "Intro to Microeconomics", 3, "A", "Spring 2021"),
        ("ECO104", "Intro to Macroeconomics", 3, "A-", "Summer 2021"),
        ("MIS107", "Introduction to Computers", 3, "B+", "Autumn 2021"),
        ("BUS251", "Business Communication", 3, "A", "Spring 2022"),
        ("BUS172", "Introduction to Statistics", 3, "B", "Summer 2022"),
        ("BUS173", "Applied Statistics", 3, "A-", "Autumn 2022"),
        ("BUS135", "Business Mathematics", 3, "B+", "Spring 2023"),
        # Core (39cr)
        ("ACT201", "Intro to Financial Accounting", 3, "A", "Summer 2021"),
        ("ACT202", "Intro to Managerial Accounting", 3, "B+", "Autumn 2021"),
        ("FIN254", "Intro to Financial Management", 3, "A", "Spring 2022"),
        ("LAW200", "Legal Environment of Business", 3, "A-", "Summer 2022"),
        ("INB372", "International Business", 3, "B+", "Autumn 2022"),
        ("MGT212", "Principles of Management", 3, "B", "Spring 2023"),
        ("MKT202", "Introduction to Marketing", 3, "A", "Summer 2023"),
        ("BUS101", "Introduction to Business", 3, "A-", "Autumn 2023"),
        ("MIS207", "Management Information Systems", 3, "B+", "Spring 2024"),
        ("MGT351", "Human Resource Management", 3, "B", "Summer 2024"),
        ("MGT314", "Production Management", 3, "A-", "Autumn 2024"),
        ("MGT368", "Entrepreneurship", 3, "B+", "Spring 2025"),
        ("MGT489", "Strategic Management", 3, "A", "Summer 2025"),
        # GED (9cr fixed)
        ("ENG103", "Intermediate Composition", 3, "A", "Spring 2021"),
        ("ENG105", "Advanced Composition", 3, "A-", "Summer 2021"),
        ("PHI401", "Ethics / Philosophy", 3, "B+", "Autumn 2021"),
        # GED Choice (Lots)
        ("BEN205", "Bengali Literature", 3, "A", "Spring 2022"),
        ("HIS101", "Bangladesh History & Culture", 3, "A", "Summer 2022"),
        ("HIS102", "World Civilization", 3, "A-", "Autumn 2022"),
        ("POL101", "Intro to Political Science", 3, "B+", "Spring 2023"),
        ("SOC101", "Intro to Sociology", 3, "B", "Summer 2023"),
        ("BIO103", "Biology I", 3, "A", "Autumn 2023"),
        ("ENV107", "Environmental Science", 3, "A-", "Spring 2024"),
        ("PBH101", "Public Health", 3, "B+", "Summer 2024"),
        ("BIO103L", "Biology I Lab", 1, "A", "Autumn 2023"),
        # Waivable (6cr)
        ("ENG102", "Intro to Composition", 3, "A", "Spring 2021"),
        ("BUS112", "Intro to Business Math", 3, "A", "Spring 2021"),
        # Internship (4cr)
        ("BUS498", "Internship", 4, "A", "Autumn 2025"),
        # Concentration INB (18cr) - 4 Req + 2 Elec
        ("INB400", "International Business Strategy", 3, "A", "Summer 2024"),
        ("INB490", "INB Capstone", 3, "A", "Autumn 2024"),
        ("INB480", "Global Operations", 3, "A-", "Spring 2025"),
        ("MKT382", "International Marketing", 3, "B+", "Summer 2025"),
        ("INB410", "Cross-Cultural Management", 3, "A", "Autumn 2025"),
        ("INB350", "Global Marketing", 3, "A-", "Spring 2026"),
        # Free Electives (11cr)
        ("ECO249", "Socio Economic Profiles", 3, "A", "Autumn 2024"),
        ("BUS401", "Business Ethics", 3, "A", "Spring 2025"),
        ("INT101", "Intro to IR", 3, "A", "Summer 2025"),
        ("ENV203", "Environmental Studies", 3, "A", "Spring 2026"),
    ]
    write_csv("test_verification/bba_eligible.csv", courses)

def create_bba_ineligible():
    # Complete list but lots of Cs and Ds to fail CGPA
    courses = [
        ("ECO101", "Intro to Microeconomics", 3, "D", "Spring 2021"),
        ("ECO104", "Intro to Macroeconomics", 3, "D+", "Summer 2021"),
        ("MIS107", "Introduction to Computers", 3, "C-", "Autumn 2021"),
        ("BUS251", "Business Communication", 3, "C", "Spring 2022"),
        ("BUS172", "Introduction to Statistics", 3, "D", "Summer 2022"),
        ("BUS173", "Applied Statistics", 3, "D+", "Autumn 2022"),
        ("BUS135", "Business Mathematics", 3, "C-", "Spring 2023"),
        ("ACT201", "Intro to Financial Accounting", 3, "D", "Summer 2021"),
        ("ACT202", "Intro to Managerial Accounting", 3, "C", "Autumn 2021"),
        ("FIN254", "Intro to Financial Management", 3, "D", "Spring 2022"),
        ("LAW200", "Legal Environment of Business", 3, "C-", "Summer 2022"),
        ("INB372", "International Business", 3, "D+", "Autumn 2022"),
        ("MGT212", "Principles of Management", 3, "C", "Spring 2023"),
        ("MKT202", "Introduction to Marketing", 3, "D", "Summer 2023"),
        ("BUS101", "Introduction to Business", 3, "C-", "Autumn 2023"),
        ("MIS207", "Management Information Systems", 3, "D+", "Spring 2024"),
        ("MGT351", "Human Resource Management", 3, "C", "Summer 2024"),
        ("MGT314", "Production Management", 3, "D", "Autumn 2024"),
        ("MGT368", "Entrepreneurship", 3, "C-", "Spring 2025"),
        ("MGT489", "Strategic Management", 3, "D+", "Summer 2025"),
        ("ENG103", "Intermediate Composition", 3, "D", "Spring 2021"),
        ("ENG105", "Advanced Composition", 3, "C", "Summer 2021"),
        ("PHI401", "Ethics / Philosophy", 3, "D+", "Autumn 2021"),
        ("BEN205", "Bengali Literature", 3, "C", "Spring 2022"),
        ("HIS101", "Bangladesh History & Culture", 3, "D", "Summer 2022"),
        ("HIS102", "World Civilization", 3, "C-", "Autumn 2022"),
        ("POL101", "Intro to Political Science", 3, "D+", "Spring 2023"),
        ("SOC101", "Intro to Sociology", 3, "C", "Summer 2023"),
        ("BIO103", "Biology I", 3, "D", "Autumn 2023"),
        ("ENV107", "Environmental Science", 3, "C-", "Spring 2024"),
        ("PBH101", "Public Health", 3, "D+", "Summer 2024"),
        ("BIO103L", "Biology I Lab", 1, "C", "Autumn 2023"),
        ("BUS498", "Internship", 4, "C", "Autumn 2025"),
        # Use FIN concentration
        ("FIN433", "Investment Analysis", 3, "D", "Summer 2024"),
        ("FIN440", "International Finance", 3, "C-", "Autumn 2024"),
        ("FIN435", "Financial Institutions", 3, "D+", "Spring 2025"),
        ("FIN444", "Financial Markets", 3, "C", "Summer 2025"),
        ("FIN455", "Derivatives", 3, "D", "Autumn 2025"),
        ("FIN464", "Corporate Finance", 3, "C-", "Spring 2026"),
        ("ECO244", "Applied Economics", 3, "D+", "Autumn 2024"),
        ("ECO301", "Micro Theory", 3, "C", "Spring 2025"),
        ("ECO304", "Macro Theory", 3, "D", "Summer 2025"),
        ("ENG115", "Advanced English", 3, "D", "Summer 2025"), # Total 120
    ]
    write_csv("test_verification/bba_ineligible.csv", courses)

def write_csv(path, courses):
    with open(path, "w") as f:
        f.write("course_code,course_name,credits,grade,semester\n")
        for c in courses:
            f.write(f"{c[0]},{c[1]},{c[2]},{c[3]},{c[4]}\n")

if __name__ == "__main__":
    create_cse_eligible()
    create_cse_ineligible()
    create_bba_eligible()
    create_bba_ineligible()
    print("CSVs generated successfully in test_verification/")
