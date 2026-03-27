"""
GradeTrace CLI — Rich Formatter

Formats API JSON responses into beautiful terminal output using Rich.
"""

from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from packages.cli.ui import console, AMBER, GRAY, RED, GREEN, BLUE, ORANGE, CYAN, BOLD, DIM, section


# ── Course name lookup ──
_COURSE_NAMES: dict | None = None

def _get_course_name(code: str) -> str:
    """Look up a course name from the catalog."""
    global _COURSE_NAMES
    if _COURSE_NAMES is None:
        try:
            from packages.core.course_catalog import ALL_COURSES
            _COURSE_NAMES = {k: v[0] for k, v in ALL_COURSES.items()}
        except Exception:
            _COURSE_NAMES = {}
    return _COURSE_NAMES.get(code, "")


def format_full_audit(result: dict):
    """Format a complete audit result (all levels + roadmap)."""
    meta = result.get("meta", {})
    l1 = result.get("level_1", {})
    l2 = result.get("level_2", {})
    l3 = result.get("level_3", {})
    roadmap = result.get("roadmap", [])

    program = meta.get("program", "?")
    concentration = meta.get("concentration")

    # ── Header ──
    prog_label = program
    if concentration:
        prog_label += f" ({concentration})"
    console.print(f"\n  [{AMBER}]★[/] [{BOLD}]Audit Report[/]  [{GRAY}]Program: {prog_label}[/]")
    console.print(f"  [{GRAY}]{'═' * 48}[/]")

    # ── Summary Cards ──
    _print_summary_cards(l1, l2, l3)

    # ── Level 1: Credit Breakdown ──
    _print_credit_summary(l1)

    # ── Level 2: CGPA & Standing ──
    _print_cgpa_summary(l2)

    # ── Level 3: Graduation Status ──
    _print_graduation_status(l3, program)

    # ── Roadmap ──
    if roadmap:
        if isinstance(roadmap, dict):
            _print_roadmap_dict(roadmap)
        elif isinstance(roadmap, list):
            _print_roadmap_list(roadmap)

    console.print()


def _print_summary_cards(l1: dict, l2: dict, l3: dict):
    """Print the 4 stat cards in a row."""
    cgpa = l2.get("cgpa", 0)
    credits = l1.get("credits_earned", 0)
    standing = l2.get("standing", "—")
    eligible = l3.get("eligible", False)

    cgpa_color = GREEN if cgpa >= 2.0 else RED
    standing_color = GREEN if standing == "NORMAL" else ORANGE
    grad_color = GREEN if eligible else RED

    cards = [
        Panel(
            Text.from_markup(f"[{cgpa_color}]{cgpa:.2f}[/]"),
            title=f"[{AMBER}]CGPA[/]",
            border_style="rgb(245,158,11)",
            width=14,
            padding=(0, 1),
        ),
        Panel(
            Text.from_markup(f"[{BLUE}]{credits}[/]"),
            title=f"[{BLUE}]Credits[/]",
            border_style="rgb(59,130,246)",
            width=14,
            padding=(0, 1),
        ),
        Panel(
            Text.from_markup(f"[{standing_color}]{standing}[/]"),
            title=f"[{GREEN}]Standing[/]",
            border_style="rgb(34,197,94)",
            width=14,
            padding=(0, 1),
        ),
        Panel(
            Text.from_markup(f"[{grad_color}]{'✓ YES' if eligible else '✗ NO'}[/]"),
            title=f"[{ORANGE}]Eligible[/]",
            border_style="rgb(249,115,22)",
            width=14,
            padding=(0, 1),
        ),
    ]

    console.print()
    console.print(Columns(cards, padding=(0, 1), expand=False), justify="center")


def _print_credit_summary(l1: dict):
    """Print Level 1 credit summary."""
    section("Credit Summary")

    attempted = l1.get("credits_attempted", 0)
    earned = l1.get("credits_earned", 0)

    console.print(f"    Credits Attempted:  [{BOLD}]{attempted}[/]")
    console.print(f"    Credits Earned:     [{GREEN}]{earned}[/]")

    records = l1.get("records", [])
    if records:
        statuses = {}
        for r in records:
            s = r.get("status", "UNKNOWN")
            statuses[s] = statuses.get(s, 0) + 1

        parts = []
        for s, count in sorted(statuses.items()):
            color = GREEN if s == "BEST" else GRAY if s == "REPEAT" else ORANGE
            parts.append(f"[{color}]{s}:{count}[/]")
        console.print(f"    Courses:            {' │ '.join(parts)}")


