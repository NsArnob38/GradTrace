const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            return { success: false, data: null, error: err.detail || "Request failed" };
        }
        return await res.json();
    } catch (err: any) {
        return { success: false, data: null, error: err.message || "Network error" };
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

        const res = await fetch(`${API_URL}/transcripts/upload`, {
            method: "POST",
            headers: {
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: form,
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: "Upload failed" }));
            return { success: false, data: null, error: err.detail };
        }
        return res.json();
    },
    listTranscripts: () => request("/transcripts"),
    getTranscript: (id: string) => request(`/transcripts/${id}`),

    // Audit
    runAudit: (transcriptId: string, program: string, concentration?: string) =>
        fetch(`${API_URL}/audit/${transcriptId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ program, concentration }),
        }).then(res => res.json()),
    getAuditResult: (transcriptId: string) => request(`/audit/${transcriptId}`),
    listHistory: () => request("/audit"),
    deleteHistory: (transcriptId: string) => request(`/audit/${transcriptId}`, { method: "DELETE" }),

    // Admin
    listStudents: () => request("/admin/students"),
    getStudent: (id: string) => request(`/admin/students/${id}`),
    listPrograms: () => request("/admin/programs"),
    updatePrograms: (entries: Record<string, unknown>[]) =>
        request("/admin/programs", { method: "PUT", body: JSON.stringify(entries) }),
};
