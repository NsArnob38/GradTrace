"use client";

import { useEffect, useState, use } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { api } from "@/lib/api";
import {
    Star, ArrowLeft, CheckCircle2, XCircle, AlertTriangle,
    GraduationCap, TrendingUp, BookOpen, MapPin, ChevronDown, ChevronUp, Printer,
    Edit2, Save, X, PlusCircle, Trash2, Sparkles, Gauge, Target
} from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { ThemeToggle } from "@/components/theme-toggle";

/* eslint-disable @typescript-eslint/no-explicit-any */

const VALID_MCP_GRADES = new Set(["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F", "P", "T"]);

function normalizeMcpCode(value: unknown): string {
    return String(value || "")
        .trim()
        .toUpperCase()
        .replace(/\s+/g, "")
        .replace(/[^A-Z0-9]/g, "")
        .slice(0, 20);
}

function normalizeMcpGrade(value: unknown): string | null {
    const grade = String(value || "").trim().toUpperCase();
    if (VALID_MCP_GRADES.has(grade)) return grade;
    if (grade === "A+") return "A";
    return null;
}

function toMcpCredits(value: unknown): number {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return 0;
    return Math.max(0, Math.min(12, Math.round(parsed)));
}

function toMcpWhole(value: unknown, fallback = 0): number {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return fallback;
    return Math.max(0, Math.round(parsed));
}

