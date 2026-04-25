# GradeTrace Local MCP Server

This folder contains a local-only MCP adapter for GradeTrace. It does not replace the existing FastAPI backend or the existing HTTP graduation MCP server in `mcp_graduation_server/`.

The purpose of this adapter is to let local MCP clients such as Cursor, Claude Desktop, or Codex-style tools start a `stdio` MCP process with `python mcp_server/server.py`.

## What It Exposes

This local server uses `mcp.server.fastmcp.FastMCP` and exposes safe, read-oriented tools first.

Available tools:

- `health_check`
- `inspect_project_structure`
- `list_available_routes`
- `list_datasets`
- `get_training_status`
- `read_recent_training_log`
- `run_ocr_on_image_path`
- `get_latest_eval_metrics`
- `list_graduation_tools`
- `call_graduation_tool`

The graduation tools are bridged from the existing deterministic implementation in `mcp_graduation_server/`.

## Install

From the repository root:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r mcp_server/requirements.txt
```

On macOS/Linux, activate with:

```bash
source .venv/bin/activate
```

## Run

The MCP server is intended to be started by an MCP client over `stdio`:

```bash
python mcp_server/server.py
```

You normally do not run it in a browser. It communicates through stdin/stdout.

## Environment

Optional environment variables:

```env
BACKEND_URL=http://127.0.0.1:8000
GEMINI_API_KEY=your-key-only-if-you-want-run_ocr_on_image_path
```

`BACKEND_URL` is used by `health_check` and the OpenAPI fallback in `list_available_routes`.

`GEMINI_API_KEY` is only needed if you call `run_ocr_on_image_path`. The tool returns an honest configuration error when the key is missing.

## Example Client Config

See `example_mcp_config.json`:

```json
{
  "mcpServers": {
    "project-local-mcp": {
      "command": "python",
      "args": ["/ABSOLUTE/PATH/TO/mcp_server/server.py"],
      "env": {
        "BACKEND_URL": "http://127.0.0.1:8000"
      }
    }
  }
}
```

Change `/ABSOLUTE/PATH/TO/mcp_server/server.py` to the real absolute path on your machine.

Windows example:

```json
"args": ["E:/GradTrace/NSU-Audit-2/mcp_server/server.py"]
```

## Cursor / Claude Desktop

Use the same `mcpServers` object from `example_mcp_config.json` in your client MCP settings.

After saving the config, restart the client so it launches the local Python MCP process.

## Backend Connection Test

To check whether the configured backend is reachable:

```bash
python mcp_server/test_backend_connection.py
```

It checks:

- `BACKEND_URL`
- `/health`
- `/docs`
- `/openapi.json`

It exits gracefully if the backend is not running.

## Safety Notes

- This server is local-only and uses `stdio` by default.
- It does not bind to `0.0.0.0`.
- It does not expose delete or overwrite tools.
- It avoids large/generated folders such as `node_modules`, `.git`, `.venv`, `runs`, `checkpoints`, `datasets`, and binary model/image files during inspection.
- `.env` file values are redacted if text is ever read through helper logic.
- `run_ocr_on_image_path` reads only local JPG/PNG/WEBP/PDF files and enforces a 12 MB safety limit.

## Troubleshooting

- If the client cannot start the server, confirm the Python path and absolute `server.py` path are correct.
- If imports fail, run `pip install -r mcp_server/requirements.txt` inside the same Python environment used by the MCP client.
- If `health_check` says the backend is unavailable, start the API with `python -m uvicorn packages.api.main:app --port 8000 --reload` or update `BACKEND_URL`.
- If OCR fails with a missing key, set `GEMINI_API_KEY` only in the local MCP client environment.
