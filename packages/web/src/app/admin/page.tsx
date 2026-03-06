"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { api } from "@/lib/api";
import {
    Star, Users, Search, CheckCircle2, XCircle,
    AlertTriangle, GraduationCap, ArrowLeft,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface Student {
    id: string;
    full_name: string;
    student_id: string;
    email: string;
    program: string;
    bba_concentration: string;
    created_at: string;
    latest_audit?: {
        summary: {
            cgpa: number;
            earned_credits: number;
            probation_phase: string;
            graduation_eligible: boolean;
        };
        scanned_at: string;
    } | null;
}

export default function AdminPage() {
    const [students, setStudents] = useState<Student[]>([]);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        api.listStudents().then((res) => {
            if (res.success && res.data) {
                setStudents(res.data as Student[]);
            } else {
                setError(res.error || "Failed to load admin data");
            }
        }).catch((err) => {
            setError(err.message || "Network error. Please try again later.");
        }).finally(() => {
            setLoading(false);
        });
    }, []);

    const filtered = students.filter(s =>
        (s.full_name || "").toLowerCase().includes(search.toLowerCase()) ||
        (s.student_id || "").toLowerCase().includes(search.toLowerCase()) ||
        (s.email || "").toLowerCase().includes(search.toLowerCase())
    );

    const stats = {
        total: students.length,
        eligible: students.filter(s => s.latest_audit?.summary?.graduation_eligible).length,
        probation: students.filter(s => s.latest_audit?.summary?.probation_phase && s.latest_audit.summary.probation_phase !== "NORMAL").length,
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-bg">
                <nav className="flex items-center justify-between px-8 py-4 bg-white border-b border-border">
                    <Link href="/dashboard" className="flex items-center gap-2">
                        <Star className="w-6 h-6 text-accent fill-accent" />
                        <span className="text-lg font-semibold">GradeTrace</span>
                        <span className="text-xs bg-primary text-white px-2 py-0.5 rounded-full ml-2">Admin</span>
                    </Link>
                </nav>
                <div className="max-w-6xl mx-auto px-6 py-8">
                    <Skeleton className="h-4 w-16 mb-6" />
                    <Skeleton className="h-8 w-48 mb-6" />
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
                        {[1, 2, 3].map(i => <Skeleton key={i} className="h-24 w-full rounded-xl" />)}
                    </div>
                    <Skeleton className="h-12 w-full rounded-xl mb-6" />
                    <Skeleton className="h-64 w-full rounded-xl" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-bg">
                <nav className="flex items-center justify-between px-8 py-4 bg-white border-b border-border">
                    <Link href="/dashboard" className="flex items-center gap-2">
                        <Star className="w-6 h-6 text-accent fill-accent" />
                        <span className="text-lg font-semibold">GradeTrace</span>
                        <span className="text-xs bg-primary text-white px-2 py-0.5 rounded-full ml-2">Admin</span>
                    </Link>
                </nav>
                <div className="max-w-6xl mx-auto px-6 py-8">
                    <Link href="/dashboard" className="text-muted text-sm flex items-center gap-1 mb-6 hover:text-primary">
                        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
                    </Link>
                    <div className="bg-white rounded-xl p-10 text-center shadow-sm border border-border mt-10">
                        <AlertTriangle className="w-12 h-12 text-warning mx-auto mb-4" />
                        <h3 className="font-semibold mb-2 text-lg">Admin Access Required</h3>
                        <p className="text-muted mb-6">{error}</p>
                        <Link href="/dashboard" className="bg-primary text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-primary/90 transition-all inline-block">
                            Return Home
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-bg">
            <nav className="flex items-center justify-between px-8 py-4 bg-white border-b border-border">
                <Link href="/dashboard" className="flex items-center gap-2">
                    <Star className="w-6 h-6 text-accent fill-accent" />
                    <span className="text-lg font-semibold">GradeTrace</span>
                    <span className="text-xs bg-primary text-white px-2 py-0.5 rounded-full ml-2">Admin</span>
                </Link>
            </nav>

            <div className="max-w-6xl mx-auto px-6 py-8">
                <Link href="/dashboard" className="text-muted text-sm flex items-center gap-1 mb-6 hover:text-primary">
                    <ArrowLeft className="w-4 h-4" /> Back
                </Link>
                <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
                    {[
                        { icon: Users, label: "Total Students", value: stats.total, color: "text-primary" },
                        { icon: GraduationCap, label: "Graduation Eligible", value: stats.eligible, color: "text-success" },
                        { icon: AlertTriangle, label: "On Probation", value: stats.probation, color: "text-warning" },
                    ].map((s, i) => (
                        <motion.div key={s.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                            className="bg-white rounded-xl p-5 shadow-sm"
                        >
                            <div className="flex items-center gap-2 mb-2">
                                <s.icon className={`w-5 h-5 ${s.color}`} />
                                <span className="text-xs text-muted uppercase tracking-wider">{s.label}</span>
                            </div>
                            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
                        </motion.div>
                    ))}
                </div>

                {/* Search */}
                <div className="relative mb-6">
                    <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
                    <input
                        type="text"
                        placeholder="Search by name, ID, or email..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 bg-white border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
                    />
                </div>

                {/* Student Table */}
                <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                    <table className="w-full text-sm">
                        <thead className="bg-bg">
                            <tr>
                                {["Name", "Student ID", "Program", "CGPA", "Credits", "Standing", "Grad Status"].map(h => (
                                    <th key={h} className="text-left px-4 py-3 text-xs text-muted uppercase tracking-wider font-medium">{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((s, i) => {
                                const a = s.latest_audit?.summary;
                                return (
                                    <motion.tr key={s.id}
                                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }}
                                        className="border-t border-border hover:bg-bg/50 transition-colors cursor-pointer"
                                        onClick={() => window.location.href = `/admin/student/${s.id}`}
                                    >
                                        <td className="px-4 py-3 font-medium">{s.full_name || "—"}</td>
                                        <td className="px-4 py-3 font-mono text-muted">{s.student_id || "—"}</td>
                                        <td className="px-4 py-3">
                                            <span className="bg-bg px-2 py-0.5 rounded text-xs font-medium">
                                                {s.program}{s.bba_concentration ? ` / ${s.bba_concentration}` : ""}
                                            </span>
                                        </td>
                                        <td className={`px-4 py-3 font-medium ${(a?.cgpa || 0) >= 2.0 ? "text-success" : "text-danger"}`}>
                                            {a?.cgpa?.toFixed(2) || "—"}
                                        </td>
                                        <td className="px-4 py-3">{a?.earned_credits || "—"}</td>
                                        <td className="px-4 py-3">
                                            {a?.probation_phase === "NORMAL" ? (
                                                <span className="text-success text-xs">Normal</span>
                                            ) : a?.probation_phase ? (
                                                <span className="text-warning text-xs flex items-center gap-1">
                                                    <AlertTriangle className="w-3 h-3" />{a.probation_phase}
                                                </span>
                                            ) : "—"}
                                        </td>
                                        <td className="px-4 py-3">
                                            {a?.graduation_eligible ? (
                                                <CheckCircle2 className="w-4 h-4 text-success" />
                                            ) : a ? (
                                                <XCircle className="w-4 h-4 text-danger" />
                                            ) : "—"}
                                        </td>
                                    </motion.tr>
                                );
                            })}
                        </tbody>
                    </table>
                    {filtered.length === 0 && (
                        <div className="text-center py-10 text-muted text-sm">No students found</div>
                    )}
                </div>
            </div>
        </div>
    );
}
