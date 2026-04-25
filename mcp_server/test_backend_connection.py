from __future__ import annotations

import os
import sys

try:
    import httpx
except ModuleNotFoundError:
    print("Missing dependency: httpx")
    print("Install local MCP dependencies with: pip install -r mcp_server/requirements.txt")
    sys.exit(0)

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> None:
        return None


load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")


def check_endpoint(path: str) -> None:
    url = f"{BACKEND_URL}{path}"
    try:
        response = httpx.get(url, timeout=5.0)
    except httpx.HTTPError as exc:
        print(f"{path}: unavailable ({exc.__class__.__name__}: {exc})")
        return

    print(f"{path}: HTTP {response.status_code}")
    if response.status_code < 400:
        body = response.text[:300].replace("\n", " ")
        print(f"  response: {body}")


def main() -> int:
    print(f"Testing BACKEND_URL={BACKEND_URL}")
    try:
        response = httpx.get(BACKEND_URL, timeout=5.0)
        print(f"/ : HTTP {response.status_code}")
    except httpx.HTTPError as exc:
        print(f"Backend base URL unavailable: {exc.__class__.__name__}: {exc}")
        print("This is okay if the backend is not currently running.")
        return 0

    check_endpoint("/health")
    check_endpoint("/docs")
    check_endpoint("/openapi.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