def _print_cgpa_summary(l2: dict):
    """Print Level 2 CGPA breakdown."""
    section("CGPA & Academic Standing")

    cgpa = l2.get("cgpa", 0)
    qp = l2.get("quality_points", 0)
    gpa_credits = l2.get("gpa_credits", 0)
    standing = l2.get("standing", "—")
    prob_count = l2.get("probation_count", 0)
    waivers = l2.get("waivers", {})
    credit_reduction = l2.get("credit_reduction", 0)

    cgpa_color = GREEN if cgpa >= 3.5 else BLUE if cgpa >= 3.0 else AMBER if cgpa >= 2.0 else RED
    console.print(f"    CGPA:               [{cgpa_color}]{cgpa:.4f}[/]")
    console.print(f"    Quality Points:     [{GRAY}]{qp:.2f}[/]")
    console.print(f"    GPA Credits:        [{GRAY}]{gpa_credits}[/]")

    standing_color = GREEN if standing == "NORMAL" else RED
    console.print(f"    Standing:           [{standing_color}]{standing}[/]")

    if prob_count > 0:
        console.print(f"    Probation Count:    [{RED}]{prob_count}[/]")

    if waivers:
        waiver_list = ", ".join(waivers.keys())
        console.print(f"    Waivers Applied:    [{CYAN}]{waiver_list}[/]")

    if credit_reduction > 0:
        console.print(f"    Credit Reduction:   [{ORANGE}]{credit_reduction}[/]")


def _print_graduation_status(l3: dict, program: str):
    """Print Level 3 graduation status."""
    section("Graduation Eligibility")

    eligible = l3.get("eligible", False)
    reasons = l3.get("reasons", [])
    total_required = l3.get("total_credits_required", 0)
    remaining = l3.get("remaining", {})
    prereq_violations = l3.get("prereq_violations", [])

    if eligible:
        console.print(f"    [{GREEN}]✓ ELIGIBLE FOR GRADUATION[/]")
    else:
        console.print(f"    [{RED}]✗ NOT YET ELIGIBLE[/]")
        for reason in reasons:
            console.print(f"      [{RED}]• {reason}[/]")

    console.print(f"    Total Credits Required: [{BOLD}]{total_required}[/]")

    # Program-specific CGPAs
    if program == "CSE":
        major_cgpa = l3.get("major_core_cgpa", 0)
        elective_cgpa = l3.get("major_elective_cgpa", 0)
        console.print(f"    Major Core CGPA:    [{BLUE}]{major_cgpa:.2f}[/]")
        console.print(f"    Elective CGPA:      [{BLUE}]{elective_cgpa:.2f}[/]")
    else:
        core_cgpa = l3.get("core_cgpa", 0)
        conc_cgpa = l3.get("concentration_cgpa", 0)
        conc_label = l3.get("concentration_label", "Undeclared")
        console.print(f"    Core CGPA:          [{BLUE}]{core_cgpa:.2f}[/]")
        console.print(f"    {conc_label} CGPA:   [{BLUE}]{conc_cgpa:.2f}[/]")

    # Remaining courses
    if remaining:
        console.print(f"\n    [{AMBER}]Missing Courses:[/]")
        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
        table.add_column("Category", style=GRAY, max_width=30)
        table.add_column("Course", style="bold", width=10)
        table.add_column("Name", min_width=20)
        table.add_column("Cr", justify="right", width=4)

        for category, courses in remaining.items():
            if isinstance(courses, dict):
                for code, info in courses.items():
                    if isinstance(info, dict):
                        name = info.get("name", _get_course_name(code))
                        cr = info.get("credits", "?")
                    elif isinstance(info, (int, float)):
                        # remaining maps code → credits (int)
                        name = _get_course_name(code)
                        cr = info
                    else:
                        name = str(info)
                        cr = "?"
                    table.add_row(category, code, name, str(cr))
            elif isinstance(courses, list):
                for item in courses:
                    if isinstance(item, dict):
                        table.add_row(category, item.get("code", "?"), item.get("name", ""), str(item.get("credits", "?")))
                    else:
                        table.add_row(category, str(item), "", "")

        console.print(table)

    if prereq_violations:
        console.print(f"\n    [{RED}]Prerequisite Violations:[/]")
        for v in prereq_violations:
            if isinstance(v, dict):
                course = v.get("course", "?")
                sem = v.get("semester", "?")
                missing = ", ".join(v.get("missing", []))
                console.print(f"      [{RED}]• {course} ({sem}) — missing: {missing}[/]")
            else:
                console.print(f"      [{RED}]• {v}[/]")


