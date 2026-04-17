from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from tools.registry import ToolSpec, get_tool_registry


app = FastAPI(
    title="Graduation Audit MCP Server",
    version="1.0.0",
    description="Deterministic MCP server for graduation audit tools.",
)

TOOL_REGISTRY: dict[str, ToolSpec] = get_tool_registry()


class JsonRpcRequest(BaseModel):
    jsonrpc: str = Field(default="2.0")
    id: int | str | None = None
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


def _jsonrpc_success(request_id: int | str | None, result: dict[str, Any]) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": result})


def _jsonrpc_error(
    request_id: int | str | None,
    code: int,
    message: str,
    data: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message, "data": data or {}},
        }
    )


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "graduation-audit-mcp"}


@app.post("/mcp")
def mcp_endpoint(request: JsonRpcRequest):
    if request.jsonrpc != "2.0":
        return _jsonrpc_error(request.id, -32600, "Invalid Request: jsonrpc must be '2.0'.")

    if request.method == "initialize":
        return _jsonrpc_success(
            request.id,
            {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "graduation-audit-mcp", "version": "1.0.0"},
                "capabilities": {"tools": {"listChanged": False}},
            },
        )

    if request.method == "tools/list":
        return _jsonrpc_success(
            request.id,
            {"tools": [spec.to_mcp_descriptor() for spec in TOOL_REGISTRY.values()]},
        )

    if request.method == "tools/call":
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})

        if not isinstance(tool_name, str) or not tool_name:
            return _jsonrpc_error(request.id, -32602, "Invalid params: 'name' is required.")

        spec = TOOL_REGISTRY.get(tool_name)
        if spec is None:
            return _jsonrpc_error(request.id, -32601, f"Tool '{tool_name}' not found.")

        try:
            parsed_input = spec.input_model.model_validate(arguments)
            output = spec.handler(parsed_input)
            output_payload = output.model_dump()
        except Exception as exc:
            return _jsonrpc_error(
                request.id,
                -32000,
                "Tool execution failed.",
                {"tool": tool_name, "detail": str(exc)},
            )

        return _jsonrpc_success(
            request.id,
            {
                "content": [{"type": "text", "text": json.dumps(output_payload, separators=(",", ":"))}],
                "structuredContent": output_payload,
                "isError": False,
            },
        )

    return _jsonrpc_error(request.id, -32601, f"Method '{request.method}' not found.")


@app.get("/tools")
def list_tools_rest() -> dict[str, Any]:
    return {"tools": [spec.to_mcp_descriptor() for spec in TOOL_REGISTRY.values()]}


@app.post("/tools/{tool_name}")
def call_tool_rest(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    spec = TOOL_REGISTRY.get(tool_name)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    parsed_input = spec.input_model.model_validate(payload)
    result = spec.handler(parsed_input)
    return result.model_dump()
