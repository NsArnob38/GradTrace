"use client";

import { useEffect, useState, use } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { api } from "@/lib/api";
import {
    Star, ArrowLeft, CheckCircle2, XCircle, AlertTriangle,
    GraduationCap, TrendingUp, BookOpen, MapPin, ChevronDown, ChevronUp, Printer,
} from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { ThemeToggle } from "@/components/theme-toggle";

/* eslint-disable @typescript-eslint/no-explicit-any */

export default function AuditReportPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [openSections, setOpenSections] = useState<Set<string>>(new Set(["level1", "level2", "level3", "roadmap"]));

    useEffect(() => {
        api.getAuditResult(id).then((res) => {
            if (res.data) setData(res.data);
            else setError(res.error || "No audit result found");
            setLoading(false);
        }).catch(() => {
            setError("Failed to load audit result");
            setLoading(false);
        });
    }, [id]);

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

    if (!data || error) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-bg dark:bg-gray-950 text-primary dark:text-gray-100">
                <p className="text-muted dark:text-gray-400">{error || "No audit result found."}</p>
                <Link href="/upload" className="text-accent mt-4">Upload a transcript →</Link>
            </div>
        );
    }

    const l1 = data.level_1 || {};
    const l2 = data.level_2 || {};
    const l3 = data.level_3 || {};
    const roadmap = data.roadmap || {};

    const cgpa = typeof l2.cgpa === "number" ? l2.cgpa : 0;
    const creditsEarned = l1.credits_earned ?? 0;
    const creditsAttempted = l1.credits_attempted ?? 0;
    const totalRequired = l3.total_credits_required ?? 130;
    const standing = l2.standing ?? "UNKNOWN";
    const eligible = l3.eligible ?? false;
    const reasons = l3.reasons ?? [];
    const remaining = l3.remaining ?? {};
    const prereqViolations = l3.prereq_violations ?? [];
    const roadmapSteps = roadmap.steps ?? [];
    const estimatedSemesters = roadmap.estimated_semesters ?? 0;

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

                {/* Level 1 — Credits */}
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                    className="bg-white dark:bg-gray-900 border border-transparent dark:border-gray-800 rounded-xl shadow-sm mb-4 overflow-hidden"
                >
                    <SectionHeader id="level1" icon={BookOpen} title="Level 1 — Credit Tally" />
                    {openSections.has("level1") && (
                        <div className="px-5 pb-5">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                                <div className="bg-bg dark:bg-gray-800 rounded-lg p-4">
                                    <p className="text-xs text-muted dark:text-gray-400 mb-1">Attempted</p>
                                    <p className="text-xl font-bold">{creditsAttempted}</p>
                                </div>
                                <div className="bg-bg dark:bg-gray-800 rounded-lg p-4">
                                    <p className="text-xs text-muted dark:text-gray-400 mb-1">Earned</p>
                                    <p className="text-xl font-bold text-success">{creditsEarned}</p>
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
                                    <p className={`text-xl font-bold ${cgpa >= 2.0 ? "text-success" : "text-danger"}`}>{cgpa.toFixed(2)}</p>
                                </div>
                                <div className="bg-bg dark:bg-gray-800 rounded-lg p-4">
                                    <p className="text-xs text-muted dark:text-gray-400 mb-1">Quality Points</p>
                                    <p className="text-xl font-bold">{l2.quality_points ?? "—"}</p>
                                </div>
                                <div className="bg-bg dark:bg-gray-800 rounded-lg p-4">
                                    <p className="text-xs text-muted dark:text-gray-400 mb-1">GPA Credits</p>
                                    <p className="text-xl font-bold">{l2.gpa_credits ?? "—"}</p>
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
            </div>
        </div>
    );
}

