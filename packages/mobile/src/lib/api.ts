import { z } from "zod";
import { env } from "./env";
import { requestJson } from "./http";
import { supabase } from "./supabase";
import type { AuditDetail, AuditSummary, CourseRecord, TranscriptCourseRow, UploadFileAsset } from "../types/audit";

const EnvelopeSchema = z.object({
  success: z.boolean(),
  data: z.unknown().nullable(),
  error: z.string().nullable(),
});

function parseEnvelope<T>(payload: unknown): { success: boolean; data: T | null; error: string | null } {
  const parsed = EnvelopeSchema.safeParse(payload);
  if (parsed.success) {
    return {
      success: parsed.data.success,
      data: parsed.data.data as T | null,
      error: parsed.data.error,
    };
  }
  return {
    success: true,
    data: payload as T,
    error: null,
  };
}

async function accessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

function normalizeHistoryItem(item: unknown): AuditSummary | null {
  if (!item || typeof item !== "object") return null;
  const record = item as Record<string, unknown>;

  const nestedPayload =
    (record.result as Record<string, unknown> | undefined) ??
    (record.audit_result as Record<string, unknown> | undefined) ??
    (record.audit as Record<string, unknown> | undefined) ??
    record;

  const level1 = (nestedPayload.level_1 as Record<string, unknown> | undefined) ?? {};
  const level2 = (nestedPayload.level_2 as Record<string, unknown> | undefined) ?? {};
  const level3 = (nestedPayload.level_3 as Record<string, unknown> | undefined) ?? {};
  const reasons = Array.isArray(level3.reasons) ? level3.reasons : [];

  const toNumber = (value: unknown, fallback = 0): number => {
    const parsed = typeof value === "string" ? Number(value) : value;
    return typeof parsed === "number" && Number.isFinite(parsed) ? parsed : fallback;
  };

  const transcriptId =
    (typeof record.transcript_id === "string" && record.transcript_id) ||
    (typeof record.id === "string" && record.id) ||
    "";
  if (!transcriptId) return null;

  return {
    id: (typeof record.id === "string" && record.id) || transcriptId,
    transcriptId,
    program:
      (nestedPayload.meta as { program?: string } | undefined)?.program ||
      (typeof record.program === "string" ? record.program : "CSE"),
    eligible: Boolean(level3.eligible),
    cgpa: toNumber(level2.cgpa, toNumber(record.cgpa, 0)),
    creditsEarned: toNumber(level1.credits_earned, toNumber(record.credits_earned, 0)),
    totalRequired: toNumber(level3.total_credits_required, toNumber(record.total_credits_required, 130)),
    issuesCount: reasons.length || toNumber(record.issues_count, 0),
    createdAt:
      (typeof record.created_at === "string" && record.created_at) ||
      (typeof nestedPayload.created_at === "string" ? nestedPayload.created_at : undefined),
  };
}

async function authorizedJson<T>(path: string, method: "GET" | "POST" | "PUT" | "DELETE" = "GET", body?: unknown): Promise<T> {
  const token = await accessToken();
  const payload = await requestJson<unknown>(`${env.apiUrl}${path}`, {
    method,
    token,
    body,
  });
  const envelope = parseEnvelope<T>(payload);
  if (!envelope.success) {
    throw new Error(envelope.error || "API request failed");
  }
  if (envelope.data === null) {
    throw new Error("API returned empty data");
  }
  return envelope.data;
}

async function publicJson<T>(path: string, method: "GET" | "POST" | "PUT" | "DELETE" = "GET", body?: unknown): Promise<T> {
  const payload = await requestJson<unknown>(`${env.apiUrl}${path}`, {
    method,
    body,
  });
  const envelope = parseEnvelope<T>(payload);
  if (!envelope.success) {
    throw new Error(envelope.error || "API request failed");
  }
  if (envelope.data === null) {
    throw new Error("API returned empty data");
  }
  return envelope.data;
}

