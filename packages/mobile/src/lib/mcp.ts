import { env } from "./env";
import { HttpError, requestJson } from "./http";
import type { CourseRecord } from "../types/audit";

const VALID_GRADES = new Set(["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F", "P", "T"]);

function normalizeCode(value: string): string {
  const cleaned = value.trim().toUpperCase().replace(/\s+/g, "").replace(/[^A-Z0-9]/g, "");
  if (!cleaned || cleaned.length > 20) return "";
  return cleaned;
}

function normalizeGrade(value: string): string | null {
  const grade = value.trim().toUpperCase();
  if (VALID_GRADES.has(grade)) return grade;
  if (grade === "A+") return "A";
  return null;
}

function toCredits(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(12, Math.round(value)));
}

function toWhole(value: number, fallback = 0): number {
  if (!Number.isFinite(value)) return fallback;
  return Math.max(0, Math.round(value));
}

type PlanPayload = {
  student_record: {
    student_id: string;
    courses: CourseRecord[];
  };
  program_requirements: {
    program_code: string;
    total_credits_required: number;
    core_courses_required: string[];
    elective_credit_required: number;
    elective_pool: string[];
  };
  available_courses: Array<{
    course_code: string;
    credits: number;
    category: "CORE" | "ELECTIVE" | "GENERAL";
  }>;
};

export type PlannerPlan = {
  courses: string[];
  totalCredits: number;
  rationale: string;
  eligibleAfter: boolean | null;
  remainingRequirements: string[];
};

async function toolCall<T>(tool: string, payload: unknown): Promise<T> {
  try {
    return await requestJson<T>(`${env.mcpUrl}/v1/tools/${tool}`, {
      method: "POST",
      body: payload,
    });
  } catch (error) {
    if (error instanceof HttpError && error.status === 422) {
      const detail = (error.detail as { detail?: unknown } | null)?.detail;
      if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0] as { msg?: unknown; loc?: unknown };
        const msg = typeof first?.msg === "string" ? first.msg : "Invalid MCP payload";
        const loc = Array.isArray(first?.loc) ? first.loc.join(".") : "payload";
        throw new Error(`MCP validation failed at ${loc}: ${msg}`);
      }
      throw new Error("MCP rejected request (422). Check transcript data format.");
    }
    throw error;
  }
}

export async function generatePlannerPlans(basePayload: PlanPayload, options: { maxCourses?: number; maxCredits?: number } = {}): Promise<{
  fastest: PlannerPlan;
  balanced: PlannerPlan;
  cgpa: PlannerPlan;
}> {
  const sanitizedStudentCourses = basePayload.student_record.courses
    .map((course) => {
      const code = normalizeCode(course.course_code);
      const grade = normalizeGrade(course.grade);
      if (!code || !grade) return null;
      return {
        course_code: code,
        credits: toCredits(course.credits),
        grade,
      };
    })
    .filter((row): row is CourseRecord => row !== null);

  const sanitizedAvailableCourses = basePayload.available_courses
    .map((course) => {
      const code = normalizeCode(course.course_code);
      if (!code) return null;
      return {
        course_code: code,
        credits: toCredits(course.credits),
        category: course.category,
      };
    })
    .filter(
      (row): row is { course_code: string; credits: number; category: "CORE" | "ELECTIVE" | "GENERAL" } => row !== null
    );

  const payload: PlanPayload = {
    student_record: {
      student_id: String(basePayload.student_record.student_id || "unknown"),
      courses: sanitizedStudentCourses,
    },
    program_requirements: {
      program_code: String(basePayload.program_requirements.program_code || "CSE"),
      total_credits_required: toWhole(basePayload.program_requirements.total_credits_required, 130),
      core_courses_required: Array.from(new Set(basePayload.program_requirements.core_courses_required.map(normalizeCode).filter(Boolean))),
      elective_credit_required: toWhole(basePayload.program_requirements.elective_credit_required, 0),
      elective_pool: Array.from(new Set(basePayload.program_requirements.elective_pool.map(normalizeCode).filter(Boolean))),
    },
    available_courses: sanitizedAvailableCourses,
  };

  const [opt, plan] = await Promise.all([
    toolCall<{ minimum_course_set: string[]; rationale: string }>("optimize_graduation_path", payload),
    toolCall<{ recommended_courses: string[]; reasoning: string }>("plan_path", payload),
  ]);

  const fastestCourses = Array.isArray(opt.minimum_course_set) ? opt.minimum_course_set : [];
  const balancedCourses = Array.isArray(plan.recommended_courses) ? plan.recommended_courses : [];
  const cgpaCourses = [...balancedCourses].sort((a, b) => {
    const aLab = a.endsWith("L") ? 1 : 0;
    const bLab = b.endsWith("L") ? 1 : 0;
    return aLab - bLab || a.localeCompare(b);
  });

  const creditsByCode = new Map(payload.available_courses.map((course) => [course.course_code, course.credits]));
  const limitPlanCourses = (courses: string[]): string[] => {
    const maxCourses = Math.max(1, options.maxCourses ?? (courses.length || 1));
    const maxCredits = Math.max(1, options.maxCredits ?? Number.MAX_SAFE_INTEGER);
    const limitedByCount = Array.from(new Set(courses.filter(Boolean))).slice(0, maxCourses);
    const result: string[] = [];
    let usedCredits = 0;
    for (const code of limitedByCount) {
      const credits = creditsByCode.get(code) ?? 3;
      if (result.length > 0 && usedCredits + credits > maxCredits) continue;
      result.push(code);
      usedCredits += credits;
    }
    return result;
  };

  const limitedFastestCourses = limitPlanCourses(fastestCourses);
  const limitedBalancedCourses = limitPlanCourses(balancedCourses);
  const limitedCgpaCourses = limitPlanCourses(cgpaCourses);

  const totalCredits = (courses: string[]) => courses.reduce((sum, code) => sum + (creditsByCode.get(code) ?? 3), 0);

  const simulate = async (courses: string[]): Promise<{ eligible_after: boolean; remaining_requirements: string[] }> => {
    return toolCall<{ eligible_after: boolean; remaining_requirements: string[] }>("simulate_changes", {
      student_record: payload.student_record,
      program_requirements: payload.program_requirements,
      hypothetical_courses: courses.map((code) => ({ course_code: code, credits: creditsByCode.get(code) ?? 3, grade: "B" })),
    });
  };

  const [fastestSim, balancedSim, cgpaSim] = await Promise.all([
    simulate(limitedFastestCourses),
    simulate(limitedBalancedCourses),
    simulate(limitedCgpaCourses),
  ]);

  return {
    fastest: {
      courses: limitedFastestCourses,
      totalCredits: totalCredits(limitedFastestCourses),
      rationale: opt.rationale || "Minimum-course path",
      eligibleAfter: fastestSim.eligible_after,
      remainingRequirements: fastestSim.remaining_requirements || [],
    },
    balanced: {
      courses: limitedBalancedCourses,
      totalCredits: totalCredits(limitedBalancedCourses),
      rationale: plan.reasoning || "Balanced progression path",
      eligibleAfter: balancedSim.eligible_after,
      remainingRequirements: balancedSim.remaining_requirements || [],
    },
    cgpa: {
      courses: limitedCgpaCourses,
      totalCredits: totalCredits(limitedCgpaCourses),
      rationale: "Lower-intensity ordering for GPA recovery.",
      eligibleAfter: cgpaSim.eligible_after,
      remainingRequirements: cgpaSim.remaining_requirements || [],
    },
  };
}
