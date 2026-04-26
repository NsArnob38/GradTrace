from __future__ import annotations

from copy import deepcopy
from typing import Any

from packages.core import course_catalog as course_catalog_module
from packages.core.course_catalog import CourseCatalog


_DEFAULTS = {
    "CSE_MAJOR_CORE": deepcopy(CourseCatalog.CSE_MAJOR_CORE),
    "CSE_CAPSTONE": deepcopy(CourseCatalog.CSE_CAPSTONE),
    "CSE_SEPS_CORE": deepcopy(CourseCatalog.CSE_SEPS_CORE),
    "CSE_GED_REQUIRED": deepcopy(CourseCatalog.CSE_GED_REQUIRED),
    "CSE_GED_CHOICE_1": deepcopy(CourseCatalog.CSE_GED_CHOICE_1),
    "CSE_GED_CHOICE_2": deepcopy(CourseCatalog.CSE_GED_CHOICE_2),
    "CSE_GED_CHOICE_3": deepcopy(CourseCatalog.CSE_GED_CHOICE_3),
    "CSE_GED_WAIVABLE": deepcopy(CourseCatalog.CSE_GED_WAIVABLE),
    "CSE_TOTAL_CREDITS": CourseCatalog.CSE_TOTAL_CREDITS,
    "CSE_ELECTIVE_CREDITS": CourseCatalog.CSE_ELECTIVE_CREDITS,
    "CSE_OPEN_ELECTIVE_CREDITS": CourseCatalog.CSE_OPEN_ELECTIVE_CREDITS,
    "BBA_SCHOOL_CORE": deepcopy(CourseCatalog.BBA_SCHOOL_CORE),
    "BBA_CORE": deepcopy(CourseCatalog.BBA_CORE),
    "BBA_GED": deepcopy(CourseCatalog.BBA_GED),
    "BBA_GED_WAIVABLE": deepcopy(CourseCatalog.BBA_GED_WAIVABLE),
    "BBA_GED_CHOICE_LANG": deepcopy(CourseCatalog.BBA_GED_CHOICE_LANG),
    "BBA_GED_CHOICE_HIS": deepcopy(CourseCatalog.BBA_GED_CHOICE_HIS),
    "BBA_GED_CHOICE_POL": deepcopy(CourseCatalog.BBA_GED_CHOICE_POL),
    "BBA_GED_CHOICE_SOC": deepcopy(CourseCatalog.BBA_GED_CHOICE_SOC),
    "BBA_GED_CHOICE_SCI": deepcopy(CourseCatalog.BBA_GED_CHOICE_SCI),
    "BBA_GED_CHOICE_LAB": deepcopy(CourseCatalog.BBA_GED_CHOICE_LAB),
    "BBA_INTERNSHIP": deepcopy(CourseCatalog.BBA_INTERNSHIP),
    "BBA_TOTAL_CREDITS": CourseCatalog.BBA_TOTAL_CREDITS,
    "BBA_FREE_ELECTIVE_CREDITS": CourseCatalog.BBA_FREE_ELECTIVE_CREDITS,
    "BBA_CONCENTRATIONS": deepcopy(CourseCatalog.BBA_CONCENTRATIONS),
    "VALID_CONCENTRATIONS": deepcopy(CourseCatalog.VALID_CONCENTRATIONS),
    "_CSE_MAJOR_CORE_DB": deepcopy(CourseCatalog._CSE_MAJOR_CORE_DB),
    "_CSE_CAPSTONE_DB": deepcopy(CourseCatalog._CSE_CAPSTONE_DB),
    "_CSE_SEPS_DB": deepcopy(CourseCatalog._CSE_SEPS_DB),
    "_CSE_GED_DB": deepcopy(CourseCatalog._CSE_GED_DB),
    "_CSE_ELECTIVES_400_DB": deepcopy(CourseCatalog._CSE_ELECTIVES_400_DB),
    "_BBA_SCHOOL_CORE_DB": deepcopy(CourseCatalog._BBA_SCHOOL_CORE_DB),
    "_BBA_CORE_DB": deepcopy(CourseCatalog._BBA_CORE_DB),
    "_BBA_GED_DB": deepcopy(CourseCatalog._BBA_GED_DB),
    "_WAIVER_COURSES_DB": deepcopy(CourseCatalog._WAIVER_COURSES_DB),
    "_BBA_CONC_DB": deepcopy(CourseCatalog._BBA_CONC_DB),
}

