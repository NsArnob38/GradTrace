"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { supabase } from "@/lib/supabase";
import { api } from "@/lib/api";
import { Star, ArrowLeft, Save, CheckCircle2 } from "lucide-react";

export default function SettingsPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [form, setForm] = useState({
        full_name: "",
        student_id: "",
        program: "CSE",
        concentration: "",
    });

    useEffect(() => {
        supabase.auth.getSession().then(({ data: { session } }) => {
            if (!session) { router.push("/auth/login"); return; }
            api.getProfile().then((res) => {
                if (res.data) {
                    const d = res.data as Record<string, unknown>;
                    setForm({
                        full_name: (d.full_name as string) || "",
                        student_id: (d.student_id as string) || "",
                        program: (d.program as string) || "CSE",
                        concentration: (d.concentration as string) || "",
                    });
                }
                setLoading(false);
            });
        });
    }, [router]);

    const handleSave = async () => {
        setSaving(true);
        setSaved(false);
        const res = await api.updateProfile(form);
        setSaving(false);
        if (res.success) {
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-bg dark:bg-gray-950">
                <div className="animate-spin w-8 h-8 border-2 border-accent border-t-transparent rounded-full" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-bg dark:bg-gray-950 text-primary dark:text-gray-100">
            <nav className="flex items-center justify-between px-8 py-4 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-border dark:border-gray-800 sticky top-0 z-50">
                <Link href="/dashboard" className="flex items-center gap-2">
                    <Star className="w-6 h-6 text-accent fill-accent" />
                    <span className="text-lg font-semibold">GradeTrace</span>
                </Link>
            </nav>

            <div className="max-w-2xl mx-auto px-6 py-8">
                <Link href="/dashboard" className="text-muted dark:text-gray-400 text-sm flex items-center gap-1 mb-6 hover:text-primary dark:hover:text-gray-100">
                    <ArrowLeft className="w-4 h-4" /> Back to Dashboard
                </Link>

                <h1 className="text-2xl font-bold mb-2">Settings</h1>
                <p className="text-muted dark:text-gray-400 text-sm mb-8">Update your profile information</p>

                <div className="bg-white dark:bg-gray-900 border border-border dark:border-gray-800 rounded-xl shadow-sm p-6 space-y-5">
                    {/* Full Name */}
                    <div>
                        <label className="text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium block mb-1.5">Full Name</label>
                        <input
                            type="text"
                            value={form.full_name}
                            onChange={e => setForm({ ...form, full_name: e.target.value })}
                            placeholder="Enter your full name"
                            className="w-full border border-border dark:border-gray-800 rounded-lg px-4 py-2.5 text-sm bg-white dark:bg-gray-950 focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-all"
                        />
                    </div>

                    {/* Student ID */}
                    <div>
                        <label className="text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium block mb-1.5">Student ID</label>
                        <input
                            type="text"
                            value={form.student_id}
                            onChange={e => setForm({ ...form, student_id: e.target.value })}
                            placeholder="e.g. 2012345678"
                            className="w-full border border-border dark:border-gray-800 rounded-lg px-4 py-2.5 text-sm bg-white dark:bg-gray-950 focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-all"
                        />
                    </div>

                    {/* Program */}
                    <div>
                        <label className="text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium block mb-1.5">Program</label>
                        <select
                            value={form.program}
                            onChange={e => setForm({ ...form, program: e.target.value, concentration: "" })}
                            className="w-full border border-border dark:border-gray-800 rounded-lg px-4 py-2.5 text-sm bg-white dark:bg-gray-950 focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-all"
                        >
                            <option value="CSE">CSE — Computer Science & Engineering</option>
                            <option value="BBA">BBA — Bachelor of Business Administration</option>
                        </select>
                    </div>

                    {/* Concentration (BBA only) */}
                    {form.program === "BBA" && (
                        <div>
                            <label className="text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium block mb-1.5">Concentration</label>
                            <select
                                value={form.concentration}
                                onChange={e => setForm({ ...form, concentration: e.target.value })}
                                className="w-full border border-border dark:border-gray-800 rounded-lg px-4 py-2.5 text-sm bg-white dark:bg-gray-950 focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-all"
                            >
                                <option value="">Not declared / Auto-detect</option>
                                {["ACT", "FIN", "MKT", "MGT", "HRM", "MIS", "SCM", "ECO", "INB"].map(c => (
                                    <option key={c} value={c}>{c}</option>
                                ))}
                            </select>
                        </div>
                    )}

                    {/* Save Button */}
                    <div className="pt-2">
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="bg-primary dark:bg-gray-100 text-white dark:text-gray-950 px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-primary/90 dark:hover:bg-gray-200 transition-all flex items-center gap-2 disabled:opacity-50"
                        >
                            {saving ? (
                                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                            ) : saved ? (
                                <>
                                    <CheckCircle2 className="w-4 h-4" />
                                    Saved!
                                </>
                            ) : (
                                <>
                                    <Save className="w-4 h-4" />
                                    Save Changes
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
