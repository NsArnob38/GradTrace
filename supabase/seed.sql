-- GradeTrace — Full Curriculum Seed Data
-- CSE: 130 credits | BBA: 124-130 credits (7 concentrations)

DELETE FROM programs;

INSERT INTO programs (program_code, course_code, course_name, credits, category) VALUES

-- ═══════════════════════════════════════════════
-- CSE PROGRAM — 130 Credits Total
-- ═══════════════════════════════════════════════

-- ── 1. General Education (GED) — 27 Credits ──

-- English (9 cr)
('CSE', 'ENG102', 'Introduction to Composition', 3, 'GED_english'),
('CSE', 'ENG103', 'Intermediate Composition', 3, 'GED_english'),
('CSE', 'ENG111', 'Public Speaking', 3, 'GED_english'),
-- History (6 cr)
('CSE', 'HIS101', 'Bangladesh History and Culture', 3, 'GED_history'),
('CSE', 'HIS102', 'Introduction to World Civilizations', 3, 'GED_history'),
-- Humanities & Philosophy (3 cr)
('CSE', 'PHI104', 'Introduction to Ethics', 3, 'GED_humanities'),
-- Social Sciences (3 cr — pick one)
('CSE', 'ECO101', 'Introduction to Microeconomics', 3, 'GED_social_pick1'),
('CSE', 'POL101', 'Introduction to Political Science', 3, 'GED_social_pick1'),
('CSE', 'SOC101', 'Introduction to Sociology', 3, 'GED_social_pick1'),
('CSE', 'ANT101', 'Introduction to Anthropology', 3, 'GED_social_pick1'),
-- Basic Science (3 cr)
('CSE', 'BIO103', 'Biology I', 3, 'GED_science'),
-- Open Elective (3 cr — any non-SEPS course)
('CSE', 'OPEN_ELECTIVE', 'Open Elective (non-SEPS)', 3, 'GED_open_elective'),

-- ── 2. SEPS Core (Math & Physical Sciences) — 41 Credits ──

-- Mathematics (21 cr)
('CSE', 'MAT116', 'Pre-calculus', 0, 'SEPS_math'),
('CSE', 'MAT120', 'Calculus and Analytical Geometry I', 3, 'SEPS_math'),
('CSE', 'MAT125', 'Introduction to Linear Algebra', 3, 'SEPS_math'),
('CSE', 'MAT130', 'Calculus and Analytical Geometry II', 3, 'SEPS_math'),
('CSE', 'MAT250', 'Calculus and Analytical Geometry III', 3, 'SEPS_math'),
('CSE', 'MAT350', 'Engineering Mathematics', 3, 'SEPS_math'),
('CSE', 'MAT361', 'Probability and Statistics', 3, 'SEPS_math'),
-- Physical Sciences (12 cr)
('CSE', 'PHY107', 'Physics I', 3, 'SEPS_physics'),
('CSE', 'PHY107L', 'Physics I Lab', 1, 'SEPS_physics'),
('CSE', 'PHY108', 'Physics II', 3, 'SEPS_physics'),
('CSE', 'PHY108L', 'Physics II Lab', 1, 'SEPS_physics'),
('CSE', 'CHE101', 'General Chemistry', 3, 'SEPS_physics'),
('CSE', 'CHE101L', 'General Chemistry Lab', 1, 'SEPS_physics'),
-- Engineering Foundation (8 cr)
('CSE', 'EEE141', 'Electrical Circuits I', 3, 'SEPS_engineering'),
('CSE', 'EEE141L', 'Electrical Circuits I Lab', 1, 'SEPS_engineering'),
('CSE', 'EEE111', 'Analog Electronics', 3, 'SEPS_engineering'),
('CSE', 'EEE111L', 'Analog Electronics Lab', 1, 'SEPS_engineering'),

-- ── 3. CSE Major Core — 53 Credits ──

