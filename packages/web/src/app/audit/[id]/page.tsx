"use client";

import { useEffect, useState, use } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { api } from "@/lib/api";
import {
    Star, ArrowLeft, CheckCircle2, XCircle, AlertTriangle,
    GraduationCap, TrendingUp, BookOpen, MapPin, ChevronDown, ChevronUp, Printer,
    Edit2, Save, X, PlusCircle, Trash2
} from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { ThemeToggle } from "@/components/theme-toggle";

/* eslint-disable @typescript-eslint/no-explicit-any */

export default function AuditReportPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [data, setData] = useState<any>(null);
    const [previousData, setPreviousData] = useState<any>(null);
    const [rawCourses, setRawCourses] = useState<any[]>([]);
    const [isEditingData, setIsEditingData] = useState(false);
    const [isReauditing, setIsReauditing] = useState(false);
    
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [openSections, setOpenSections] = useState<Set<string>>(new Set(["level1", "level2", "level3", "roadmap"]));

    useEffect(() => {
        Promise.all([
            api.getAuditResult(id),
            api.getTranscript(id)
        ]).then(([auditRes, transcriptRes]) => {
            if (auditRes.data) {
                setData(auditRes.data);
                setPreviousData(auditRes.data);
            } else setError(String(auditRes.error || "No audit result found"));
            
            if (transcriptRes.data) {
                setRawCourses((transcriptRes.data as any).raw_data || []);
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
        setError("");
        
        // Save
        const upRes = await api.updateTranscriptRawData(id, rawCourses);
        if (!upRes.success) {
            setError(upRes.error || "Failed to save transcript courses");
            setIsReauditing(false);
            return;
        }

        const isBBA = data?.level_3?.concentration_label !== undefined;
        let program = isBBA ? "BBA" : "CSE";
        if (data?.level_3?.total_credits_required === 124) program = "BBA";
        
        const concentration = isBBA && data.level_3.concentration_label !== "Undeclared" ? data.level_3.concentration_label : undefined;

        const auditRes = await api.runAudit(id, program, concentration);
        
        if (auditRes.data) {
            setPreviousData(data); // Capture old data immediately
            setData(auditRes.data);
            setIsEditingData(false);
        } else {
            setError(String(auditRes.error || "Failed to re-audit. Fix courses and try again."));
        }
        setIsReauditing(false);
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

                            <div className="overflow-x-auto border border-border dark:border-gray-800 rounded-lg max-h-80 overflow-y-auto mb-4">
                                <table className="w-full text-sm">
                                    <thead className="bg-bg dark:bg-gray-950 sticky top-0 z-10 shadow-sm">
                                        <tr>
                                            <th className="text-left px-4 py-2.5 text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium">Code</th>
                                            <th className="text-left px-4 py-2.5 text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium min-w-[200px]">Name (Optional)</th>
                                            <th className="text-left px-4 py-2.5 text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium">Cr</th>
                                            <th className="text-left px-4 py-2.5 text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium">Grade</th>
                                            <th className="text-left px-4 py-2.5 text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium">Semester</th>
                                            {isEditingData && <th className="px-4 py-2.5"></th>}
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
                                                    <td className="px-4 py-2 text-right">
                                                        <button onClick={() => handleRemoveCourse(i)} className="text-muted hover:text-danger p-1 rounded-md opacity-0 group-hover:opacity-100 transition-opacity">
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
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