_CONCENTRATION_LABELS = {
    code: label for code, (_required, _elective, label) in _DEFAULTS["BBA_CONCENTRATIONS"].items()
}

_CSE_DB_MAP_NAMES = (
    "_CSE_MAJOR_CORE_DB",
    "_CSE_CAPSTONE_DB",
    "_CSE_SEPS_DB",
    "_CSE_GED_DB",
    "_CSE_ELECTIVES_400_DB",
)

_BBA_DB_MAP_NAMES = (
    "_BBA_SCHOOL_CORE_DB",
    "_BBA_CORE_DB",
    "_BBA_GED_DB",
    "_WAIVER_COURSES_DB",
    "_BBA_CONC_DB",
)


def _reset_catalog_defaults() -> None:
    for key, value in _DEFAULTS.items():
        setattr(CourseCatalog, key, deepcopy(value))


def _rebuild_catalog_derived() -> None:
    CourseCatalog.CSE_ALL_CORE = {
        **CourseCatalog.CSE_MAJOR_CORE,
        **CourseCatalog.CSE_CAPSTONE,
        **CourseCatalog.CSE_SEPS_CORE,
    }
    CourseCatalog.BBA_ALL_CORE = {
        **CourseCatalog.BBA_SCHOOL_CORE,
        **CourseCatalog.BBA_CORE,
    }
    CourseCatalog.VALID_CONCENTRATIONS = set(CourseCatalog.BBA_CONCENTRATIONS.keys())

    all_courses = CourseCatalog.build_all_courses()
    course_catalog_module.ALL_COURSES.clear()
    course_catalog_module.ALL_COURSES.update(all_courses)


def _remove_code_from_maps(code: str, map_names: tuple[str, ...]) -> None:
    for map_name in map_names:
        target = getattr(CourseCatalog, map_name)
        target.pop(code, None)


def _normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        program_code = str(row.get("program_code") or "").strip().upper()
        course_code = str(row.get("course_code") or "").strip().upper()
        course_name = str(row.get("course_name") or "").strip()
        category = str(row.get("category") or "").strip()
        credits_raw = row.get("credits", 0)
        try:
            credits = int(float(credits_raw))
        except (TypeError, ValueError):
            credits = 0

        if not program_code or not course_code or not category:
            continue

        normalized.append(
            {
                "program_code": program_code,
                "course_code": course_code,
                "course_name": course_name,
                "credits": credits,
                "category": category,
            }
        )
    return normalized


