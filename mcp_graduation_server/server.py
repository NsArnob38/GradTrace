from __future__ import annotations

import logging
import os
import json
import time
import uuid
from collections import defaultdict, deque
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from tools.registry import ToolSpec, get_tool_registry


SERVICE_NAME = "graduation-audit-mcp"
SERVICE_VERSION = "1.1.0"
MCP_PROTOCOL_VERSION = "2024-11-05"
MAX_ARGUMENT_BYTES = int(os.getenv("MCP_MAX_ARGUMENT_BYTES", "250000"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("MCP_RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("MCP_RATE_LIMIT_MAX_REQUESTS", "120"))


def _setup_logging() -> logging.Logger:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return logging.getLogger(SERVICE_NAME)


logger = _setup_logging()


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> tuple[bool, int]:
        now = time.monotonic()
        queue = self._events[key]
        cutoff = now - self.window_seconds
        while queue and queue[0] < cutoff:
            queue.popleft()
        if len(queue) >= self.max_requests:
            retry_after = max(1, int(self.window_seconds - (now - queue[0])))
            return False, retry_after
        queue.append(now)
        return True, 0


rate_limiter = RateLimiter(
    max_requests=RATE_LIMIT_MAX_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
)


app = FastAPI(
    title="Graduation Audit MCP Server",
    version=SERVICE_VERSION,
    description="Deterministic MCP server for graduation audit tools.",
)

TOOL_REGISTRY: dict[str, ToolSpec] = get_tool_registry()


class JsonRpcRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

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


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _enforce_rate_limit(request: Request) -> JSONResponse | None:
    client_key = f"{_client_ip(request)}:{request.url.path}"
    allowed, retry_after = rate_limiter.check(client_key)
    if allowed:
        return None
    logger.warning("rate_limited client=%s path=%s", _client_ip(request), request.url.path)
    response = JSONResponse(
        status_code=429,
        content={
            "error": "rate_limited",
            "detail": "Too many requests. Please retry later.",
            "retry_after_seconds": retry_after,
        },
    )
    response.headers["Retry-After"] = str(retry_after)
    return response


def _safe_detail(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return "Input validation failed"
    return "Internal tool execution failure"


def _handle_tool_call(request_id: int | str | None, tool_name: Any, arguments: Any) -> JSONResponse:
    if not isinstance(tool_name, str) or not tool_name:
        return _jsonrpc_error(request_id, -32602, "Invalid params: 'name' is required.")
    if not isinstance(arguments, dict):
        return _jsonrpc_error(request_id, -32602, "Invalid params: 'arguments' must be an object.")

    arg_size = len(json.dumps(arguments, separators=(",", ":"), default=str).encode("utf-8"))
    if arg_size > MAX_ARGUMENT_BYTES:
        return _jsonrpc_error(
            request_id,
            -32602,
            "Invalid params: tool input too large.",
            {"max_bytes": MAX_ARGUMENT_BYTES, "actual_bytes": arg_size},
        )

    spec = TOOL_REGISTRY.get(tool_name)
    if spec is None:
        return _jsonrpc_error(request_id, -32601, f"Tool '{tool_name}' not found.")

    try:
        parsed_input = spec.input_model.model_validate(arguments)
    except ValidationError as exc:
        return _jsonrpc_error(
            request_id,
            -32602,
            "Invalid tool input.",
            {"tool": tool_name, "errors": exc.errors()},
        )

    try:
        output = spec.handler(parsed_input)
        output_payload = spec.output_model.model_validate(output).model_dump()
    except Exception as exc:
        logger.exception("tool_execution_failed tool=%s", tool_name)
        return _jsonrpc_error(
            request_id,
            -32000,
            "Tool execution failed.",
            {"tool": tool_name, "detail": _safe_detail(exc)},
        )

    return _jsonrpc_success(
        request_id,
        {
            "content": [{"type": "text", "text": json.dumps(output_payload, separators=(",", ":"))}],
            "structuredContent": output_payload,
            "isError": False,
        },
    )


def _handle_mcp(request: JsonRpcRequest) -> JSONResponse:
    if request.jsonrpc != "2.0":
        return _jsonrpc_error(request.id, -32600, "Invalid Request: jsonrpc must be '2.0'.")

    if request.method == "initialize":
        return _jsonrpc_success(
            request.id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "serverInfo": {"name": SERVICE_NAME, "version": SERVICE_VERSION},
                "capabilities": {"tools": {"listChanged": False}},
            },
        )

    if request.method == "tools/list":
        return _jsonrpc_success(request.id, {"tools": [spec.to_mcp_descriptor() for spec in TOOL_REGISTRY.values()]})

    if request.method == "tools/call":
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        return _handle_tool_call(request.id, tool_name, arguments)

    return _jsonrpc_error(request.id, -32601, f"Method '{request.method}' not found.")


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    start = time.perf_counter()
    limiter_response = _enforce_rate_limit(request)
    if limiter_response is not None:
        limiter_response.headers["X-Request-ID"] = request_id
        return limiter_response

    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed request_id=%s path=%s", request_id, request.url.path)
        response = JSONResponse(status_code=500, content={"error": "internal_server_error", "request_id": request_id})

    duration_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%s ip=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        _client_ip(request),
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("request_validation_failed path=%s errors=%s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"error": "invalid_request", "detail": exc.errors(), "request_id": getattr(request.state, "request_id", "")},
    )


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "api_versions": ["v1"],
    }


@app.get("/v1/health")
def health_v1() -> dict[str, Any]:
    return health()


@app.post("/mcp")
def mcp_endpoint(request: JsonRpcRequest, _raw_request: Request):
    return _handle_mcp(request)


@app.post("/v1/mcp")
def mcp_endpoint_v1(request: JsonRpcRequest, _raw_request: Request):
    return _handle_mcp(request)


@app.get("/tools")
def list_tools_rest() -> dict[str, Any]:
    return {"tools": [spec.to_mcp_descriptor() for spec in TOOL_REGISTRY.values()]}


@app.get("/v1/tools")
def list_tools_rest_v1() -> dict[str, Any]:
    return list_tools_rest()


@app.post("/tools/{tool_name}")
def call_tool_rest(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    spec = TOOL_REGISTRY.get(tool_name)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    try:
        parsed_input = spec.input_model.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())

    try:
        result = spec.handler(parsed_input)
        return spec.output_model.model_validate(result).model_dump()
    except Exception:
        logger.exception("rest_tool_execution_failed tool=%s", tool_name)
        raise HTTPException(status_code=500, detail="Tool execution failed")


@app.post("/v1/tools/{tool_name}")
def call_tool_rest_v1(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return call_tool_rest(tool_name, payload)