export default function AuditReportPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [data, setData] = useState<any>(null);
    const [previousData, setPreviousData] = useState<any>(null);
    const [rawCourses, setRawCourses] = useState<any[]>([]);
    const [customMappings, setCustomMappings] = useState<Record<string, string>>({});
    const [ignoredCourses, setIgnoredCourses] = useState<string[]>([]);
    
    const [isEditingData, setIsEditingData] = useState(false);
    const [isReauditing, setIsReauditing] = useState(false);
    
    // Program/Concentration state for re-auditing
    const [selectedProgram, setSelectedProgram] = useState("CSE");
    const [selectedConcentration, setSelectedConcentration] = useState("");
    const [aiPlan, setAiPlan] = useState<Record<string, {
        title: string;
        subtitle: string;
        courses: string[];
        totalCredits: number;
        reasoning: string[];
        overlapCount: number;
        overlapTotal: number;
        eligibleAfter: boolean | null;
        remainingRequirementsCount: number | null;
        remainingCreditDeficit: number | null;
    }> | null>(null);
    const [aiPlanLoading, setAiPlanLoading] = useState(false);
    const [aiPlanError, setAiPlanError] = useState("");
    const [selectedAiPlan, setSelectedAiPlan] = useState("FASTEST");
    const [maxCoursesPerTerm, setMaxCoursesPerTerm] = useState(5);
    const [maxCreditsPerTerm, setMaxCreditsPerTerm] = useState(15);
    
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [auditError, setAuditError] = useState("");
    const [openSections, setOpenSections] = useState<Set<string>>(new Set(["level1", "level2", "level3", "roadmap"]));

    useEffect(() => {
        Promise.all([
            api.getAuditResult(id),
            api.getTranscript(id)
        ]).then(([auditRes, transcriptRes]) => {
            let transcriptLoaded = false;
            
            if (transcriptRes.data) {
                let parsedCourses = (transcriptRes.data as any).raw_data || [];
                if (!Array.isArray(parsedCourses)) {
                    if (parsedCourses.courses && Array.isArray(parsedCourses.courses)) {
                        parsedCourses = parsedCourses.courses;
                    } else {
                        parsedCourses = [];
                    }
                }
                setRawCourses(parsedCourses);
                
                // Initialize program/concentration from results
                const prog = (auditRes.data as any)?.meta?.program || "CSE";
                const conc = (auditRes.data as any)?.meta?.concentration || "";
                setSelectedProgram(prog);
                setSelectedConcentration(conc);
                
                transcriptLoaded = true;
            } else {
                setError(String(transcriptRes.error || "Transcript not found"));
            }
            
            if (auditRes.data) {
                setData(auditRes.data);
                setPreviousData(auditRes.data);
            } else {
                setAuditError(String(auditRes.error || "No audit result found. Please correct your courses below."));
                if (transcriptLoaded) {
                    setOpenSections(new Set(["courses"]));
                    setIsEditingData(true);
                }
            }
            
            setLoading(false);
        }).catch(() => {
            setError("Failed to load data");
            setLoading(false);
        });
    }, [id]);

    const handleCourseChange = (index: number, field: string, value: string) => {
        const newCourses = [...rawCourses];
        newCourses[index] = { ...newCourses[index], [field]: value };
        setRawCourses(newCourses);
    };

    const handleRemoveCourse = (index: number) => {
        setRawCourses(rawCourses.filter((_, i) => i !== index));
    };

    const handleAddCourse = () => {
        setRawCourses([...rawCourses, { course_code: "", course_name: "", credits: "3", grade: "", semester: "" }]);
    };

    const handleReaudit = async () => {
        setIsReauditing(true);
        setAuditError("");
        
        // Save
        const upRes = await api.updateTranscriptRawData(id, rawCourses);
        if (!upRes.success) {
            setAuditError(upRes.error || "Failed to save transcript courses");
            setIsReauditing(false);
            return;
        }

        const auditRes = await api.runAudit(
            id, 
            selectedProgram, 
            selectedConcentration || undefined,
            customMappings,
            ignoredCourses
        );
        
        if (auditRes.data) {
            setPreviousData(data); // Capture old data immediately
            setData(auditRes.data);
            setIsEditingData(false);
            setAuditError("");
        } else {
            setAuditError(String(auditRes.error || "Failed to re-audit. Fix courses and try again."));
        }
        setIsReauditing(false);
    };

    const handleGenerateAiPlan = async () => {
        setAiPlanLoading(true);
        setAiPlanError("");

        const extractCourseLevel = (courseCode: string): number => {
            const matched = courseCode.match(/(\d{3})/);
            return matched ? Number(matched[1]) : 999;
        };

        const extractCourseCodesFromText = (text: string): string[] => {
            const matches = text.match(/[A-Z]{2,4}\d{3}L?/g) || [];
            return matches.map((m) => m.toUpperCase());
        };

        const parseRemainingCreditDeficit = (remainingRequirements: string[]): number | null => {
            const item = remainingRequirements.find((entry) => entry.startsWith("CREDIT_DEFICIT:"));
            if (!item) return null;
            const parsed = Number(item.split(":")[1]);
            return Number.isFinite(parsed) ? parsed : null;
        };

        const completedCourses = rawCourses
            .map((course) => {
                const code = normalizeMcpCode(course?.course_code);
                const grade = normalizeMcpGrade(course?.grade);
                const credits = toMcpCredits(course?.credits);
                return { course_code: code, credits, grade };
            })
            .filter((course): course is { course_code: string; credits: number; grade: string } => Boolean(course.course_code) && Boolean(course.grade));

        const remainingEntries = Object.entries(remaining).flatMap(([category, courses]) => {
            if (!courses || typeof courses !== "object") return [];
            return Object.entries(courses as Record<string, unknown>).map(([code, cr]) => ({
                code: normalizeMcpCode(code),
                credits: toMcpCredits(cr) || 3,
                category,
            }));
        });

        if (remainingEntries.length === 0) {
            setAiPlan({
                FASTEST: {
                    title: "Already Eligible",
                    subtitle: "No immediate next-term courses required.",
                    courses: [],
                    totalCredits: 0,
                    reasoning: ["All current requirements appear satisfied for this profile."],
                    overlapCount: 0,
                    overlapTotal: 0,
                    eligibleAfter: true,
                    remainingRequirementsCount: 0,
                    remainingCreditDeficit: 0,
                },
            });
            setSelectedAiPlan("FASTEST");
            setAiPlanLoading(false);
            return;
        }

        const coreCoursesRequired = remainingEntries
            .filter((entry) => entry.category.toLowerCase().includes("core"))
            .map((entry) => entry.code)
            .filter(Boolean);

        const electivePool = remainingEntries
            .filter((entry) => entry.category.toLowerCase().includes("elective"))
            .map((entry) => entry.code)
            .filter(Boolean);

        const electiveCreditRequired = remainingEntries
            .filter((entry) => entry.category.toLowerCase().includes("elective"))
            .reduce((sum, entry) => sum + entry.credits, 0);

        const availableCourses = remainingEntries.map((entry) => ({
            course_code: entry.code,
            credits: toMcpCredits(entry.credits),
            category: entry.category.toLowerCase().includes("core")
                ? "CORE"
                : entry.category.toLowerCase().includes("elective")
                    ? "ELECTIVE"
                    : "GENERAL",
        })).filter((entry) => Boolean(entry.course_code));

        const creditsByCode = new Map(availableCourses.map((course) => [course.course_code, course.credits]));

        const limitPlanCourses = (courseCodes: string[]): string[] => {
            const unique = Array.from(new Set(courseCodes.filter(Boolean)));
            const limitedByCount = unique.slice(0, Math.max(1, maxCoursesPerTerm));
            const byCredits: string[] = [];
            let creditsUsed = 0;
            for (const code of limitedByCount) {
                const credits = creditsByCode.get(code) ?? 3;
                if (byCredits.length > 0 && creditsUsed + credits > maxCreditsPerTerm) {
                    continue;
                }
                byCredits.push(code);
                creditsUsed += credits;
            }
            return byCredits;
        };

        const basePayload = {
            student_record: {
                student_id: id,
                courses: completedCourses,
            },
            program_requirements: {
                program_code: selectedProgram,
                total_credits_required: toMcpWhole(totalRequired),
                core_courses_required: Array.from(new Set(coreCoursesRequired)),
                elective_credit_required: toMcpWhole(electiveCreditRequired),
                elective_pool: Array.from(new Set(electivePool)),
            },
            available_courses: availableCourses,
        };

        const [fastestRes, balancedRes, cgpaBaseRes] = await Promise.all([
            api.mcpCallTool<{ structuredContent?: { minimum_course_set?: string[]; rationale?: string } }>(
                "optimize_graduation_path",
                basePayload
            ),
            api.mcpCallTool<{ structuredContent?: { recommended_courses?: string[]; reasoning?: string } }>(
                "plan_path",
                basePayload
            ),
            api.mcpCallTool<{ structuredContent?: { recommended_courses?: string[]; reasoning?: string } }>(
                "plan_path",
                basePayload
            ),
        ]);

        if (!fastestRes.success || !balancedRes.success || !cgpaBaseRes.success) {
            setAiPlanError(
                fastestRes.error || balancedRes.error || cgpaBaseRes.error || "Failed to generate MCP plans."
            );
            setAiPlanLoading(false);
            return;
        }

        const fastestCoursesRaw = fastestRes.data?.structuredContent?.minimum_course_set || [];
        const balancedCoursesRaw = balancedRes.data?.structuredContent?.recommended_courses || [];
        const cgpaBaseCourses = cgpaBaseRes.data?.structuredContent?.recommended_courses || [];

        const cgpaCoursesRaw = [...cgpaBaseCourses].sort((a, b) => {
            const aLabPenalty = a.endsWith("L") ? 1 : 0;
            const bLabPenalty = b.endsWith("L") ? 1 : 0;
            const aLevel = extractCourseLevel(a);
            const bLevel = extractCourseLevel(b);
            return aLabPenalty - bLabPenalty || aLevel - bLevel || a.localeCompare(b);
        });

        const fastestCourses = limitPlanCourses(fastestCoursesRaw);
        const balancedCourses = limitPlanCourses(balancedCoursesRaw);
        const cgpaCourses = limitPlanCourses(cgpaCoursesRaw);

        const roadmapCourseSet = new Set(
            roadmapSteps.flatMap((step: any) =>
                extractCourseCodesFromText(`${String(step?.action || "")} ${String(step?.detail || "")}`)
            )
        );

        const runSimulation = async (courses: string[]) => {
            const hypothetical_courses = courses.map((code) => ({
                course_code: code,
                credits: creditsByCode.get(code) || 3,
                grade: "B",
            }));

            const sim = await api.mcpCallTool<{ structuredContent?: { eligible_after?: boolean; remaining_requirements?: string[] } }>(
                "simulate_changes",
                {
                    student_record: basePayload.student_record,
                    program_requirements: basePayload.program_requirements,
                    hypothetical_courses,
                }
            );

            if (!sim.success || !sim.data?.structuredContent) {
                return {
                    eligibleAfter: null,
                    remainingRequirementsCount: null,
                    remainingCreditDeficit: null,
                };
            }

            const remainingRequirements = Array.isArray(sim.data.structuredContent.remaining_requirements)
                ? sim.data.structuredContent.remaining_requirements
                : [];

            return {
                eligibleAfter: Boolean(sim.data.structuredContent.eligible_after),
                remainingRequirementsCount: remainingRequirements.length,
                remainingCreditDeficit: parseRemainingCreditDeficit(remainingRequirements),
            };
        };

        const [fastestSim, balancedSim, cgpaSim] = await Promise.all([
            runSimulation(fastestCourses),
            runSimulation(balancedCourses),
            runSimulation(cgpaCourses),
        ]);

        const buildPlan = (
            title: string,
            subtitle: string,
            courses: string[],
            reasoning: string[],
            sim: { eligibleAfter: boolean | null; remainingRequirementsCount: number | null; remainingCreditDeficit: number | null }
        ) => {
            const overlapCount = courses.filter((course) => roadmapCourseSet.has(course)).length;
            return {
                title,
                subtitle,
                courses,
                totalCredits: courses.reduce((sum, code) => sum + (creditsByCode.get(code) || 3), 0),
                reasoning,
                overlapCount,
                overlapTotal: courses.length,
                eligibleAfter: sim.eligibleAfter,
                remainingRequirementsCount: sim.remainingRequirementsCount,
                remainingCreditDeficit: sim.remainingCreditDeficit,
            };
        };

        setAiPlan({
            FASTEST: buildPlan(
                "Fastest Graduation",
                "Minimize number of courses while unblocking as many requirements as possible.",
                fastestCourses,
                [
                    "Prioritizes mandatory blockers first (core + capstone dependencies).",
                    "Uses minimum-course optimization to reduce total course count.",
                    "Best for shortest time-to-graduation if workload is manageable.",
                ],
                fastestSim
            ),
            BALANCED: buildPlan(
                "Balanced Workload",
                "Steady progress with moderate credit load for next term.",
                balancedCourses,
                [
                    "Balances core and elective completion in one term.",
                    "Avoids overloading beyond selected max credits/courses.",
                    "Good default path for consistent semester progress.",
                ],
                balancedSim
            ),
            CGPA: buildPlan(
                "CGPA Recovery",
                "Favors lighter/foundational picks first to support GPA stabilization.",
                cgpaCourses,
                [
                    "Prefers non-lab and lower-level courses where available.",
                    "Keeps the term load conservative for better grade focus.",
                    "Best when improving GPA is prioritized over raw speed.",
                ],
                cgpaSim
            ),
        });
        setSelectedAiPlan("BALANCED");
        setAiPlanLoading(false);
        return;
    };

    const renderChangedBadge = (current: any, prev: any, improvedFn?: (c: any, p: any) => boolean) => {
        if (prev === null || current === prev) return null;
        const improved = improvedFn ? improvedFn(current, prev) : false;
        return (
            <span className={`ml-2 text-[10px] px-1.5 py-0.5 rounded font-bold tracking-wider uppercase ${improved ? "bg-success/20 text-success" : "bg-warning/20 text-warning"}`}>
                Was {prev}
            </span>
        );
    };

    const toggle = (s: string) => {
        setOpenSections(prev => {
            const next = new Set(prev);
            next.has(s) ? next.delete(s) : next.add(s);
            return next;
        });
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-bg dark:bg-gray-950 text-primary dark:text-gray-100">
                <nav className="flex items-center justify-between px-8 py-4 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-border dark:border-gray-800 sticky top-0 z-50">
                    <Link href="/dashboard" className="flex items-center gap-2">
                        <Star className="w-6 h-6 text-accent fill-accent" />
                        <span className="text-lg font-semibold text-primary dark:text-gray-100">GradeTrace</span>
                    </Link>
                    <div className="flex items-center gap-4">
                        <ThemeToggle />
                    </div>
                </nav>
                <div className="max-w-4xl mx-auto px-6 py-8">
                    <Skeleton className="h-4 w-32 mb-6" />
                    <Skeleton className="h-32 w-full rounded-2xl mb-8" />
                    {[1, 2, 3, 4].map(i => (
                        <Skeleton key={i} className="h-16 w-full rounded-xl mb-4" />
                    ))}
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-bg dark:bg-gray-950 text-primary dark:text-gray-100">
                <p className="text-muted dark:text-gray-400">{error}</p>
                <Link href="/upload" className="text-accent mt-4">Upload a transcript →</Link>
            </div>
        );
    }

    const l1 = data?.level_1 || {};
    const l2 = data?.level_2 || {};
    const l3 = data?.level_3 || {};
    const roadmap = data?.roadmap || {};

    const cgpa = typeof l2.cgpa === "number" ? l2.cgpa : 0;
    const creditsEarned = l1.credits_earned ?? 0;
    const creditsAttempted = l1.credits_attempted ?? 0;
    const totalRequired = l3.total_credits_required ?? 124;
    const standing = l2.standing ?? "NORMAL";
    const eligible = l3.eligible ?? false;
    const reasons = Array.isArray(l3.reasons) ? l3.reasons : [];
    const remaining = l3.remaining || {};
    const prereqViolations = Array.isArray(l3.prereq_violations) ? l3.prereq_violations : [];
    const roadmapSteps = Array.isArray(roadmap.steps) ? roadmap.steps : [];
    const estimatedSemesters = roadmap.estimated_semesters ?? 0;

    const selectedPlan = aiPlan?.[selectedAiPlan] ?? null;
    const selectedPlanStatusText = !selectedPlan
        ? ""
        : selectedPlan.eligibleAfter === null
            ? "Simulation unavailable"
            : selectedPlan.eligibleAfter
                ? "Eligible after this plan"
                : "Not eligible after this term";
    const selectedPlanStatusTone = !selectedPlan || selectedPlan.eligibleAfter === null
        ? "text-muted dark:text-gray-400"
        : selectedPlan.eligibleAfter
            ? "text-success"
            : "text-warning";
    const selectedPlanRequirementsText = !selectedPlan || selectedPlan.remainingRequirementsCount === null
        ? "Unknown"
        : selectedPlan.remainingRequirementsCount === 0
            ? "All cleared"
            : `${selectedPlan.remainingRequirementsCount} still open`;
    const selectedPlanCreditText = !selectedPlan || selectedPlan.remainingCreditDeficit === null
        ? "Unknown"
        : selectedPlan.remainingCreditDeficit === 0
            ? "No credit gap"
            : `${selectedPlan.remainingCreditDeficit} credits still needed`;
    const selectedPlanProgressText = !selectedPlan
        ? ""
        : selectedPlan.overlapTotal > 0
            ? `${selectedPlan.overlapCount} of ${selectedPlan.overlapTotal} roadmap items targeted`
            : `${selectedPlan.courses.length} course${selectedPlan.courses.length === 1 ? "" : "s"} planned`;
    const selectedPlanTermSummary = selectedPlan
        ? `This next-term plan adds ${selectedPlan.totalCredits} planned credits and targets ${selectedPlan.overlapCount} roadmap item${selectedPlan.overlapCount === 1 ? "" : "s"}.`
        : "";

    const SectionHeader = ({ id: sId, icon: Icon, title, badge }: { id: string; icon: any; title: string; badge?: any }) => (
        <button onClick={() => toggle(sId)} className="w-full flex items-center justify-between p-5 hover:bg-bg/50 dark:hover:bg-gray-800/50 transition-colors">
            <div className="flex items-center gap-3">
                <Icon className="w-5 h-5 text-accent" />
                <h2 className="text-lg font-semibold text-primary dark:text-gray-100">{title}</h2>
                {badge}
            </div>
            {openSections.has(sId) ? <ChevronUp className="w-5 h-5 text-muted dark:text-gray-400" /> : <ChevronDown className="w-5 h-5 text-muted dark:text-gray-400" />}
        </button>
    );

    return (
        <div className="min-h-screen bg-bg dark:bg-gray-950 text-primary dark:text-gray-100">
            <nav className="flex items-center justify-between px-8 py-4 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-border dark:border-gray-800 sticky top-0 z-50">
                <Link href="/dashboard" className="flex items-center gap-2">
                    <Star className="w-6 h-6 text-accent fill-accent" />
                    <span className="text-lg font-semibold text-primary dark:text-gray-100">GradeTrace</span>
                </Link>
                <div className="flex items-center gap-4">
                    <ThemeToggle />
                </div>
            </nav>

            <div className="max-w-4xl mx-auto px-6 py-8">
                <div className="flex items-center justify-between mb-6 print-hidden">
                    <Link href="/dashboard" className="text-muted dark:text-gray-400 text-sm flex items-center gap-1 hover:text-primary dark:hover:text-gray-100">
                        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
                    </Link>
                    <button onClick={() => window.print()} className="text-muted dark:text-gray-400 text-sm flex items-center gap-1 hover:text-primary dark:hover:text-gray-100 bg-bg dark:bg-gray-900 px-3 py-1.5 rounded-lg border border-border dark:border-gray-800">
                        <Printer className="w-4 h-4" /> Export PDF
                    </button>
                </div>

                {/* Top Summary Banner */}
                {auditError && !data ? (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                        className="rounded-2xl p-6 mb-8 text-white bg-gradient-to-r from-red-600 to-red-500 shadow-md"
                    >
                        <div className="flex items-center gap-3">
                            <AlertTriangle className="w-7 h-7" />
                            <h1 className="text-2xl font-bold">Audit Paused: Issues Found</h1>
                        </div>
                        <p className="mt-3 text-white/90">
                            {auditError}
                        </p>
                        <p className="mt-2 text-sm text-white/80">
                            Please fix any AI typos in the <strong>Completed Courses</strong> list below and hit "Save & Re-run Audit".
                        </p>
                    </motion.div>
                ) : !data ? (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                        className="rounded-2xl p-6 mb-8 text-white bg-gradient-to-r from-gray-700 to-gray-600 shadow-md"
                    >
                        <div className="flex items-center gap-3 mb-2">
                            <AlertTriangle className="w-7 h-7 text-warning" />
                            <h1 className="text-2xl font-bold">Audit Not Generated</h1>
                        </div>
                        <p className="mt-2 text-white/90">
                            We haven't generated an audit for this transcript yet. 
                        </p>
                        <p className="mt-4 text-sm bg-black/20 p-3 rounded-lg border border-white/10">
                            <strong>How to fix:</strong> Click <strong>Edit Courses</strong> below, ensure the Program (BBA/CSE) is correct, and hit <strong>Save & Re-run Audit</strong>.
                        </p>
                    </motion.div>
                ) : (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                        className={`rounded-2xl p-6 mb-8 text-white ${eligible ? "bg-gradient-to-r from-emerald-600 to-emerald-500" : "bg-gradient-to-r from-primary to-primary/80"}`}
                    >
                        <div className="flex items-center gap-3 mb-2">
                            {eligible ? <CheckCircle2 className="w-7 h-7" /> : <AlertTriangle className="w-7 h-7 text-warning" />}
                            <h1 className="text-2xl font-bold">
                                {eligible ? "Eligible for Graduation! 🎓" : "Not Yet Eligible"}
                            </h1>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
                            <div>
                                <p className="text-white/70 text-xs uppercase">CGPA</p>
                                <p className="text-xl font-bold">{cgpa.toFixed(2)}</p>
                            </div>
                            <div>
                                <p className="text-white/70 text-xs uppercase">Credits Earned</p>
                                <p className="text-xl font-bold">{creditsEarned} / {totalRequired}</p>
                            </div>
                            <div>
                                <p className="text-white/70 text-xs uppercase">Standing</p>
                                <p className="text-xl font-bold">{standing}</p>
                            </div>
                            <div>
                                <p className="text-white/70 text-xs uppercase">Issues</p>
                                <p className="text-xl font-bold">{reasons.length}</p>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Level 0 — Completed Courses (Editable) */}
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
                    className="bg-white dark:bg-gray-900 border border-transparent dark:border-gray-800 rounded-xl shadow-sm mb-4 overflow-hidden"
                >
                    <SectionHeader id="courses" icon={Edit2} title="Completed Courses"
                        badge={
                            <span className="text-xs bg-bg dark:bg-gray-800 text-muted dark:text-gray-400 px-2 py-1 rounded-full font-medium">
                                {rawCourses.length} courses
                            </span>
                        }
                    />
                    {openSections.has("courses") && (
                        <div className="px-5 pb-5">
                            <div className="flex justify-between mb-3 items-end">
                                <p className="text-xs text-muted dark:text-gray-400 max-w-md">
                                    If the AI missed or misread a course, you can fix it here and re-run the audit.
                                </p>
                                <button
                                    onClick={() => {
                                        if (isEditingData) {
                                            setIsEditingData(false);
                                            // Optional: reload from server if cancelled, for now we just exit mode
                                        } else {
                                            setIsEditingData(true);
                                        }
                                    }}
                                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                                        isEditingData ? "bg-bg text-muted hover:text-primary" : "bg-accent/10 text-accent hover:bg-accent/20"
                                    }`}
                                >
                                    {isEditingData ? <X className="w-4 h-4" /> : <Edit2 className="w-4 h-4" />}
                                    {isEditingData ? "Cancel" : "Edit Courses"}
                                </button>
                            </div>

                            {isEditingData && (
                                <div className="mb-6 p-4 bg-bg dark:bg-gray-800 rounded-xl border border-border dark:border-gray-700 flex flex-wrap gap-6 items-end">
                                    <div className="flex-1 min-w-[200px]">
                                        <label className="text-[10px] text-muted dark:text-gray-400 uppercase tracking-widest font-bold block mb-2">Program Requirement</label>
                                        <div className="flex bg-white dark:bg-gray-900 rounded-lg p-1 border border-border dark:border-gray-700">
                                            {["CSE", "BBA"].map(p => (
                                                <button
                                                    key={p}
                                                    onClick={() => setSelectedProgram(p)}
                                                    className={`flex-1 py-1.5 px-4 rounded-md text-xs font-bold transition-all ${
                                                        selectedProgram === p 
                                                        ? "bg-primary text-white shadow-sm" 
                                                        : "text-muted hover:text-primary dark:hover:text-gray-300"
                                                    }`}
                                                >
                                                    {p} Audit ({p === "CSE" ? "130cr" : "124cr"})
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    
                                    {selectedProgram === "BBA" && (
                                        <div className="flex-1 min-w-[200px]">
                                            <label className="text-[10px] text-muted dark:text-gray-400 uppercase tracking-widest font-bold block mb-2">BBA Concentration</label>
                                            <select
                                                value={selectedConcentration}
                                                onChange={e => setSelectedConcentration(e.target.value)}
                                                className="w-full bg-white dark:bg-gray-900 border border-border dark:border-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-accent appearance-none cursor-pointer"
                                            >
                                                <option value="">Auto-detect Concentration</option>
                                                {["ACT", "FIN", "MKT", "MGT", "HRM", "MIS", "SCM", "ECO", "INB"].map(c => (
                                                    <option key={c} value={c}>{c}</option>
                                                ))}
                                            </select>
                                        </div>
                                    )}
                                </div>
                            )}

                            {auditError && isEditingData && (
                                <div className="mb-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-lg border border-red-200 dark:border-red-800/30 text-sm flex gap-2">
                                    <AlertTriangle className="w-4 h-4 mt-0.5" />
                                    <span>{auditError}</span>
                                </div>
                            )}

                            <div className="overflow-x-auto border border-border dark:border-gray-800 rounded-lg max-h-80 overflow-y-auto mb-4">
                                <table className="w-full text-sm">
                                    <thead className="bg-bg dark:bg-gray-950 sticky top-0 z-10 shadow-sm">
                                        <tr>
                                            <th className="text-left px-4 py-2.5 text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium">Code</th>
                                            <th className="text-left px-4 py-2.5 text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium min-w-[200px]">Name (Optional)</th>
                                            <th className="text-left px-4 py-2.5 text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium">Cr</th>
                                            <th className="text-left px-4 py-2.5 text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium">Grade</th>
                                            <th className="text-left px-4 py-2.5 text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium">Semester</th>
                                            {isEditingData && <th className="text-left px-4 py-2.5 text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium">Map To (Optional)</th>}
                                            {isEditingData && <th className="text-right px-4 py-2.5"></th>}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {rawCourses.map((c, i) => (
                                            <tr key={i} className="border-t border-border dark:border-gray-800 group hover:bg-bg/50">
                                                <td className="px-4 py-2 text-mono font-medium">
                                                    {isEditingData ? (
                                                        <input value={c.course_code} onChange={e => handleCourseChange(i, 'course_code', e.target.value)} className="w-20 bg-transparent border-b border-dashed focus:border-accent outline-none font-mono uppercase" placeholder="CSE115" />
                                                    ) : c.course_code}
                                                </td>
                                                <td className="px-4 py-2 text-muted">
                                                    {isEditingData ? (
                                                        <input value={c.course_name} onChange={e => handleCourseChange(i, 'course_name', e.target.value)} className="w-full bg-transparent border-b border-dashed focus:border-accent outline-none" placeholder="Programming..." />
                                                    ) : <span className="truncate block max-w-[200px]">{c.course_name || "—"}</span>}
                                                </td>
                                                <td className="px-4 py-2">
                                                    {isEditingData ? (
                                                        <input value={c.credits} onChange={e => handleCourseChange(i, 'credits', e.target.value)} className="w-10 bg-transparent border-b border-dashed focus:border-accent outline-none" type="number" step="0.5" />
                                                    ) : c.credits}
                                                </td>
                                                <td className="px-4 py-2">
                                                    {isEditingData ? (
                                                        <input value={c.grade} onChange={e => handleCourseChange(i, 'grade', e.target.value)} className="w-12 bg-transparent border-b border-dashed focus:border-accent outline-none uppercase" placeholder="A" />
                                                    ) : <span className={`font-medium ${["A", "A-", "B+", "B", "B-"].includes(c.grade) ? "text-success" : ["F", "I"].includes(c.grade) ? "text-danger" : "text-warning"}`}>{c.grade}</span>}
                                                </td>
                                                <td className="px-4 py-2">
                                                    {isEditingData ? (
                                                        <input value={c.semester} onChange={e => handleCourseChange(i, 'semester', e.target.value)} className="w-24 bg-transparent border-b border-dashed focus:border-accent outline-none" placeholder="Fall 2024" />
                                                    ) : c.semester}
                                                </td>
                                                {isEditingData && (
                                                    <td className="px-4 py-2">
                                                        {ignoredCourses.includes(c.course_code) ? (
                                                            <span className="text-xs text-muted block text-center italic">Ignored</span>
                                                        ) : (
                                                            <input 
                                                                value={customMappings[c.course_code] || ""} 
                                                                onChange={e => {
                                                                    const val = e.target.value.toUpperCase();
                                                                    setCustomMappings(prev => {
                                                                        const copy = { ...prev };
                                                                        if (val) copy[c.course_code] = val;
                                                                        else delete copy[c.course_code];
                                                                        return copy;
                                                                    });
                                                                }}
                                                                className="w-24 bg-transparent border-b border-dashed focus:border-accent outline-none font-mono uppercase text-xs" 
                                                                placeholder="e.g. ACT201" 
                                                            />
                                                        )}
                                                    </td>
                                                )}
                                                {isEditingData && (
                                                    <td className="px-4 py-2 text-right">
                                                        <div className="flex justify-end gap-2 items-center">
                                                            <button 
                                                                onClick={() => {
                                                                    setIgnoredCourses(prev => 
                                                                        prev.includes(c.course_code) 
                                                                            ? prev.filter(code => code !== c.course_code) 
                                                                            : [...prev, c.course_code]
                                                                    );
                                                                }} 
                                                                title="Ignore Course"
                                                                className={`p-1 rounded-md transition-colors ${ignoredCourses.includes(c.course_code) ? 'text-warning bg-warning/10' : 'text-muted hover:text-warning'}`}
                                                            >
                                                                <XCircle className="w-4 h-4" />
                                                            </button>
                                                            <button onClick={() => handleRemoveCourse(i)} title="Delete row" className="text-muted hover:text-danger p-1 rounded-md opacity-0 group-hover:opacity-100 transition-opacity">
                                                                <Trash2 className="w-4 h-4" />
                                                            </button>
                                                        </div>
                                                    </td>
                                                )}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            
                            {isEditingData && (
                                <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/50">
                                    <button onClick={handleAddCourse} className="text-accent text-sm font-medium flex items-center gap-1.5 hover:underline">
                                        <PlusCircle className="w-4 h-4" /> Add Row
                                    </button>
                                    <button 
                                        onClick={handleReaudit} 
                                        disabled={isReauditing}
                                        className="bg-primary text-white dark:bg-gray-100 dark:text-gray-950 px-5 py-2 rounded-lg text-sm font-semibold hover:opacity-90 disabled:opacity-50 flex items-center gap-2"
                                    >
                                        {isReauditing ? (
                                            <div className="animate-spin w-4 h-4 border-2 border-current border-t-transparent rounded-full" />
                                        ) : <Save className="w-4 h-4" />}
                                        Save & Re-run Audit
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </motion.div>

                {/* Level 1 — Credits */}
                {data && (
                    <>
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                    className="bg-white dark:bg-gray-900 border border-transparent dark:border-gray-800 rounded-xl shadow-sm mb-4 overflow-hidden"
                >
                    <SectionHeader id="level1" icon={BookOpen} title="Level 1 — Credit Tally" />
                    {openSections.has("level1") && (
                        <div className="px-5 pb-5">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                                <div className="bg-bg dark:bg-gray-800 rounded-lg p-4">
                                    <p className="text-xs text-muted dark:text-gray-400 mb-1">Attempted</p>
                                    <p className="text-xl font-bold">
                                        {creditsAttempted}
                                        {renderChangedBadge(creditsAttempted, previousData?.level_1?.credits_attempted)}
                                    </p>
                                </div>
                                <div className="bg-bg dark:bg-gray-800 rounded-lg p-4">
                                    <p className="text-xs text-muted dark:text-gray-400 mb-1">Earned</p>
                                    <p className="text-xl font-bold text-success">
                                        {creditsEarned}
                                        {renderChangedBadge(creditsEarned, previousData?.level_1?.credits_earned, (c, p) => c > p)}
                                    </p>
                                </div>
                            </div>
                            <div className="mt-2">
                                <div className="flex justify-between text-xs text-muted dark:text-gray-400 mb-1">
                                    <span>Progress</span>
                                    <span>{creditsEarned} / {totalRequired} credits</span>
                                </div>
                                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${Math.min(100, (creditsEarned / totalRequired) * 100)}%` }}
                                        transition={{ duration: 1, ease: "easeOut" }}
                                        className="h-full bg-gradient-to-r from-accent to-accent/70 rounded-full"
                                    />
                                </div>
                            </div>
                        </div>
                    )}
                </motion.div>

                {/* Level 2 — CGPA & Standing */}
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                    className="bg-white dark:bg-gray-900 border border-transparent dark:border-gray-800 rounded-xl shadow-sm mb-4 overflow-hidden"
                >
                    <SectionHeader id="level2" icon={TrendingUp} title="Level 2 — CGPA & Standing"
                        badge={standing !== "NORMAL" && standing !== "UNKNOWN" && (
                            <span className="text-xs bg-warning/10 text-warning px-2 py-1 rounded-full font-medium">{standing}</span>
                        )}
                    />
                    {openSections.has("level2") && (
                        <div className="px-5 pb-5">
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                                <div className="bg-bg dark:bg-gray-800 rounded-lg p-4">
                                    <p className="text-xs text-muted dark:text-gray-400 mb-1">Overall CGPA</p>
                                    <p className={`text-xl font-bold ${cgpa >= 2.0 ? "text-success" : "text-danger"}`}>
                                        {cgpa.toFixed(2)}
                                        {renderChangedBadge(cgpa, previousData?.level_2?.cgpa ? Number(previousData.level_2.cgpa).toFixed(2) : null, (c, p) => Number(c) > Number(p))}
                                    </p>
                                </div>
                                <div className="bg-bg dark:bg-gray-800 rounded-lg p-4">
                                    <p className="text-xs text-muted dark:text-gray-400 mb-1">Quality Points</p>
                                    <p className="text-xl font-bold">
                                        {l2.quality_points ?? "—"}
                                        {renderChangedBadge(l2.quality_points, previousData?.level_2?.quality_points, (c, p) => c > p)}
                                    </p>
                                </div>
                                <div className="bg-bg dark:bg-gray-800 rounded-lg p-4">
                                    <p className="text-xs text-muted dark:text-gray-400 mb-1">GPA Credits</p>
                                    <p className="text-xl font-bold">
                                        {l2.gpa_credits ?? "—"}
                                        {renderChangedBadge(l2.gpa_credits, previousData?.level_2?.gpa_credits)}
                                    </p>
                                </div>
                            </div>
                            {l2.waivers && Object.keys(l2.waivers).length > 0 && (
                                <div className="text-sm bg-bg dark:bg-gray-800 rounded-lg p-4">
                                    <p className="text-muted dark:text-gray-400 mb-2 font-medium">Waivable Courses:</p>
                                    {Object.entries(l2.waivers).map(([code, waived]) => (
                                        <span key={code} className={`inline-flex items-center gap-1.5 mr-4 ${waived ? "text-success dark:text-green-400" : "text-muted dark:text-gray-500"}`}>
                                            {waived ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                                            {code}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </motion.div>

                {/* Level 3 — Graduation Eligibility */}
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
                    className="bg-white dark:bg-gray-900 border border-transparent dark:border-gray-800 rounded-xl shadow-sm mb-4 overflow-hidden"
                >
                    <SectionHeader id="level3" icon={GraduationCap} title="Level 3 — Graduation Audit"
                        badge={
                            <span className={`text-xs px-2 py-1 rounded-full font-medium ${eligible ? "bg-success/10 text-success" : "bg-danger/10 text-danger"}`}>
                                {eligible ? "ELIGIBLE" : "NOT ELIGIBLE"}
                            </span>
                        }
                    />
                    {openSections.has("level3") && (
                        <div className="px-5 pb-5">
                            {reasons.length > 0 && (
                                <div className="mb-4">
                                    <p className="text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium mb-2">Issues</p>
                                    {reasons.map((r: string, i: number) => (
                                        <div key={i} className="flex items-start gap-2 text-sm mb-1.5">
                                            <XCircle className="w-4 h-4 text-danger mt-0.5 shrink-0" />
                                            <span>{r}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {Object.keys(remaining).length > 0 && (
                                <div>
                                    <p className="text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium mb-2">Missing Courses</p>
                                    {Object.entries(remaining).map(([category, courses]: [string, any]) => (
                                        <div key={category} className="mb-3">
                                            <p className="text-sm font-medium text-primary dark:text-gray-100 mb-1">{category}</p>
                                            <div className="flex flex-wrap gap-2">
                                                {Object.entries(courses).map(([code, cr]: [string, any]) => (
                                                    <span key={code} className="text-xs bg-bg dark:bg-gray-800 px-2.5 py-1 rounded-md font-mono">
                                                        {code} <span className="text-muted dark:text-gray-400">({cr}cr)</span>
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {prereqViolations.length > 0 && (
                                <div className="mt-4">
                                    <p className="text-xs text-muted uppercase tracking-wider font-medium mb-2">Prerequisite Violations</p>
                                    {prereqViolations.map((v: any, i: number) => (
                                        <div key={i} className="flex items-start gap-2 text-sm mb-1.5">
                                            <AlertTriangle className="w-4 h-4 text-warning mt-0.5 shrink-0" />
                                            <span><strong>{v.course}</strong> ({v.semester}) — missing: {v.missing?.join(", ")}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {reasons.length === 0 && Object.keys(remaining).length === 0 && prereqViolations.length === 0 && (
                                <div className="flex items-center gap-2 text-success text-sm">
                                    <CheckCircle2 className="w-4 h-4" />
                                    <span>All requirements satisfied!</span>
                                </div>
                            )}

                            <div className="mt-5 pt-4 border-t border-border dark:border-gray-800">
                                <div className="flex items-center justify-between gap-3 mb-3">
                                    <div>
                                        <p className="text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5" /> AI Planner</p>
                                        <p className="text-sm text-muted dark:text-gray-400">Choose a strategy and generate a realistic next-term course plan.</p>
                                    </div>
                                    <button
                                        onClick={handleGenerateAiPlan}
                                        disabled={aiPlanLoading}
                                        className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-accent/10 text-accent hover:bg-accent/20 disabled:opacity-60"
                                    >
                                        {aiPlanLoading ? "Generating..." : "Generate Smart Plans"}
                                    </button>
                                </div>

                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                                    <div className="bg-bg dark:bg-gray-800 rounded-lg border border-border dark:border-gray-700 px-3 py-2">
                                        <label className="text-[10px] text-muted dark:text-gray-400 uppercase tracking-wider font-semibold block mb-1">Max Courses / Term</label>
                                        <select
                                            value={maxCoursesPerTerm}
                                            onChange={(e) => setMaxCoursesPerTerm(Number(e.target.value))}
                                            className="w-full bg-transparent text-sm outline-none"
                                        >
                                            {[3, 4, 5, 6].map((count) => (
                                                <option key={count} value={count} className="text-black">{count} courses</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="bg-bg dark:bg-gray-800 rounded-lg border border-border dark:border-gray-700 px-3 py-2">
                                        <label className="text-[10px] text-muted dark:text-gray-400 uppercase tracking-wider font-semibold block mb-1">Max Credits / Term</label>
                                        <select
                                            value={maxCreditsPerTerm}
                                            onChange={(e) => setMaxCreditsPerTerm(Number(e.target.value))}
                                            className="w-full bg-transparent text-sm outline-none"
                                        >
                                            {[9, 12, 15, 18].map((credits) => (
                                                <option key={credits} value={credits} className="text-black">{credits} credits</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                {aiPlanError && (
                                    <div className="text-sm text-danger bg-danger/10 border border-danger/20 rounded-lg px-3 py-2 mb-3">
                                        {aiPlanError}
                                    </div>
                                )}

                                {aiPlan && (
                                    <>
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mb-3">
                                            {[
                                                { key: "FASTEST", label: "Fastest", icon: <Target className="w-3.5 h-3.5" /> },
                                                { key: "BALANCED", label: "Balanced", icon: <Gauge className="w-3.5 h-3.5" /> },
                                                { key: "CGPA", label: "CGPA Recovery", icon: <TrendingUp className="w-3.5 h-3.5" /> },
                                            ].map((planTab) => (
                                                <button
                                                    key={planTab.key}
                                                    onClick={() => setSelectedAiPlan(planTab.key)}
                                                    className={`text-left rounded-lg border px-3 py-2 transition-colors ${selectedAiPlan === planTab.key
                                                        ? "bg-accent/10 border-accent/30 text-accent"
                                                        : "bg-bg dark:bg-gray-800 border-border dark:border-gray-700 text-muted hover:text-primary"}`}
                                                >
                                                    <span className="text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5">{planTab.icon}{planTab.label}</span>
                                                    <p className="text-[11px] mt-1 opacity-80">{aiPlan[planTab.key]?.totalCredits ?? 0} planned credits</p>
                                                </button>
                                            ))}
                                        </div>

                                        {selectedPlan && (
                                            <div className="bg-bg dark:bg-gray-800 rounded-lg border border-border dark:border-gray-700 p-3">
                                                <div className="flex items-start justify-between gap-3 mb-2">
                                                    <div>
                                                        <p className="text-sm font-semibold text-primary dark:text-gray-100">{selectedPlan.title}</p>
                                                        <p className="text-xs text-muted dark:text-gray-400">{selectedPlan.subtitle}</p>
                                                    </div>
                                                    <span className="text-[11px] px-2 py-1 rounded-full bg-accent/10 text-accent font-semibold">{selectedPlan.totalCredits} credits</span>
                                                </div>

                                                <div className="flex flex-wrap gap-2 mb-3">
                                                    {selectedPlan.courses.length > 0 ? selectedPlan.courses.map((course, index) => (
                                                        <span key={course} className="text-xs bg-white dark:bg-gray-900 border border-border dark:border-gray-700 px-2.5 py-1 rounded-md font-mono">
                                                            {index + 1}. {course}
                                                        </span>
                                                    )) : (
                                                        <span className="text-sm text-muted dark:text-gray-400">No additional courses recommended.</span>
                                                    )}
                                                </div>

                                                <div className="rounded-md border border-accent/30 bg-accent/10 px-2.5 py-2 mb-3">
                                                    <p className="text-[10px] uppercase tracking-wider text-accent font-semibold">Next-term progress</p>
                                                    <p className="text-sm font-semibold text-primary dark:text-gray-100">{selectedPlanTermSummary}</p>
                                                    <p className="text-[11px] mt-1 text-muted dark:text-gray-400">
                                                        This is a semester plan, not a promise that all graduation requirements finish immediately.
                                                    </p>
                                                </div>

                                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-3">
                                                    <div className="rounded-md border border-border dark:border-gray-700 bg-white/60 dark:bg-gray-900 px-2.5 py-2">
                                                        <p className="text-[10px] uppercase tracking-wider text-muted dark:text-gray-400">Plan coverage</p>
                                                        <p className="text-sm font-semibold">{selectedPlanProgressText}</p>
                                                    </div>
                                                    <div className="rounded-md border border-border dark:border-gray-700 bg-white/60 dark:bg-gray-900 px-2.5 py-2">
                                                        <p className="text-[10px] uppercase tracking-wider text-muted dark:text-gray-400">Projected status</p>
                                                        <p className={`text-sm font-semibold ${selectedPlanStatusTone}`}>
                                                            {selectedPlanStatusText}
                                                        </p>
                                                    </div>
                                                    <div className="rounded-md border border-border dark:border-gray-700 bg-white/60 dark:bg-gray-900 px-2.5 py-2">
                                                        <p className="text-[10px] uppercase tracking-wider text-muted dark:text-gray-400">After this term</p>
                                                        <p className="text-sm font-semibold">
                                                            {selectedPlanRequirementsText}
                                                        </p>
                                                    </div>
                                                </div>

                                                <div className="rounded-md border border-border dark:border-gray-700 bg-white/40 dark:bg-gray-900/70 px-2.5 py-2 mb-3">
                                                    <p className="text-[10px] uppercase tracking-wider text-muted dark:text-gray-400">Long-term graduation context</p>
                                                    <p className="text-sm font-semibold text-muted dark:text-gray-300">{selectedPlanCreditText}</p>
                                                    <p className="text-[11px] mt-1 text-muted dark:text-gray-400">
                                                        The number above is the remaining program-wide gap after this semester plan. Future terms are still expected.
                                                    </p>
                                                </div>

                                                <div>
                                                    <p className="text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-semibold mb-1">Why this plan</p>
                                                    {selectedPlan.reasoning.map((line, i) => (
                                                        <p key={`${selectedAiPlan}-reason-${i}`} className="text-xs text-muted dark:text-gray-400 mb-1">- {line}</p>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        </div>
                    )}
                </motion.div>

                {/* Roadmap */}
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
                    className="bg-white dark:bg-gray-900 border border-transparent dark:border-gray-800 rounded-xl shadow-sm mb-4 overflow-hidden"
                >
                    <SectionHeader id="roadmap" icon={MapPin} title="Graduation Roadmap"
                        badge={estimatedSemesters > 0 && (
                            <span className="text-xs bg-accent/10 text-accent px-2 py-1 rounded-full font-medium">
                                ~{estimatedSemesters} semester{estimatedSemesters > 1 ? "s" : ""}
                            </span>
                        )}
                    />
                    {openSections.has("roadmap") && (
                        <div className="px-5 pb-5">
                            {roadmapSteps.length > 0 ? roadmapSteps.map((step: any, i: number) => {
                                const prioColors: Record<string, string> = {
                                    CRITICAL: "bg-danger/10 dark:bg-gray-800 text-danger dark:text-red-400 border-danger/20 dark:border-gray-700",
                                    HIGH: "bg-warning/10 dark:bg-gray-800 text-warning dark:text-yellow-400 border-warning/20 dark:border-gray-700",
                                    MEDIUM: "bg-accent/10 dark:bg-gray-800 text-accent dark:text-accent border-accent/20 dark:border-gray-700",
                                    LOW: "bg-bg dark:bg-gray-800 text-muted dark:text-gray-400 border-border dark:border-gray-700",
                                    RECOMMENDED: "bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-gray-700",
                                    DONE: "bg-success/10 dark:bg-gray-800 text-success dark:text-green-400 border-success/20 dark:border-gray-700",
                                };
                                const color = prioColors[step.priority] || prioColors.MEDIUM;
                                return (
                                    <motion.div
                                        key={i}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: 0.4 + i * 0.08 }}
                                        className={`border rounded-lg p-4 mb-3 ${color}`}
                                    >
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-xs uppercase tracking-wider font-medium">{step.category}</span>
                                            <span className="text-xs font-medium">{step.priority}</span>
                                        </div>
                                        <p className="text-sm font-medium text-primary dark:text-gray-100">{step.action}</p>
                                        {step.detail && <p className="text-xs mt-1 opacity-80">{step.detail}</p>}
                                    </motion.div>
                                );
                            }) : (
                                <p className="text-sm text-muted dark:text-gray-400">No roadmap steps available.</p>
                            )}
                        </div>
                    )}
                </motion.div>
                    </>
                )}
            </div>
        </div>
    );
}

