"""
GradeTrace CLI — UI Constants & Helpers

Rich console styling shared across the CLI.
"""

from rich.console import Console
from rich.theme import Theme

# ── Color palette (matches web dark theme) ──
AMBER = "bold rgb(245,158,11)"     # amber-500
GRAY = "rgb(156,163,175)"          # gray-400
RED = "bold rgb(239,68,68)"        # red-500
GREEN = "bold rgb(34,197,94)"      # green-500
BLUE = "bold rgb(59,130,246)"      # blue-500
ORANGE = "bold rgb(249,115,22)"    # orange-500
CYAN = "bold rgb(6,182,212)"       # cyan-500
BOLD = "bold"
DIM = "dim"

custom_theme = Theme({
    "info": "rgb(156,163,175)",
    "success": "bold rgb(34,197,94)",
    "warning": "bold rgb(245,158,11)",
    "danger": "bold rgb(239,68,68)",
    "accent": "bold rgb(245,158,11)",
})

console = Console(theme=custom_theme)


def logo():
    """Print the GradeTrace ASCII logo."""
    console.print()
    console.print(f"  [{AMBER}]★[/] [{BOLD}]GradeTrace[/] [{GRAY}]— Academic Transcript Auditor[/]")
    console.print(f"  [{GRAY}]{'─' * 42}[/]")


def section(title: str):
    """Print a section header."""
    console.print(f"\n  [{AMBER}]▸[/] [{BOLD}]{title}[/]")
    console.print(f"  [{GRAY}]{'─' * 42}[/]")
