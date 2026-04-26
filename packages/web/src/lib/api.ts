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

type ApiEnvelope<T = unknown> = {
    success: boolean;
    data: T | null;
    error: string | null;
};

async function getToken(): Promise<string | null> {
    if (typeof window === "undefined") return null;
    const { supabase } = await import("./supabase");
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
}

function getAdminToken(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem("admin_token");
}

async function request<T = unknown>(
    path: string,
    options: RequestInit = {}
): Promise<ApiEnvelope<T>> {
    const isAdminPath = path.startsWith("/admin");
    const requestUrl = isAdminPath ? `/api${path}` : `${API_URL}${path}`;
    const token = isAdminPath ? getAdminToken() : await getToken();
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
    };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    try {
        const res = await fetch(requestUrl, { ...options, headers });
        const json = (await res.json().catch(() => ({ detail: res.statusText }))) as unknown;
        
        if (!res.ok) {
            let errorMsg = "Request failed";
            if (typeof json === "object" && json !== null && "detail" in json) {
                const detail = (json as { detail?: unknown }).detail;
                if (Array.isArray(detail)) {
                    errorMsg = detail
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
                } else if (typeof detail === "string") {
                    errorMsg = detail;
                } else if (
                    typeof detail === "object" &&
                    detail !== null &&
                    "msg" in detail &&
                    typeof (detail as { msg?: unknown }).msg === "string"
                ) {
                    errorMsg = (detail as { msg: string }).msg;
                } else {
                    errorMsg = JSON.stringify(detail);
                }
            }
            console.error(`API Error [${res.status}]:`, { path, json, errorMsg });
            return { success: false, data: null, error: errorMsg };
        }

        if (
            typeof json === "object" &&
            json !== null &&
            "success" in json &&
            "data" in json &&
            "error" in json
        ) {
            return json as ApiEnvelope<T>;
        }

        return { success: true, data: json as T, error: null };
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
    getAdminStats: () => request("/admin/stats"),
    listAdminAudits: () => request("/admin/audits"),
    listAdmins: () => request<string[]>("/admin/admins"),
    addAdmin: (admin_id: string, password: string) =>
        request("/admin/admins", { method: "POST", body: JSON.stringify({ admin_id, password }) }),
    removeAdmin: (admin_id: string) => request(`/admin/admins/${admin_id}`, { method: "DELETE" }),
    listPrograms: () => request("/admin/programs"),
    updatePrograms: (entries: Record<string, unknown>[]) =>
        request("/admin/programs", { method: "PUT", body: JSON.stringify(entries) }),
    deleteProgram: (program_code: string) => request(`/admin/programs/${encodeURIComponent(program_code)}`, { method: "DELETE" }),

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