('CSE', 'CSE115', 'Programming Language I', 3, 'major_core'),
('CSE', 'CSE115L', 'Programming Language I Lab', 1, 'major_core'),
('CSE', 'CSE173', 'Discrete Mathematics', 3, 'major_core'),
('CSE', 'CSE215', 'Programming Language II', 3, 'major_core'),
('CSE', 'CSE215L', 'Programming Language II Lab', 1, 'major_core'),
('CSE', 'CSE225', 'Data Structures and Algorithms', 3, 'major_core'),
('CSE', 'CSE225L', 'Data Structures and Algorithms Lab', 1, 'major_core'),
('CSE', 'CSE231', 'Digital Logic Design', 3, 'major_core'),
('CSE', 'CSE231L', 'Digital Logic Design Lab', 1, 'major_core'),
('CSE', 'CSE299', 'Junior Design', 1, 'major_core'),
('CSE', 'CSE311', 'Database Systems', 3, 'major_core'),
('CSE', 'CSE311L', 'Database Systems Lab', 1, 'major_core'),
('CSE', 'CSE323', 'Operating Systems Design', 3, 'major_core'),
('CSE', 'CSE325', 'Operating Systems', 3, 'major_core'),
('CSE', 'CSE327', 'Software Engineering', 3, 'major_core'),
('CSE', 'CSE331', 'Microprocessor Interfacing & Embedded Systems', 3, 'major_core'),
('CSE', 'CSE331L', 'Microprocessor Interfacing Lab', 1, 'major_core'),
('CSE', 'CSE332', 'Computer Organization and Architecture', 3, 'major_core'),
('CSE', 'CSE373', 'Design and Analysis of Algorithms', 3, 'major_core'),
('CSE', 'CSE425', 'Programming Language Principles', 3, 'major_core'),
('CSE', 'EEE452', 'Engineering Economics', 3, 'major_core'),
('CSE', 'CEE110', 'Engineering Drawing / CAD', 1, 'major_core'),
('CSE', 'CSE498', 'Senior Design / Capstone Project', 6, 'capstone'),

-- ── 4. Specialized Electives — 9 Credits (pick 3) ──

-- AI & Data Science
('CSE', 'CSE440', 'Artificial Intelligence', 3, 'elective_ai'),
('CSE', 'CSE445', 'Machine Learning', 3, 'elective_ai'),
('CSE', 'CSE419', 'Data Mining', 3, 'elective_ai'),
('CSE', 'CSE465', 'Pattern Recognition', 3, 'elective_ai'),
('CSE', 'CSE467', 'Image Processing', 3, 'elective_ai'),
('CSE', 'CSE470', 'Theory of Fuzzy Systems', 3, 'elective_ai'),
('CSE', 'CSE448', 'Neural Networks', 3, 'elective_ai'),
-- Software Engineering & Systems
('CSE', 'CSE411', 'Advanced Database Systems', 3, 'elective_se'),
('CSE', 'CSE421', 'Advanced Enterprise Java', 3, 'elective_se'),
('CSE', 'CSE427', 'Software Quality Assurance', 3, 'elective_se'),
('CSE', 'CSE428', 'Software Project Management', 3, 'elective_se'),
('CSE', 'CSE429', 'Software System Architecture', 3, 'elective_se'),
('CSE', 'CSE424', 'Object-Oriented Software Development', 3, 'elective_se'),
('CSE', 'CSE423', 'Advanced Operating Systems', 3, 'elective_se'),
-- Networks & Architecture
('CSE', 'CSE438', 'Networks and Distributed Systems', 3, 'elective_net'),
('CSE', 'CSE439', 'Advanced Computer Networks', 3, 'elective_net'),
('CSE', 'CSE433', 'Computer Architecture', 3, 'elective_net'),
('CSE', 'CSE482', 'Internet and Web Technology', 3, 'elective_net'),
('CSE', 'CSE437', 'Fundamentals of Telecommunications', 3, 'elective_net'),
-- Theory & Hardware
('CSE', 'CSE472', 'Advanced Algorithm', 3, 'elective_theory'),
('CSE', 'CSE473', 'Parallel Processing', 3, 'elective_theory'),
('CSE', 'CSE435', 'Introduction to VLSI Design', 3, 'elective_theory'),
('CSE', 'CSE485', 'Digital Signal Processing', 3, 'elective_theory'),
('CSE', 'CSE487', 'Microprocessor Based System Design', 3, 'elective_theory'),


-- ═══════════════════════════════════════════════
-- BBA PROGRAM — 124-130 Credits Total
-- ═══════════════════════════════════════════════

-- ── 1. University GED — 36 Credits ──

