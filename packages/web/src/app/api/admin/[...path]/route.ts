import { NextRequest, NextResponse } from "next/server";

function getApiBaseUrl(): string | null {
    const base = process.env.API_URL?.trim() || process.env.NEXT_PUBLIC_API_URL?.trim();
    if (!base) return null;
    return base.replace(/\/+$/, "");
}

async function proxy(request: NextRequest, params: { path?: string[] }) {
    const baseUrl = getApiBaseUrl();
    if (!baseUrl) {
        return NextResponse.json({ detail: "API base URL is not configured." }, { status: 500 });
    }

    const segments = params.path ?? [];
    const target = new URL(`${baseUrl}/admin/${segments.map(encodeURIComponent).join("/")}`);
    target.search = request.nextUrl.search;

    const headers = new Headers();
    const authorization = request.headers.get("authorization");
    const contentType = request.headers.get("content-type");
    if (authorization) headers.set("authorization", authorization);
    if (contentType) headers.set("content-type", contentType);

    const init: RequestInit = {
        method: request.method,
        headers,
        cache: "no-store",
    };

    if (request.method !== "GET" && request.method !== "HEAD") {
        init.body = await request.text();
    }

    try {
        const upstream = await fetch(target, init);
        const text = await upstream.text();
        return new NextResponse(text, {
            status: upstream.status,
            headers: {
                "content-type": upstream.headers.get("content-type") || "application/json",
            },
        });
    } catch {
        return NextResponse.json({ detail: "Unable to reach admin API upstream." }, { status: 502 });
    }
}

export async function GET(request: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
    return proxy(request, await context.params);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
    return proxy(request, await context.params);
}

export async function PUT(request: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
    return proxy(request, await context.params);
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
    return proxy(request, await context.params);
}
