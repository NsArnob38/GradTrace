"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { supabase } from "@/lib/supabase";
import { api } from "@/lib/api";
import {
    Star, Upload, LogOut, GraduationCap, TrendingUp,
    AlertTriangle, CheckCircle2, Clock, FileText, Settings, Trash2, RefreshCw,
} from "lucide-react";
import { useToast } from "@/components/toast";
import { Skeleton } from "@/components/ui/skeleton";

interface HistoryItem {
    id: string;
    file_name: string;
    input_type: string;
    scanned_at: string;
    summary: {
        cgpa: number;
        earned_credits: number;
        probation_phase: string;
        graduation_eligible: boolean;
    };
    transcript_id: string;
}

export default function DashboardPage() {
    const router = useRouter();
    const [user, setUser] = useState<Record<string, unknown> | null>(null);
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [deleting, setDeleting] = useState<string | null>(null);
    const [rerunning, setRerunning] = useState<string | null>(null);
    const { toast } = useToast();

    const loadData = useCallback(async (session: { access_token: string } | null) => {
        if (!session) {
            // Guest mode — still show dashboard, just no user data
            setLoading(false);
            return;
        }

        try {
            const [profileRes, historyRes] = await Promise.all([
                api.getProfile(),
                api.listHistory(),
            ]);
            if (profileRes.data) setUser(profileRes.data as Record<string, unknown>);
            if (historyRes.data) setHistory(historyRes.data as HistoryItem[]);
        } catch {
            // API unreachable — still show dashboard with session info
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        // Listen for auth state changes (handles OAuth callback redirect)
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            (_event, session) => {
                if (session) {
                    loadData(session);
                } else {
                    loadData(null);
                }
            }
        );

        // Also check immediately
        supabase.auth.getSession().then(({ data: { session } }) => {
            loadData(session);
        });

        return () => subscription.unsubscribe();
    }, [loadData]);

    const handleLogout = async () => {
        await supabase.auth.signOut();
        router.push("/");
    };

    const handleDelete = async (e: React.MouseEvent, transcriptId: string) => {
        e.preventDefault();
        e.stopPropagation();
        if (!confirm("Are you sure you want to delete this transcript and its audit report?")) return;

        setDeleting(transcriptId);
        const res = await api.deleteHistory(transcriptId);
        if (res.success) {
            toast("Transcript and audit deleted", "success");
            setHistory(prev => prev.filter(h => h.transcript_id !== transcriptId));
        } else {
            toast(res.error || "Failed to delete transcript", "error");
        }
        setDeleting(null);
    };

    const handleRerun = async (e: React.MouseEvent, transcriptId: string) => {
        e.preventDefault();
        e.stopPropagation();
        setRerunning(transcriptId);

        const prog = (user?.program as string) || "CSE";
        const conc = (user?.concentration as string) || undefined;

        toast(`Re-running audit as ${prog}${conc ? ` / ${conc}` : ""}...`, "info");
        const auditRes = await api.runAudit(transcriptId, prog, conc);

        if (auditRes.success) {
            toast("Audit re-run success! Refreshing...", "success");
            const { data: { session } } = await supabase.auth.getSession();
            loadData(session);
        } else {
            toast(auditRes.error || auditRes.detail || "Failed to re-run audit", "error");
        }
        setRerunning(null);
    };

    const latest = history[0]?.summary;

    if (loading) {
        return (
            <div className="min-h-screen bg-bg">
                <nav className="flex items-center justify-between px-8 py-4 bg-white border-b border-border sticky top-0 z-50">
                    <div className="flex items-center gap-2">
                        <Star className="w-6 h-6 text-accent fill-accent" />
                        <span className="text-lg font-semibold">GradeTrace</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <Skeleton className="w-24 h-4" />
                        <Skeleton className="w-5 h-5 rounded-full" />
                        <Skeleton className="w-5 h-5 rounded-full" />
                    </div>
                </nav>
                <div className="max-w-6xl mx-auto px-6 py-8">
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <Skeleton className="h-8 w-64 mb-2" />
                            <Skeleton className="h-4 w-48" />
                        </div>
                        <Skeleton className="h-10 w-40 rounded-lg" />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-10">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="bg-white rounded-xl p-5 shadow-sm border border-border">
                                <div className="flex items-center gap-2 mb-3">
                                    <Skeleton className="w-5 h-5 rounded-full" />
                                    <Skeleton className="w-24 h-3" />
                                </div>
                                <Skeleton className="h-8 w-16" />
                            </div>
                        ))}
                    </div>
                    <Skeleton className="h-6 w-32 mb-4" />
                    <div className="bg-white rounded-xl shadow-sm overflow-hidden border border-border">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="px-6 py-4 border-b border-border last:border-0 flex justify-between">
                                <div className="flex gap-4">
                                    <Skeleton className="w-10 h-10 rounded-lg" />
                                    <div>
                                        <Skeleton className="w-48 h-4 mb-2" />
                                        <Skeleton className="w-32 h-3" />
                                    </div>
                                </div>
                                <Skeleton className="w-32 h-5" />
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-bg">
            {/* Top Bar */}
            <nav className="flex items-center justify-between px-8 py-4 bg-white border-b border-border sticky top-0 z-50">
                <div className="flex items-center gap-2">
                    <Star className="w-6 h-6 text-accent fill-accent" />
                    <span className="text-lg font-semibold">GradeTrace</span>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-sm text-muted">{(user?.email as string) || "Guest"}</span>
                    <Link href="/settings" className="text-muted hover:text-primary transition-colors" title="Settings">
                        <Settings className="w-5 h-5" />
                    </Link>
                    <button onClick={handleLogout} className="text-muted hover:text-danger transition-colors" title="Sign out">
                        <LogOut className="w-5 h-5" />
                    </button>
                </div>
            </nav>

            <div className="max-w-6xl mx-auto px-6 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">
                            Welcome{user?.full_name ? `, ${user.full_name}` : ""}
                        </h1>
                        <p className="text-muted text-sm mt-1">
                            {user?.program ? `${user.program} Program` : "Set your program in settings"}
                        </p>
                    </div>
                    <Link
                        href="/upload"
                        className="bg-primary text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-primary/90 transition-all flex items-center gap-2"
                    >
                        <Upload className="w-4 h-4" /> Upload Transcript
                    </Link>
                </div>

                {/* Summary Cards */}
                {latest ? (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-10">
                        {[
                            {
                                icon: TrendingUp,
                                label: "CGPA",
                                value: latest.cgpa?.toFixed(2) || "—",
                                color: (latest.cgpa || 0) >= 2.0 ? "text-success" : "text-danger",
                            },
                            {
                                icon: GraduationCap,
                                label: "Credits Earned",
                                value: latest.earned_credits?.toString() || "—",
                                color: "text-primary",
                            },
                            {
                                icon: latest.probation_phase === "NORMAL" ? CheckCircle2 : AlertTriangle,
                                label: "Standing",
                                value: latest.probation_phase || "—",
                                color: latest.probation_phase === "NORMAL" ? "text-success" : "text-warning",
                            },
                            {
                                icon: latest.graduation_eligible ? CheckCircle2 : Clock,
                                label: "Graduation",
                                value: latest.graduation_eligible ? "Eligible" : "Not Yet",
                                color: latest.graduation_eligible ? "text-success" : "text-warning",
                            },
                        ].map((card, i) => (
                            <motion.div
                                key={card.label}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.1 }}
                                className="bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow"
                            >
                                <div className="flex items-center gap-2 mb-3">
                                    <card.icon className={`w-5 h-5 ${card.color}`} />
                                    <span className="text-xs text-muted uppercase tracking-wider font-medium">{card.label}</span>
                                </div>
                                <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
                            </motion.div>
                        ))}
                    </div>
                ) : (
                    <div className="bg-white rounded-xl p-10 text-center shadow-sm mb-10">
                        <FileText className="w-12 h-12 text-muted mx-auto mb-4" />
                        <h3 className="font-semibold mb-2">No audits yet</h3>
                        <p className="text-muted text-sm mb-4">Upload a transcript to get your first audit report</p>
                        <Link href="/upload" className="text-accent font-medium text-sm hover:underline">
                            Upload now →
                        </Link>
                    </div>
                )}

                {/* Scan History */}
                {history.length > 0 && (
                    <div>
                        <h2 className="text-lg font-semibold mb-4">Audit History</h2>
                        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                            {history.map((item, i) => (
                                <motion.div
                                    key={item.id}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.05 }}
                                    className="flex items-center justify-between px-6 py-4 border-b border-border last:border-0 hover:bg-bg/50 transition-colors"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center">
                                            <FileText className="w-5 h-5 text-accent" />
                                        </div>
                                        <div>
                                            <p className="font-medium text-sm">{item.file_name}</p>
                                            <p className="text-xs text-muted">
                                                {new Date(item.scanned_at).toLocaleDateString("en-US", {
                                                    month: "short", day: "numeric", year: "numeric",
                                                    hour: "2-digit", minute: "2-digit",
                                                })}
                                                <span className="ml-2 px-1.5 py-0.5 bg-bg rounded text-xs uppercase">
                                                    {item.input_type}
                                                </span>
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-6">
                                        <span className="text-sm font-medium">
                                            CGPA: {item.summary.cgpa?.toFixed(2)}
                                        </span>
                                        <div className="flex items-center gap-3">
                                            <Link
                                                href={`/audit/${item.transcript_id}`}
                                                className="text-accent text-sm font-medium hover:underline"
                                            >
                                                View Report →
                                            </Link>
                                            <button
                                                onClick={(e) => handleRerun(e, item.transcript_id)}
                                                disabled={rerunning === item.transcript_id || deleting === item.transcript_id}
                                                className="p-1.5 text-muted hover:text-accent hover:bg-accent/10 rounded-md transition-colors disabled:opacity-50"
                                                title="Re-run Audit"
                                            >
                                                {rerunning === item.transcript_id ? (
                                                    <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                                                ) : (
                                                    <RefreshCw className="w-4 h-4" />
                                                )}
                                            </button>
                                            <button
                                                onClick={(e) => handleDelete(e, item.transcript_id)}
                                                disabled={deleting === item.transcript_id}
                                                className="p-1.5 text-muted hover:text-danger hover:bg-danger/10 rounded-md transition-colors disabled:opacity-50"
                                                title="Delete Audit"
                                            >
                                                {deleting === item.transcript_id ? (
                                                    <div className="w-4 h-4 border-2 border-danger border-t-transparent rounded-full animate-spin" />
                                                ) : (
                                                    <Trash2 className="w-4 h-4" />
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