-- Languages (9 cr)
('BBA', 'ENG103', 'Intermediate Composition', 3, 'GED_languages'),
('BBA', 'ENG105', 'Advanced Composition', 3, 'GED_languages'),
('BBA', 'BEN205', 'Bengali Language and Literature', 3, 'GED_languages'),
-- Humanities (9 cr)
('BBA', 'PHI104', 'Introduction to Ethics', 3, 'GED_humanities'),
('BBA', 'HIS101', 'Bangladesh History and Culture', 3, 'GED_humanities'),
('BBA', 'HIS103', 'Emergence of Bangladesh', 3, 'GED_humanities'),
-- Social Sciences (6 cr)
('BBA', 'POL101', 'Political Science', 3, 'GED_social'),
('BBA', 'SOC101', 'Introduction to Sociology', 3, 'GED_social'),
-- Sciences with Lab (12 cr — pick 3 of these)
('BBA', 'BIO103', 'Biology I', 3, 'GED_science_pick3'),
('BBA', 'BIO103L', 'Biology I Lab', 1, 'GED_science_pick3'),
('BBA', 'CHE101', 'Chemistry', 3, 'GED_science_pick3'),
('BBA', 'CHE101L', 'Chemistry Lab', 1, 'GED_science_pick3'),
('BBA', 'ENV107', 'Environmental Science', 3, 'GED_science_pick3'),
('BBA', 'ENV107L', 'Environmental Science Lab', 1, 'GED_science_pick3'),
('BBA', 'PHY107', 'Physics I', 3, 'GED_science_pick3'),
('BBA', 'PHY107L', 'Physics I Lab', 1, 'GED_science_pick3'),
('BBA', 'PSY101', 'Introduction to Psychology', 3, 'GED_science_pick3'),
('BBA', 'PSY101L', 'Introduction to Psychology Lab', 1, 'GED_science_pick3'),

-- ── 2. School Core — 21 Credits ──

('BBA', 'ECO101', 'Introduction to Microeconomics', 3, 'school_core'),
('BBA', 'ECO104', 'Introduction to Macroeconomics', 3, 'school_core'),
('BBA', 'MIS107', 'Computer Information Systems', 3, 'school_core'),
('BBA', 'BUS135', 'Applied Business Mathematics', 3, 'school_core'),
('BBA', 'BUS172', 'Introduction to Statistics', 3, 'school_core'),
('BBA', 'BUS173', 'Applied Statistics', 3, 'school_core'),
('BBA', 'BUS251', 'Business Communication', 3, 'school_core'),

-- ── 3. BBA Major Core — 36 Credits ──

('BBA', 'ACT201', 'Introduction to Financial Accounting', 3, 'major_core'),
('BBA', 'ACT202', 'Introduction to Managerial Accounting', 3, 'major_core'),
('BBA', 'FIN254', 'Introduction to Financial Management', 3, 'major_core'),
('BBA', 'LAW200', 'Legal Environment of Business', 3, 'major_core'),
('BBA', 'MGT212', 'Organizational Management', 3, 'major_core'),
('BBA', 'MGT314', 'Operations Management', 3, 'major_core'),
('BBA', 'MGT351', 'Human Resource Management', 3, 'major_core'),
('BBA', 'MGT368', 'Entrepreneurship', 3, 'major_core'),
('BBA', 'MGT489', 'Strategic Management', 3, 'major_core'),
('BBA', 'MIS207', 'E-Business', 3, 'major_core'),
('BBA', 'MKT202', 'Introduction to Marketing', 3, 'major_core'),
('BBA', 'INB372', 'International Business', 3, 'major_core'),

-- ── 4. Free Electives + Internship — 13 Credits ──

('BBA', 'FREE_ELEC_1', 'Free Elective 1', 3, 'free_elective'),
('BBA', 'FREE_ELEC_2', 'Free Elective 2', 3, 'free_elective'),
('BBA', 'FREE_ELEC_3', 'Free Elective 3', 3, 'free_elective'),
('BBA', 'BUS498', 'Internship', 4, 'internship'),

-- ── 5. Waivable Courses ──

('BBA', 'ENG102', 'Introduction to Composition', 3, 'waivable'),
('BBA', 'BUS112', 'Intro to Business Mathematics', 3, 'waivable'),

-- ═══════════════════════════════════════════════
-- BBA CONCENTRATIONS — 18 Credits each (4 Core + 2 Electives)
-- ═══════════════════════════════════════════════

-- ── FIN — Finance ──
('BBA_FIN', 'FIN433', 'Financial Markets', 3, 'concentration_core'),
('BBA_FIN', 'FIN435', 'Investment Theory', 3, 'concentration_core'),
('BBA_FIN', 'FIN440', 'Corporate Finance', 3, 'concentration_core'),
('BBA_FIN', 'FIN444', 'International Financial Management', 3, 'concentration_core'),
('BBA_FIN', 'FIN464', 'Bank Management', 3, 'concentration_elective'),
('BBA_FIN', 'FIN470', 'Insurance', 3, 'concentration_elective'),
('BBA_FIN', 'FIN480', 'Derivatives', 3, 'concentration_elective'),
('BBA_FIN', 'FIN340', 'Working Capital Management', 3, 'concentration_elective'),

