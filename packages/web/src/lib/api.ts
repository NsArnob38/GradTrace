const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type JsonRpcId = string | number | null;

type JsonRpcError = {
    code: number;
    message: string;
    data?: unknown;
};

type JsonRpcResponse<T = unknown> = {
    jsonrpc: "2.0";
    id: JsonRpcId;
    result?: T;
    error?: JsonRpcError;
};

async function getToken(): Promise<string | null> {
    if (typeof window === "undefined") return null;
    const { supabase } = await import("./supabase");
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
}

async function request<T = unknown>(
    path: string,
    options: RequestInit = {}
): Promise<{ success: boolean; data: T | null; error: string | null }> {
    const token = await getToken();
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
    };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    try {
        const res = await fetch(`${API_URL}${path}`, { ...options, headers });
        const json = (await res.json().catch(() => ({ detail: res.statusText }))) as {
            detail?: unknown;
        };
        
        if (!res.ok) {
            let errorMsg = "Request failed";
            if (json.detail) {
                if (Array.isArray(json.detail)) {
                    errorMsg = json.detail
                        .map((e) => {
                            if (typeof e !== "object" || e === null) return "error: invalid detail";
                            const detailObj = e as { loc?: unknown; msg?: unknown };
                            const loc = Array.isArray(detailObj.loc)
                                ? detailObj.loc.map((part) => String(part)).join(".")
                                : "error";
                            const msg = typeof detailObj.msg === "string" ? detailObj.msg : "invalid message";
                            return `${loc}: ${msg}`;
                        })
                        .join(", ");
                } else if (typeof json.detail === "string") {
                    errorMsg = json.detail;
                } else if (
                    typeof json.detail === "object" &&
                    json.detail !== null &&
                    "msg" in json.detail &&
                    typeof (json.detail as { msg?: unknown }).msg === "string"
                ) {
                    errorMsg = (json.detail as { msg: string }).msg;
                } else {
                    errorMsg = JSON.stringify(json.detail);
                }
            }
            console.error(`API Error [${res.status}]:`, { path, json, errorMsg });
            return { success: false, data: null, error: errorMsg };
        }
        return json;
    } catch (err: unknown) {
        return {
            success: false,
            data: null,
            error: err instanceof Error ? err.message : "Network error",
        };
    }
}

export const api = {
    // Auth
    getProfile: () => request("/me"),
    updateProfile: (data: Record<string, unknown>) =>
        request("/me", { method: "PUT", body: JSON.stringify(data) }),

    // Transcripts
    uploadTranscript: async (file: File) => {
        const form = new FormData();
        form.append("file", file);

        const { supabase } = await import("./supabase");
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;

        // Use standard request logic for upload but manually handle multipart
        const res = await fetch(`${API_URL}/transcripts/upload`, {
            method: "POST",
            headers: {
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: form,
        });

        if (!res.ok) {
            const err = (await res.json().catch(() => ({ detail: "Upload failed" }))) as {
                detail?: unknown;
            };
            let msg = "Upload failed";
            if (Array.isArray(err.detail)) {
                msg = err.detail
                    .map((e) => {
                        if (typeof e !== "object" || e === null) return "error: invalid detail";
                        const detailObj = e as { loc?: unknown; msg?: unknown };
                        const loc = Array.isArray(detailObj.loc)
                            ? detailObj.loc.map((part) => String(part)).join(".")
                            : "error";
                        const detailMsg = typeof detailObj.msg === "string" ? detailObj.msg : "invalid message";
                        return `${loc}: ${detailMsg}`;
                    })
                    .join(", ");
            } else if (typeof err.detail === "string") {
                msg = err.detail;
            }
            return { success: false, data: null, error: msg };
        }
        return res.json();
    },
    listTranscripts: () => request("/transcripts"),
    getTranscript: (id: string) => request(`/transcripts/${id}`),
    updateTranscriptRawData: (id: string, raw_data: unknown[]) => 
        request(`/transcripts/${id}`, { method: "PUT", body: JSON.stringify({ raw_data }) }),

    // Audit
    runAudit: (
        transcriptId: string, 
        program: string, 
        concentration?: string,
        customMappings?: Record<string, string>,
        ignoredCourses?: string[]
    ) =>
        request(`/audit/${transcriptId}`, {
            method: "POST",
            body: JSON.stringify({ 
                program, 
                concentration,
                custom_mappings: customMappings,
                ignored_courses: ignoredCourses
            }),
        }),
    getAuditResult: (transcriptId: string) => request(`/audit/${transcriptId}`),
    listHistory: () => request("/audit"),
    deleteHistory: (transcriptId: string) => request(`/audit/${transcriptId}`, { method: "DELETE" }),

    // Admin
    listStudents: () => request("/admin/students"),
    getStudent: (id: string) => request(`/admin/students/${id}`),
    listPrograms: () => request("/admin/programs"),
    updatePrograms: (entries: Record<string, unknown>[]) =>
        request("/admin/programs", { method: "PUT", body: JSON.stringify(entries) }),

    // MCP (proxied through Next.js API route)
    mcpCall: async <T = unknown>(method: "initialize" | "tools/list" | "tools/call", params: Record<string, unknown> = {}) => {
        const body = {
            jsonrpc: "2.0" as const,
            id: Date.now(),
            method,
            params,
        };

        try {
            const res = await fetch("/api/mcp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });

            const json = (await res.json().catch(() => null)) as JsonRpcResponse<T> | null;
            if (!res.ok || !json) {
                return {
                    success: false,
                    data: null,
                    error: `MCP proxy failed (${res.status})`,
                };
            }

            if (json.error) {
                return {
                    success: false,
                    data: null,
                    error: `MCP ${json.error.code}: ${json.error.message}`,
                };
            }

            return {
                success: true,
                data: json.result ?? null,
                error: null,
            };
        } catch (err: unknown) {
            return {
                success: false,
                data: null,
                error: err instanceof Error ? err.message : "MCP request failed",
            };
        }
    },

    mcpListTools: () =>
        api.mcpCall<{ tools: unknown[] }>("tools/list"),

    mcpCallTool: <T = unknown>(name: string, argumentsPayload: Record<string, unknown>) =>
        api.mcpCall<T>("tools/call", { name, arguments: argumentsPayload }),
};