export async function listAuditHistory(): Promise<AuditSummary[]> {
  const data = await authorizedJson<unknown[]>("/audit");
  if (!Array.isArray(data)) return [];
  const base = data.map(normalizeHistoryItem).filter((value): value is AuditSummary => value !== null);

  const hydrated = await Promise.all(
    base.map(async (item) => {
      const needsHydration = item.cgpa === 0 && item.creditsEarned === 0;
      if (!needsHydration) return item;
      try {
        const detail = await authorizedJson<AuditDetail>(`/audit/${item.transcriptId}`);
        const creditsEarned = typeof detail.level_1?.credits_earned === "number" ? detail.level_1.credits_earned : item.creditsEarned;
        const cgpa = typeof detail.level_2?.cgpa === "number" ? detail.level_2.cgpa : item.cgpa;
        const totalRequired =
          typeof detail.level_3?.total_credits_required === "number" ? detail.level_3.total_credits_required : item.totalRequired;
        const reasonsCount = Array.isArray(detail.level_3?.reasons) ? detail.level_3.reasons.length : item.issuesCount;
        return {
          ...item,
          creditsEarned,
          cgpa,
          totalRequired,
          issuesCount: reasonsCount,
        };
      } catch {
        return item;
      }
    })
  );

  return hydrated;
}

export async function getAuditDetail(transcriptId: string): Promise<AuditDetail> {
  return authorizedJson<AuditDetail>(`/audit/${transcriptId}`);
}

export async function getTranscriptCourses(transcriptId: string): Promise<CourseRecord[]> {
  const rows = await getTranscriptRawData(transcriptId);
  return rows
    .map((row) => {
      const code = row.course_code.trim().toUpperCase();
      const grade = row.grade.trim().toUpperCase();
      const credits = Number(row.credits ?? 0);
      if (!code || !grade || !Number.isFinite(credits)) return null;
      return { course_code: code, grade, credits: Math.max(0, Math.min(12, Math.round(credits))) };
    })
    .filter((entry): entry is CourseRecord => entry !== null);
}

export async function getTranscriptRawData(transcriptId: string): Promise<TranscriptCourseRow[]> {
  const data = await authorizedJson<unknown>(`/transcripts/${transcriptId}`);
  if (!data || typeof data !== "object") return [];
  const rawData = (data as { raw_data?: unknown }).raw_data;
  if (!Array.isArray(rawData)) return [];

  const rows: TranscriptCourseRow[] = [];
  rawData.forEach((row) => {
      if (!row || typeof row !== "object") return;
      const record = row as Record<string, unknown>;
      const code = typeof record.course_code === "string" ? record.course_code.trim().toUpperCase() : "";
      if (!code) return;
      rows.push({
        course_code: code,
        course_name: typeof record.course_name === "string" ? record.course_name : undefined,
        credits: Number(record.credits ?? 0),
        grade: typeof record.grade === "string" ? record.grade.toUpperCase() : "",
        semester: typeof record.semester === "string" ? record.semester : undefined,
      });
    });

  return rows;
}

export async function updateTranscriptRawData(
  transcriptId: string,
  rows: TranscriptCourseRow[]
): Promise<void> {
  await authorizedJson<unknown>(`/transcripts/${transcriptId}`, "PUT", {
    raw_data: rows.map((row) => ({
      course_code: row.course_code,
      course_name: row.course_name || "",
      credits: row.credits,
      grade: row.grade,
      semester: row.semester || "",
    })),
  });
}

export async function runAudit(transcriptId: string, program: "CSE" | "BBA", concentration?: string): Promise<AuditDetail> {
  return authorizedJson<AuditDetail>(`/audit/${transcriptId}`, "POST", {
    program,
    concentration: concentration || undefined,
  });
}

export async function uploadTranscript(file: UploadFileAsset): Promise<{ id: string }> {
  const token = await accessToken();
  const formData = new FormData();
  const filePart = {
    uri: file.uri,
    name: file.name,
    type: file.mimeType,
  };

  formData.append("file", filePart as unknown as Blob);

  const response = await fetch(`${env.apiUrl}/transcripts/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: formData,
  });

  const payload = (await response.json().catch(() => null)) as unknown;
  if (!response.ok) {
    const envelope = parseEnvelope<unknown>(payload);
    throw new Error(envelope.error || "Upload failed");
  }

  const envelope = parseEnvelope<{ id: string }>(payload);
  if (!envelope.success || !envelope.data?.id) {
    throw new Error(envelope.error || "Upload response missing transcript id");
  }
  return envelope.data;
}

type RegisterResponse = {
  user_id: string;
  email: string;
  message: string;
};

export async function registerAccount(email: string, password: string): Promise<RegisterResponse> {
  return publicJson<RegisterResponse>("/auth/register", "POST", {
    email,
    password,
  });
}
