"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { api } from "@/lib/api";
import { Star, Upload, FileText, ArrowRight, X, Check, AlertCircle } from "lucide-react";
import { useToast } from "@/components/toast";
import { ThemeToggle } from "@/components/theme-toggle";

interface ParsedRow {
    course_code: string;
    course_name: string;
    credits: string;
    grade: string;
    semester: string;
}

export default function UploadPage() {
    const router = useRouter();
    const fileRef = useRef<HTMLInputElement>(null);
    const [file, setFile] = useState<File | null>(null);
    const [preview, setPreview] = useState<ParsedRow[]>([]);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState("");
    const [dragOver, setDragOver] = useState(false);
    const [program, setProgram] = useState("CSE");
    const [concentration, setConcentration] = useState("");
    const { toast } = useToast();

    const handleFile = useCallback((f: File) => {
        setFile(f);
        setError("");
        
        // If PDF, skip local preview string splitting
        if (f.name.toLowerCase().endsWith(".pdf")) {
            setPreview([{ course_code: "", course_name: "PDF Preview Unavailable (Will process server-side)", credits: "—", grade: "—", semester: "—" }]);
            toast(`Loaded PDF transcript: ${f.name}`, "success");
            return;
        }

        // Parse CSV preview client-side
        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target?.result as string;
            const lines = text.split("\n").filter(l => l.trim());
            const rows: ParsedRow[] = [];
            for (const line of lines) {
                const cols = line.split(",").map(c => c.trim());
                if (cols.length < 5) continue;
                if (cols[0].toLowerCase() === "course_code") continue;
                rows.push({
                    course_code: cols[0], course_name: cols[1],
                    credits: cols[2], grade: cols[3], semester: cols[4],
                });
            }
            setPreview(rows);
            toast(`Loaded ${rows.length} courses from ${f.name}`, "success");
        };
        reader.readAsText(f);
    }, [toast]);

    const handleUploadAndAudit = async () => {
        if (!file) return;
        setUploading(true);
        setError("");

        try {
            const uploadRes = await api.uploadTranscript(file);
            if (!uploadRes.success || !uploadRes.data) {
                const msg = uploadRes.error || "Upload failed";
                setError(msg);
                toast(msg, "error");
                setUploading(false);
                return;
            }
            const transcriptId = (uploadRes.data as { id: string }).id;
            toast("Transcript uploaded — running audit...", "info");

            const auditRes = await api.runAudit(
                transcriptId, program,
                program === "BBA" && concentration ? concentration : undefined,
            );
            if (!auditRes.success) {
                const msg = String(auditRes.error || "Audit failed");
                setError(msg);
                toast(msg, "error");
                setUploading(false);
                return;
            }
            toast("Audit complete! Redirecting to results...", "success");
            router.push(`/audit/${transcriptId}`);
        } catch {
            setError("Something went wrong");
            toast("Network error — is the API server running?", "error");
            setUploading(false);
        }
    };

    return (
        <div className="min-h-screen bg-bg dark:bg-gray-950 text-primary dark:text-gray-100">
            {/* Nav */}
            <nav className="flex items-center justify-between px-8 py-4 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-border dark:border-gray-800 sticky top-0 z-50">
                <Link href="/dashboard" className="flex items-center gap-2">
                    <Star className="w-6 h-6 text-accent fill-accent" />
                    <span className="text-lg font-semibold text-primary dark:text-gray-100">GradeTrace</span>
                </Link>
                <div className="flex items-center gap-4">
                    <ThemeToggle />
                </div>
            </nav>

            <div className="flex items-center justify-center min-h-[80vh] w-full">
                <div className="w-full max-w-4xl mx-auto px-6 py-10">
                    <h1 className="text-2xl font-bold mb-2">Upload Transcript</h1>
                    <p className="text-muted dark:text-gray-400 text-sm mb-8">Upload your NSU transcript CSV or PDF to get a full audit report</p>

                    {/* Program selector */}
                    <div className="flex gap-4 mb-6">
                        <div>
                            <label className="text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium block mb-1.5">Program</label>
                            <select
                                value={program}
                                onChange={e => setProgram(e.target.value)}
                                className="border border-border dark:border-gray-800 rounded-lg px-4 py-2.5 text-sm bg-white dark:bg-gray-900"
                            >
                                <option value="CSE">CSE</option>
                                <option value="BBA">BBA</option>
                            </select>
                        </div>
                        {program === "BBA" && (
                            <div>
                                <label className="text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium block mb-1.5">Concentration</label>
                                <select
                                    value={concentration}
                                    onChange={e => setConcentration(e.target.value)}
                                    className="border border-border dark:border-gray-800 rounded-lg px-4 py-2.5 text-sm bg-white dark:bg-gray-900"
                                >
                                    <option value="">Auto-detect</option>
                                    {["ACT", "FIN", "MKT", "MGT", "HRM", "MIS", "SCM", "ECO", "INB"].map(c => (
                                        <option key={c} value={c}>{c}</option>
                                    ))}
                                </select>
                            </div>
                        )}
                    </div>

                    {/* Drop zone */}
                    {!file ? (
                        <>
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                                onDragLeave={() => setDragOver(false)}
                                onDrop={(e) => {
                                    e.preventDefault(); setDragOver(false);
                                    const f = e.dataTransfer.files[0];
                                    if (f) handleFile(f);
                                }}
                                onClick={() => fileRef.current?.click()}
                                className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${dragOver ? "border-accent bg-accent/5 dark:bg-accent/10" : "border-border dark:border-gray-800 hover:border-accent/50 hover:bg-white dark:hover:bg-gray-900"
                                    }`}
                            >
                                <Upload className="w-10 h-10 text-muted dark:text-gray-500 mx-auto mb-4" />
                                <p className="font-medium mb-1">Drop your transcript CSV or PDF here</p>
                                <p className="text-muted dark:text-gray-400 text-sm">or click to browse files</p>
                                <input
                                    ref={fileRef}
                                    type="file"
                                    accept=".csv,.pdf"
                                    className="hidden"
                                    onChange={(e) => {
                                        const f = e.target.files?.[0];
                                        if (f) handleFile(f);
                                    }}
                                />
                            </motion.div>

                            {/* How it works */}
                            <div className="grid grid-cols-3 gap-4 mt-6">
                                {[
                                    { step: "1", title: "Download CSV", desc: "Export your transcript from the NSU portal" },
                                    { step: "2", title: "Upload Here", desc: "Drag and drop your CSV file" },
                                    { step: "3", title: "Get Your Audit", desc: "Instant analysis of credits, CGPA, and graduation status" },
                                ].map(({ step, title, desc }) => (
                                    <div key={step} className="flex flex-col items-center text-center p-4 bg-white dark:bg-gray-900 rounded-xl border border-border dark:border-gray-800">
                                        <div className="w-8 h-8 rounded-full bg-amber-500 text-white text-sm font-bold flex items-center justify-center mb-3">{step}</div>
                                        <p className="text-sm font-semibold mb-1">{title}</p>
                                        <p className="text-xs text-muted dark:text-gray-400 leading-relaxed">{desc}</p>
                                    </div>
                                ))}
                            </div>
                        </>
                    ) : (
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                            {/* File info */}
                            <div className="flex items-center justify-between bg-white dark:bg-gray-900 border border-border dark:border-gray-800 rounded-xl px-5 py-3 shadow-sm mb-6">
                                <div className="flex items-center gap-3">
                                    <FileText className="w-5 h-5 text-accent" />
                                    <div>
                                        <p className="font-medium text-sm flex items-center gap-2">
                                            {file.name}
                                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider ${file.name.toLowerCase().endsWith('.pdf') ? 'bg-rose-100 text-rose-700 dark:bg-rose-500/20 dark:text-rose-400' : 'bg-green-100 text-green-700 dark:bg-emerald-500/20 dark:text-emerald-400'}`}>
                                                {file.name.toLowerCase().endsWith(".pdf") ? "📄 PDF DETECTED" : "📊 CSV DETECTED"}
                                            </span>
                                        </p>
                                        <p className="text-xs text-muted dark:text-gray-400">{file.name.toLowerCase().endsWith(".pdf") ? "Parsing engine will automatically extract data" : `${preview.length} courses found`}</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => { setFile(null); setPreview([]); }}
                                    className="text-muted dark:text-gray-400 hover:text-danger dark:hover:text-red-400 transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Preview table */}
                            <div className="bg-white dark:bg-gray-900 border border-border dark:border-gray-800 rounded-xl shadow-sm overflow-hidden mb-6">
                                <div className="overflow-x-auto max-h-80 overflow-y-auto">
                                    <table className="w-full text-sm">
                                        <thead className="bg-bg dark:bg-gray-950 sticky top-0">
                                            <tr>
                                                {["Code", "Course Name", "Cr", "Grade", "Semester"].map(h => (
                                                    <th key={h} className="text-left px-4 py-3 text-xs text-muted dark:text-gray-400 uppercase tracking-wider font-medium">{h}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {preview.map((r, i) => (
                                                <tr key={i} className="border-t border-border dark:border-gray-800">
                                                    <td className="px-4 py-2.5 font-mono font-medium">{r.course_code}</td>
                                                    <td className="px-4 py-2.5">{r.course_name}</td>
                                                    <td className="px-4 py-2.5">{r.credits}</td>
                                                    <td className="px-4 py-2.5">
                                                        <span className={`font-medium ${["A", "A-", "B+", "B", "B-"].includes(r.grade) ? "text-success" :
                                                            ["F", "I"].includes(r.grade) ? "text-danger" : "text-warning"
                                                            }`}>{r.grade}</span>
                                                    </td>
                                                    <td className="px-4 py-2.5 text-muted dark:text-gray-400">{r.semester}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Error */}
                            {error && (
                                <div className="flex items-center gap-2 text-danger text-sm bg-danger/5 px-4 py-3 rounded-lg mb-4">
                                    <AlertCircle className="w-4 h-4" /> {error}
                                </div>
                            )}

                            {/* Submit */}
                            <button
                                onClick={handleUploadAndAudit}
                                disabled={uploading}
                                className="w-full bg-primary dark:bg-gray-100 text-white dark:text-gray-950 py-3.5 rounded-xl font-medium hover:bg-primary/90 dark:hover:bg-gray-200 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                {uploading ? (
                                    <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
                                ) : (
                                    <>
                                        <Check className="w-5 h-5" />
                                        Upload & Run Audit
                                        <ArrowRight className="w-4 h-4" />
                                    </>
                                )}
                            </button>
                        </motion.div>
                    )}
                </div>
            </div>
        </div>
    );
}