def _print_roadmap_dict(roadmap: dict):
    """Print roadmap when it's a dict with 'steps', 'credit_gap', etc."""
    section("Graduation Roadmap")

    eligible = roadmap.get("eligible", False)
    steps = roadmap.get("steps", [])
    credit_gap = roadmap.get("credit_gap", 0)
    est_courses = roadmap.get("estimated_courses_left", 0)
    est_semesters = roadmap.get("estimated_semesters", 0)

    if eligible:
        console.print(f"    [{GREEN}]🎓 You have met all graduation requirements![/]")
        return

    # Summary bar
    parts = []
    if credit_gap > 0:
        parts.append(f"[{RED}]{credit_gap} credits short[/]")
    if est_courses > 0:
        parts.append(f"[{AMBER}]{est_courses} courses left[/]")
    if est_semesters > 0:
        parts.append(f"[{BLUE}]~{est_semesters} semester(s)[/]")
    if parts:
        console.print(f"    {' │ '.join(parts)}")
        console.print()

    for step in steps:
        if isinstance(step, str):
            console.print(f"    [{AMBER}]▸[/] {step}")
            continue
        if not isinstance(step, dict):
            console.print(f"    [{GRAY}]• {step}[/]")
            continue

        priority = step.get("priority", "MEDIUM")
        action = step.get("action", "")
        detail = step.get("detail", "")

        p_map = {
            "CRITICAL": (RED, "🔴"),
            "HIGH": (ORANGE, "🟠"),
            "MEDIUM": (AMBER, "🟡"),
            "LOW": (GREEN, "🟢"),
            "DONE": (GREEN, "✅"),
            "RECOMMENDED": (CYAN, "💡"),
        }
        p_color, p_icon = p_map.get(priority, (GRAY, "•"))

        console.print(f"    {p_icon} [{p_color}][{priority}][/] [{BOLD}]{action}[/]")
        if detail:
            console.print(f"       [{GRAY}]{detail}[/]")


def _print_roadmap_list(roadmap: list):
    """Print roadmap when it's a simple list."""
    section("Graduation Roadmap")

    for step in roadmap:
        if isinstance(step, str):
            console.print(f"    [{AMBER}]▸[/] {step}")
        elif isinstance(step, dict):
            priority = step.get("priority", "MEDIUM")
            title = step.get("title", step.get("action", ""))
            detail = step.get("detail", "")
            p_color = RED if priority == "HIGH" else ORANGE if priority == "MEDIUM" else GREEN
            p_icon = "🔴" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🟢"
            console.print(f"    {p_icon} [{p_color}][{priority}][/] [{BOLD}]{title}[/]")
            if detail:
                console.print(f"       [{GRAY}]{detail}[/]")
        else:
            console.print(f"    [{GRAY}]• {step}[/]")


def format_history(history: list):
    """Format scan history list."""
    if not history:
        console.print(f"\n  [{GRAY}]No audit history found. Upload a transcript first.[/]\n")
        return

    section("Audit History")

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("#", style=DIM, width=3)
    table.add_column("File", style="bold")
    table.add_column("CGPA", justify="right")
    table.add_column("Credits", justify="right")
    table.add_column("Standing")
    table.add_column("Eligible")
    table.add_column("Date", style=GRAY)

    for i, item in enumerate(history, 1):
        summary = item.get("summary", {})
        cgpa = summary.get("cgpa", 0)
        credits = summary.get("earned_credits", 0)
        standing = summary.get("probation_phase", "—")
        eligible = summary.get("graduation_eligible", False)
        date = item.get("scanned_at", "")[:10]

        cgpa_color = GREEN if cgpa >= 2.0 else RED
        standing_color = GREEN if standing == "NORMAL" else RED
        elig_str = f"[{GREEN}]✓[/]" if eligible else f"[{RED}]✗[/]"

        table.add_row(
            str(i),
            item.get("file_name", "?"),
            f"[{cgpa_color}]{cgpa:.2f}[/]",
            str(credits),
            f"[{standing_color}]{standing}[/]",
            elig_str,
            date,
        )

    console.print(table)
    console.print()
