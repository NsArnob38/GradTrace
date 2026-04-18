import { NextRequest, NextResponse } from "next/server";

type JsonRpcRequest = {
    jsonrpc: "2.0";
    id?: string | number | null;
    method: "initialize" | "tools/list" | "tools/call";
    params?: Record<string, unknown>;
};

function isObject(value: unknown): value is Record<string, unknown> {
    return !!value && typeof value === "object" && !Array.isArray(value);
}

function validateJsonRpcPayload(payload: unknown): payload is JsonRpcRequest {
    if (!isObject(payload)) return false;
    if (payload.jsonrpc !== "2.0") return false;

    const method = payload.method;
    if (method !== "initialize" && method !== "tools/list" && method !== "tools/call") {
        return false;
    }

    if (payload.params !== undefined && !isObject(payload.params)) {
        return false;
    }

    if (method === "tools/call") {
        const params = payload.params;
        if (!isObject(params)) return false;
        if (typeof params.name !== "string" || !params.name.trim()) return false;
        if (params.arguments !== undefined && !isObject(params.arguments)) return false;
    }

    return true;
}

function getMcpUrl(): string | null {
    const base = process.env.MCP_SERVER_URL?.trim();
    if (!base) return null;
    return `${base.replace(/\/+$/, "")}/v1/mcp`;
}

export async function POST(request: NextRequest) {
    const mcpUrl = getMcpUrl();
    if (!mcpUrl) {
        return NextResponse.json(
            { error: "MCP server is not configured (MCP_SERVER_URL missing)." },
            { status: 500 }
        );
    }

    let body: unknown;
    try {
        body = await request.json();
    } catch {
        return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
    }

    if (!validateJsonRpcPayload(body)) {
        return NextResponse.json({ error: "Invalid MCP JSON-RPC payload." }, { status: 400 });
    }

    try {
        const upstream = await fetch(mcpUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            cache: "no-store",
            body: JSON.stringify(body),
        });

        const payload = await upstream.json().catch(() => ({
            jsonrpc: "2.0",
            id: body.id ?? null,
            error: {
                code: -32000,
                message: "Invalid response from MCP upstream.",
                data: {},
            },
        }));

        return NextResponse.json(payload, { status: upstream.status });
    } catch {
        return NextResponse.json(
            {
                jsonrpc: "2.0",
                id: body.id ?? null,
                error: {
                    code: -32001,
                    message: "Unable to reach MCP server.",
                    data: {},
                },
            },
            { status: 502 }
        );
    }
}
