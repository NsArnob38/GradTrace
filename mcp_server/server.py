from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".next",
    ".venv",
    "__pycache__",
    "build",
    "checkpoints",
    "datasets",
    "dist",
    "env",
    "node_modules",
    "outputs",
    "runs",
    "venv",
}
EXCLUDED_SUFFIXES = {
    ".bin",
    ".ckpt",
    ".h5",
    ".jpg",
    ".jpeg",
    ".onnx",
    ".pdf",
    ".png",
    ".pt",
    ".pth",
    ".safetensors",
    ".webp",
    ".zip",
}
DATASET_DIR_NAMES = {"data", "dataset", "datasets", "samples", "fixtures"}
METRIC_NAME_PATTERN = re.compile(r"(cer|wer|accuracy|acc|loss|eval)", re.IGNORECASE)
METRIC_VALUE_PATTERN = re.compile(r"\b(cer|wer|accuracy|acc|loss)\b\s*[:=]\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)

mcp = FastMCP("gradetrace-local-mcp")


def _safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts) or path.suffix.lower() in EXCLUDED_SUFFIXES


def _redact_env_text(text: str) -> str:
    redacted_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            redacted_lines.append(line)
            continue
        key, _value = line.split("=", 1)
        redacted_lines.append(f"{key}=<redacted>")
    return "\n".join(redacted_lines)


def _read_text_limited(path: Path, limit: int = 12000) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")[:limit]
    if path.name.startswith(".env"):
        return _redact_env_text(text)
    return text


def _latest_file(candidates: list[Path]) -> Path | None:
    readable = [path for path in candidates if path.is_file() and not _is_excluded(path)]
    if not readable:
        return None
    return max(readable, key=lambda path: path.stat().st_mtime)


def _find_files(patterns: tuple[str, ...], max_results: int = 200) -> list[Path]:
    results: list[Path] = []
    for pattern in patterns:
        for path in PROJECT_ROOT.rglob(pattern):
            if len(results) >= max_results:
                return results
            if _is_excluded(path):
                continue
            results.append(path)
    return results


@mcp.tool()
def health_check() -> dict[str, Any]:
    """Check whether the main FastAPI backend is reachable."""
    result: dict[str, Any] = {"backend_url": BACKEND_URL, "alive": False}
    try:
        response = httpx.get(f"{BACKEND_URL}/health", timeout=5.0)
        result.update(
            {
                "alive": response.status_code < 400,
                "status_code": response.status_code,
                "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text[:500],
            }
        )
    except httpx.HTTPError as exc:
        result.update({"error": f"{exc.__class__.__name__}: {exc}"})
    return result