def _sync_cse(rows: list[dict[str, Any]]) -> None:
    major_core: dict[str, int] = {}
    capstone = deepcopy(_DEFAULTS["CSE_CAPSTONE"])
    seps_core: dict[str, int] = {}
    ged_required: dict[str, int] = {}
    ged_choice_1: dict[str, int] = {}
    ged_choice_2: dict[str, int] = {}
    ged_choice_3: dict[str, int] = {}
    waivable = deepcopy(_DEFAULTS["CSE_GED_WAIVABLE"])
    open_elective_credits = _DEFAULTS["CSE_OPEN_ELECTIVE_CREDITS"]

    for row in rows:
        code = row["course_code"]
        credits = row["credits"]
        name = row["course_name"] or code
        category = row["category"]

        _remove_code_from_maps(code, _CSE_DB_MAP_NAMES)

        if category == "major_core":
            major_core[code] = credits
            CourseCatalog._CSE_MAJOR_CORE_DB[code] = (name, credits)
        elif category == "capstone":
            capstone[code] = credits
            CourseCatalog._CSE_CAPSTONE_DB[code] = (name, credits)
        elif category.startswith("SEPS_"):
            seps_core[code] = credits
            CourseCatalog._CSE_SEPS_DB[code] = (name, credits)
        elif category == "GED_open_elective":
            open_elective_credits = max(0, credits)
        elif category == "catalog_only":
            CourseCatalog._CSE_GED_DB[code] = (name, credits)
        elif category.endswith("pick1") or category.endswith("choice_1"):
            ged_choice_1[code] = credits
            CourseCatalog._CSE_GED_DB[code] = (name, credits)
        elif category.endswith("pick2") or category.endswith("choice_2"):
            ged_choice_2[code] = credits
            CourseCatalog._CSE_GED_DB[code] = (name, credits)
        elif category.endswith("pick3") or category.endswith("choice_3"):
            ged_choice_3[code] = credits
            CourseCatalog._CSE_GED_DB[code] = (name, credits)
        elif code in {"ENG102", "MAT112"} or category == "waivable":
            waivable[code] = credits
            CourseCatalog._WAIVER_COURSES_DB[code] = (name, credits)
        elif category.startswith("GED_"):
            ged_required[code] = credits
            CourseCatalog._CSE_GED_DB[code] = (name, credits)
        elif category.startswith("elective_"):
            CourseCatalog._CSE_ELECTIVES_400_DB[code] = (name, credits)

    if major_core:
        CourseCatalog.CSE_MAJOR_CORE = major_core
    if seps_core:
        CourseCatalog.CSE_SEPS_CORE = seps_core
    CourseCatalog.CSE_CAPSTONE = capstone
    if ged_required:
        CourseCatalog.CSE_GED_REQUIRED = ged_required
    CourseCatalog.CSE_GED_CHOICE_1 = ged_choice_1
    CourseCatalog.CSE_GED_CHOICE_2 = ged_choice_2
    CourseCatalog.CSE_GED_CHOICE_3 = ged_choice_3
    CourseCatalog.CSE_GED_WAIVABLE = waivable
    CourseCatalog.CSE_OPEN_ELECTIVE_CREDITS = open_elective_credits


