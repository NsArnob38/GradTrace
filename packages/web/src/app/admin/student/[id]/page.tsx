"use client";

import { useEffect, useState, use } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { api } from "@/lib/api";
import {
    Star, ArrowLeft, GraduationCap, TrendingUp, Clock, CheckCircle2, XCircle,
} from "lucide-react";

/* eslint-disable @typescript-eslint/no-explicit-any */

export default function AdminStudentPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.getStudent(id).then((res) => {
            if (res.data) setData(res.data);
            setLoading(false);
        });
    }, [id]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-bg">
                <div className="animate-spin w-8 h-8 border-2 border-accent border-t-transparent rounded-full" />
            </div>
        );
    }

    if (!data) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-bg">
                <p className="text-muted">Student not found.</p>
            </div>
        );
    }

    const profile = data.profile;
    const history = data.history || [];
    const audit = data.latest_audit;

    return (
        <div className="min-h-screen bg-bg">
            <nav className="flex items-center justify-between px-8 py-4 bg-white border-b border-border">
                <Link href="/admin" className="flex items-center gap-2">
                    <Star className="w-6 h-6 text-accent fill-accent" />
                    <span className="text-lg font-semibold">GradeTrace</span>
                    <span className="text-xs bg-primary text-white px-2 py-0.5 rounded-full ml-2">Admin</span>
                </Link>
            </nav>

            <div className="max-w-4xl mx-auto px-6 py-8">
                <Link href="/admin" className="text-muted text-sm flex items-center gap-1 mb-6 hover:text-primary">
                    <ArrowLeft className="w-4 h-4" /> Back to Students
                </Link>

                {/* Profile Card */}
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-xl shadow-sm p-6 mb-6"
                >
                    <h1 className="text-xl font-bold mb-1">{profile.full_name || "Unnamed Student"}</h1>
                    <p className="text-muted text-sm mb-4">{profile.email}</p>
                    <div className="flex gap-6 text-sm">
                        <div><span className="text-muted">Student ID:</span> <span className="font-medium">{profile.student_id || "—"}</span></div>
                        <div><span className="text-muted">Program:</span> <span className="font-medium">{profile.program || "—"}</span></div>
                        {profile.bba_concentration && (
                            <div><span className="text-muted">Concentration:</span> <span className="font-medium">{profile.bba_concentration}</span></div>
                        )}
                    </div>
                </motion.div>

                {/* Latest Audit Summary */}
                {audit && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                        className="bg-white rounded-xl shadow-sm p-6 mb-6"
                    >
                        <h2 className="font-semibold mb-4 flex items-center gap-2">
                            <GraduationCap className="w-5 h-5 text-accent" /> Latest Audit
                        </h2>
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                            <div className="bg-bg rounded-lg p-3">
                                <p className="text-xs text-muted">CGPA</p>
                                <p className="text-lg font-bold">{audit.level_2?.cgpa?.toFixed(2)}</p>
                            </div>
                            <div className="bg-bg rounded-lg p-3">
                                <p className="text-xs text-muted">Credits</p>
                                <p className="text-lg font-bold">{audit.level_1?.credits_earned}/{audit.level_3?.total_credits_required}</p>
                            </div>
                            <div className="bg-bg rounded-lg p-3">
                                <p className="text-xs text-muted">Standing</p>
                                <p className="text-lg font-bold">{audit.level_2?.standing}</p>
                            </div>
                            <div className="bg-bg rounded-lg p-3">
                                <p className="text-xs text-muted">Eligible</p>
                                <p className="text-lg font-bold flex items-center gap-1">
                                    {audit.level_3?.eligible ? <CheckCircle2 className="w-5 h-5 text-success" /> : <XCircle className="w-5 h-5 text-danger" />}
                                    {audit.level_3?.eligible ? "Yes" : "No"}
                                </p>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Scan History */}
                <h2 className="font-semibold mb-3 flex items-center gap-2">
                    <Clock className="w-5 h-5 text-accent" /> Scan History
                </h2>
                {history.length > 0 ? (
                    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                        {history.map((h: any, i: number) => (
                            <div key={h.id} className="flex items-center justify-between px-5 py-3 border-b border-border last:border-0">
                                <div>
                                    <p className="text-sm font-medium">{h.file_name}</p>
                                    <p className="text-xs text-muted">{new Date(h.scanned_at).toLocaleString()}</p>
                                </div>
                                <div className="flex items-center gap-4 text-sm">
                                    <span>CGPA: {h.summary?.cgpa?.toFixed(2)}</span>
                                    <span className={h.summary?.graduation_eligible ? "text-success" : "text-danger"}>
                                        {h.summary?.graduation_eligible ? "Eligible" : "Not eligible"}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-muted text-sm">No scan history available.</p>
                )}
            </div>
        </div>
    );
}