@mcp.tool()
def inspect_project_structure(max_depth: int = 3, max_entries: int = 300) -> dict[str, Any]:
    """Return a summarized project tree while excluding large/generated folders and binary files."""
    max_depth = max(1, min(max_depth, 6))
    max_entries = max(20, min(max_entries, 1000))
    lines: list[str] = [PROJECT_ROOT.name]
    entries_seen = 0

    def walk(directory: Path, depth: int) -> None:
        nonlocal entries_seen
        if depth > max_depth or entries_seen >= max_entries:
            return
        try:
            children = sorted(directory.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
        except OSError:
            return
        for child in children:
            if entries_seen >= max_entries:
                return
            if child.name in EXCLUDED_DIRS or child.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            entries_seen += 1
            suffix = "/" if child.is_dir() else ""
            lines.append(f"{'  ' * depth}{child.name}{suffix}")
            if child.is_dir():
                walk(child, depth + 1)

    walk(PROJECT_ROOT, 1)
    truncated = entries_seen >= max_entries
    return {"root": str(PROJECT_ROOT), "tree": "\n".join(lines), "entries": entries_seen, "truncated": truncated}


@mcp.tool()
def list_available_routes() -> dict[str, Any]:
    """List FastAPI routes by importing the app, falling back to BACKEND_URL/openapi.json."""
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from packages.api.main import app  # type: ignore

        routes = []
        for route in app.routes:
            routes.append(
                {
                    "path": getattr(route, "path", ""),
                    "name": getattr(route, "name", ""),
                    "methods": sorted(getattr(route, "methods", []) or []),
                }
            )
        return {"source": "local_import", "routes": routes}
    except Exception as import_error:
        try:
            response = httpx.get(f"{BACKEND_URL}/openapi.json", timeout=8.0)
            response.raise_for_status()
            openapi = response.json()
            routes = [
                {"path": path, "methods": sorted(methods.keys())}
                for path, methods in openapi.get("paths", {}).items()
                if isinstance(methods, dict)
            ]
            return {"source": "openapi", "routes": routes, "import_error": str(import_error)}
        except Exception as http_error:
            return {
                "source": "unavailable",
                "routes": [],
                "import_error": str(import_error),
                "backend_error": str(http_error),
            }


@mcp.tool()
def list_datasets() -> dict[str, Any]:
    """Find likely dataset directories and manifest files without reading large data files."""
    dataset_dirs: list[dict[str, Any]] = []
    manifest_files: list[dict[str, Any]] = []

    for path in PROJECT_ROOT.rglob("*"):
        if _is_excluded(path):
            continue
        lower_name = path.name.lower()
        if path.is_dir() and lower_name in DATASET_DIR_NAMES:
            try:
                visible_files = [item for item in path.iterdir() if item.is_file() and not _is_excluded(item)]
            except OSError:
                visible_files = []
            dataset_dirs.append({"name": path.name, "path": _safe_relative(path), "file_count_sample": len(visible_files)})
        elif path.is_file() and lower_name in {"manifest.json", "manifest.csv", "metadata.json", "labels.csv", "annotations.json"}:
            manifest_files.append({"name": path.name, "path": _safe_relative(path), "bytes": path.stat().st_size})

    return {"dataset_directories": dataset_dirs[:50], "manifest_files": manifest_files[:100]}


@mcp.tool()
def get_training_status() -> dict[str, Any]:
    """Look for recent training logs, runs, checkpoints, and output folders."""
    interesting_dirs = []
    for name in ("runs", "outputs", "checkpoints", "logs"):
        for path in PROJECT_ROOT.rglob(name):
            if path.is_dir():
                try:
                    latest_child = max(path.iterdir(), key=lambda item: item.stat().st_mtime, default=None)
                except OSError:
                    latest_child = None
                interesting_dirs.append(
                    {
                        "name": path.name,
                        "path": _safe_relative(path),
                        "latest_child": _safe_relative(latest_child) if latest_child else None,
                    }
                )

    logs = _find_files(("*.log", "train*.txt", "training*.txt"), max_results=100)
    latest_log = _latest_file(logs)
    return {
        "status": "No explicit training job status was found." if not latest_log and not interesting_dirs else "Training artifacts found.",
        "artifact_directories": interesting_dirs[:50],
        "latest_log": _safe_relative(latest_log) if latest_log else None,
    }


@mcp.tool()
def read_recent_training_log(lines: int = 100) -> dict[str, Any]:
    """Safely read the last N lines from the most relevant training log."""
    lines = max(1, min(lines, 500))
    logs = _find_files(("*.log", "train*.txt", "training*.txt"), max_results=200)
    latest_log = _latest_file(logs)
    if not latest_log:
        return {"found": False, "message": "No training log file was found."}

    buffer: deque[str] = deque(maxlen=lines)
    with latest_log.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            buffer.append(line.rstrip("\n"))

    text = "\n".join(buffer)
    return {"found": True, "path": _safe_relative(latest_log), "lines": len(buffer), "content": text[:20000]}


@mcp.tool()
def run_ocr_on_image_path(image_path: str) -> dict[str, Any]:
    """Run the existing Gemini transcript parser on a local image/PDF path when configured."""
    path = Path(image_path).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path = path.resolve()

    if not path.exists() or not path.is_file():
        return {"implemented": True, "success": False, "message": "Image/PDF path does not exist or is not a file."}
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".pdf"}:
        return {"implemented": True, "success": False, "message": "Only JPG, PNG, WEBP, and PDF files are supported."}
    if path.stat().st_size > 12 * 1024 * 1024:
        return {"implemented": True, "success": False, "message": "File is larger than the 12 MB safety limit."}

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        return {
            "implemented": True,
            "success": False,
            "message": "OCR parser exists, but GEMINI_API_KEY is not configured for this local MCP process.",
        }

    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from packages.core.pdf_parser import VisionParser  # type: ignore

        rows = VisionParser.parse(path.read_bytes(), gemini_api_key=gemini_key, filename=path.name)
        return {"implemented": True, "success": True, "path": _safe_relative(path), "result": rows}
    except Exception as exc:
        return {"implemented": True, "success": False, "path": _safe_relative(path), "error": str(exc)}


@mcp.tool()
def get_latest_eval_metrics() -> dict[str, Any]:
    """Search recent metric files for CER/WER/accuracy/loss values."""
    candidates = _find_files(("*metrics*.json", "*eval*.json", "*metrics*.csv", "*eval*.csv", "*.log"), max_results=300)
    metric_files = [path for path in candidates if METRIC_NAME_PATTERN.search(path.name)]
    latest = _latest_file(metric_files or candidates)
    if not latest:
        return {"found": False, "message": "No eval or metrics files were found."}

    metrics: dict[str, Any] = {}
    try:
        if latest.suffix.lower() == ".json":
            data = json.loads(_read_text_limited(latest))
            if isinstance(data, dict):
                metrics = {key: value for key, value in data.items() if METRIC_NAME_PATTERN.search(str(key))}
        elif latest.suffix.lower() == ".csv":
            with latest.open("r", encoding="utf-8", errors="replace", newline="") as handle:
                rows = list(csv.DictReader(handle))
                if rows:
                    last = rows[-1]
                    metrics = {key: value for key, value in last.items() if METRIC_NAME_PATTERN.search(str(key))}
        else:
            text = _read_text_limited(latest, limit=20000)
            metrics = {match.group(1).lower(): match.group(2) for match in METRIC_VALUE_PATTERN.finditer(text)}
    except Exception as exc:
        return {"found": True, "path": _safe_relative(latest), "error": str(exc)}

    return {"found": True, "path": _safe_relative(latest), "metrics": metrics}


@mcp.tool()
def list_graduation_tools() -> dict[str, Any]:
    """List deterministic graduation-audit tools from the existing MCP implementation."""
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "mcp_graduation_server"))
        from tools.registry import get_tool_registry  # type: ignore

        registry = get_tool_registry()
        return {"tools": [spec.to_mcp_descriptor() for spec in registry.values()]}
    except Exception as exc:
        return {"tools": [], "error": str(exc)}


@mcp.tool()
def call_graduation_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call one existing deterministic graduation-audit tool locally."""
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "mcp_graduation_server"))
        from tools.registry import get_tool_registry  # type: ignore

        registry = get_tool_registry()
        spec = registry.get(tool_name)
        if spec is None:
            return {"success": False, "error": f"Unknown graduation tool: {tool_name}"}
        parsed = spec.input_model.model_validate(arguments)
        output = spec.handler(parsed)
        return {"success": True, "structuredContent": spec.output_model.model_validate(output).model_dump()}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


if __name__ == "__main__":
    mcp.run()