-- ── MKT — Marketing ──
('BBA_MKT', 'MKT337', 'Integrated Marketing Communications', 3, 'concentration_core'),
('BBA_MKT', 'MKT344', 'Consumer Behavior', 3, 'concentration_core'),
('BBA_MKT', 'MKT460', 'Strategic Marketing', 3, 'concentration_core'),
('BBA_MKT', 'MKT470', 'Marketing Research', 3, 'concentration_core'),
('BBA_MKT', 'MKT412', 'Services Marketing', 3, 'concentration_elective'),
('BBA_MKT', 'MKT465', 'Brand Management', 3, 'concentration_elective'),
('BBA_MKT', 'MKT382', 'International Marketing', 3, 'concentration_elective'),
('BBA_MKT', 'MKT417', 'Sales Force Management', 3, 'concentration_elective'),

-- ── ACT — Accounting ──
('BBA_ACT', 'ACT310', 'Intermediate Accounting I', 3, 'concentration_core'),
('BBA_ACT', 'ACT320', 'Intermediate Accounting II', 3, 'concentration_core'),
('BBA_ACT', 'ACT360', 'Cost Accounting', 3, 'concentration_core'),
('BBA_ACT', 'ACT370', 'Auditing', 3, 'concentration_core'),
('BBA_ACT', 'ACT410', 'Financial Statement Analysis', 3, 'concentration_elective'),
('BBA_ACT', 'ACT430', 'Taxation', 3, 'concentration_elective'),
('BBA_ACT', 'ACT460', 'Accounting Information Systems', 3, 'concentration_elective'),

-- ── MIS — Management Information Systems ──
('BBA_MIS', 'MIS210', 'Systems Analysis', 3, 'concentration_core'),
('BBA_MIS', 'MIS310', 'Database Management', 3, 'concentration_core'),
('BBA_MIS', 'MIS320', 'Data Communications & Networks', 3, 'concentration_core'),
('BBA_MIS', 'MIS470', 'MIS Strategy', 3, 'concentration_core'),
('BBA_MIS', 'MIS410', 'Enterprise Systems', 3, 'concentration_elective'),
('BBA_MIS', 'MIS450', 'Business Intelligence', 3, 'concentration_elective'),
('BBA_MIS', 'MIS460', 'Project Management', 3, 'concentration_elective'),

-- ── HRM — Human Resource Management ──
('BBA_HRM', 'HRM340', 'Human Resource Planning', 3, 'concentration_core'),
('BBA_HRM', 'HRM360', 'Training & Development', 3, 'concentration_core'),
('BBA_HRM', 'HRM380', 'Compensation Management', 3, 'concentration_core'),
('BBA_HRM', 'HRM450', 'Strategic HRM', 3, 'concentration_core'),
('BBA_HRM', 'HRM370', 'Managerial Skills', 3, 'concentration_elective'),
('BBA_HRM', 'HRM410', 'Industrial Relations', 3, 'concentration_elective'),
('BBA_HRM', 'HRM470', 'International HRM', 3, 'concentration_elective'),

-- ── SCM — Supply Chain Management ──
('BBA_SCM', 'SCM310', 'Strategic SCM', 3, 'concentration_core'),
('BBA_SCM', 'SCM320', 'Logistics & Inventory', 3, 'concentration_core'),
('BBA_SCM', 'SCM450', 'Procurement', 3, 'concentration_core'),
('BBA_SCM', 'MGT460', 'Total Quality Management', 3, 'concentration_core'),
('BBA_SCM', 'SCM390', 'Global SCM', 3, 'concentration_elective'),
('BBA_SCM', 'SCM470', 'SCM Analytics', 3, 'concentration_elective'),

-- ── INB — International Business ──
('BBA_INB', 'INB400', 'International Trade', 3, 'concentration_core'),
('BBA_INB', 'INB480', 'Global Business Strategy', 3, 'concentration_core'),
('BBA_INB', 'INB490', 'Cross-Cultural Management', 3, 'concentration_core'),
('BBA_INB', 'MKT382', 'International Marketing', 3, 'concentration_core'),
('BBA_INB', 'INB410', 'International Competitiveness', 3, 'concentration_elective'),
('BBA_INB', 'INB450', 'Export-Import Management', 3, 'concentration_elective');