def _sync_bba(rows: list[dict[str, Any]], concentration_rows: list[dict[str, Any]]) -> None:
    school_core: dict[str, int] = {}
    major_core: dict[str, int] = {}
    ged_required: dict[str, int] = {}
    ged_waivable = deepcopy(_DEFAULTS["BBA_GED_WAIVABLE"])
    ged_choice_lang: dict[str, int] = {}
    ged_choice_his: dict[str, int] = {}
    ged_choice_pol: dict[str, int] = {}
    ged_choice_soc: dict[str, int] = {}
    ged_science: dict[str, int] = {}
    ged_labs: dict[str, int] = {}
    internship: dict[str, int] = {}
    free_elective_credits = 0

    for row in rows:
        code = row["course_code"]
        credits = row["credits"]
        name = row["course_name"] or code
        category = row["category"]

        _remove_code_from_maps(code, _BBA_DB_MAP_NAMES)

        if category == "school_core":
            school_core[code] = credits
            CourseCatalog._BBA_SCHOOL_CORE_DB[code] = (name, credits)
        elif category == "major_core":
            major_core[code] = credits
            CourseCatalog._BBA_CORE_DB[code] = (name, credits)
        elif category == "waivable":
            ged_waivable[code] = credits
            CourseCatalog._WAIVER_COURSES_DB[code] = (name, credits)
        elif category == "internship":
            internship[code] = credits
            CourseCatalog._BBA_GED_DB[code] = (name, credits)
        elif category == "free_elective":
            free_elective_credits += max(0, credits)
        elif category == "GED_choice_lang":
            ged_choice_lang[code] = credits
            CourseCatalog._BBA_GED_DB[code] = (name, credits)
        elif category == "GED_choice_his":
            ged_choice_his[code] = credits
            CourseCatalog._BBA_GED_DB[code] = (name, credits)
        elif category == "GED_choice_pol":
            ged_choice_pol[code] = credits
            CourseCatalog._BBA_GED_DB[code] = (name, credits)
        elif category == "GED_choice_soc":
            ged_choice_soc[code] = credits
            CourseCatalog._BBA_GED_DB[code] = (name, credits)
        elif category in {"GED_choice_sci", "GED_science_pick3"}:
            if code.endswith("L"):
                ged_labs[code] = credits
            else:
                ged_science[code] = credits
            CourseCatalog._BBA_GED_DB[code] = (name, credits)
        elif category == "GED_choice_lab":
            ged_labs[code] = credits
            CourseCatalog._BBA_GED_DB[code] = (name, credits)
        elif category.startswith("GED_"):
            ged_required[code] = credits
            CourseCatalog._BBA_GED_DB[code] = (name, credits)

    if school_core:
        CourseCatalog.BBA_SCHOOL_CORE = school_core
    if major_core:
        CourseCatalog.BBA_CORE = major_core
    if ged_required:
        CourseCatalog.BBA_GED = ged_required
    CourseCatalog.BBA_GED_WAIVABLE = ged_waivable
    CourseCatalog.BBA_GED_CHOICE_LANG = ged_choice_lang
    CourseCatalog.BBA_GED_CHOICE_HIS = ged_choice_his
    CourseCatalog.BBA_GED_CHOICE_POL = ged_choice_pol
    CourseCatalog.BBA_GED_CHOICE_SOC = ged_choice_soc
    CourseCatalog.BBA_GED_CHOICE_SCI = ged_science
    CourseCatalog.BBA_GED_CHOICE_LAB = ged_labs
    if internship:
        CourseCatalog.BBA_INTERNSHIP = internship
    if free_elective_credits > 0:
        CourseCatalog.BBA_FREE_ELECTIVE_CREDITS = free_elective_credits

    concentrations: dict[str, tuple[dict[str, int], dict[str, int], str]] = {}
    for row in concentration_rows:
        program_code = row["program_code"]
        if not program_code.startswith("BBA_"):
            continue
        conc_code = program_code.split("_", 1)[1]
        required, elective, label = concentrations.get(
            conc_code,
            ({}, {}, _CONCENTRATION_LABELS.get(conc_code, conc_code)),
        )

        code = row["course_code"]
        credits = row["credits"]
        name = row["course_name"] or code
        category = row["category"]
        _remove_code_from_maps(code, ("_BBA_CONC_DB",))
        if category == "concentration_core":
            required[code] = credits
        elif category == "concentration_elective":
            elective[code] = credits
        CourseCatalog._BBA_CONC_DB[code] = (name, credits)
        concentrations[conc_code] = (required, elective, label)

    if concentrations:
        CourseCatalog.BBA_CONCENTRATIONS = concentrations


def sync_course_catalog_with_supabase(db: Any) -> None:
    _reset_catalog_defaults()

    try:
        response = db.table("programs").select("program_code, course_code, course_name, credits, category").execute()
    except Exception:
        _rebuild_catalog_derived()
        return

    rows = _normalize_rows(response.data or [])
    if not rows:
        _rebuild_catalog_derived()
        return

    cse_rows = [row for row in rows if row["program_code"] == "CSE"]
    bba_rows = [row for row in rows if row["program_code"] == "BBA"]
    bba_concentration_rows = [row for row in rows if row["program_code"].startswith("BBA_")]

    if cse_rows:
        _sync_cse(cse_rows)
    if bba_rows or bba_concentration_rows:
        _sync_bba(bba_rows, bba_concentration_rows)

    _rebuild_catalog_derived()
