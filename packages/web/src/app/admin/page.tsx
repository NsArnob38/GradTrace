"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
    BarChart3,
    BookOpen,
    ChevronDown,
    ChevronUp,
    FileText,
    LogOut,
    Plus,
    Save,
    Search,
    Shield,
    Trash2,
    Users,
} from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";
import { api } from "@/lib/api";

type Tab = "overview" | "students" | "audits" | "programs" | "admins";

type AdminStats = {
    total_students: number;
    total_audits: number;
    audits_today: number;
    latest_audit: { email: string; created_at: string } | null;
};

type AdminStudent = {
    id: string;
    email: string;
    created_at: string;
    total_audits: number;
    full_name?: string;
    student_id?: string;
    program?: string;
    bba_concentration?: string;
};

type AdminAudit = {
    id: string;
    email?: string;
    generated_at: string;
    level_1?: { program?: string; credits_earned?: number; total_earned?: number };
    level_2?: { cgpa?: number; credits_earned?: number };
    level_3?: { eligible?: boolean; is_eligible?: boolean };
};

type ProgramCourse = {
    id?: string;
    program_code: string;
    course_code: string;
    course_name: string;
    credits: number;
    category: string;
};

type EditableProgramCourse = {
    course_code: string;
    course_name: string;
    credits: string;
    category: string;
};

const NEW_PROGRAM = "__NEW_PROGRAM__";

const TABS: Array<{ key: Tab; label: string; icon: typeof BarChart3 }> = [
    { key: "overview", label: "Overview", icon: BarChart3 },
    { key: "students", label: "Students", icon: Users },
    { key: "audits", label: "Audits", icon: FileText },
    { key: "programs", label: "Programs", icon: BookOpen },
    { key: "admins", label: "Admin Accounts", icon: Shield },
];

function normalizeCourseCode(value: string): string {
    return value.trim().toUpperCase().replace(/\s+/g, "");
}

function toEditableProgramRows(rows: ProgramCourse[]): EditableProgramCourse[] {
    return rows.map((row) => ({
        course_code: row.course_code,
        course_name: row.course_name,
        credits: String(row.credits),
        category: row.category,
    }));
}

export default function AdminPage() {
    const router = useRouter();
    const [hasAdminToken] = useState(() => {
        if (typeof window === "undefined") return false;
        return Boolean(window.localStorage.getItem("admin_token"));
    });
    const [activeTab, setActiveTab] = useState<Tab>("overview");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [stats, setStats] = useState<AdminStats | null>(null);
    const [students, setStudents] = useState<AdminStudent[]>([]);
    const [audits, setAudits] = useState<AdminAudit[]>([]);
    const [admins, setAdmins] = useState<string[]>([]);
    const [allPrograms, setAllPrograms] = useState<ProgramCourse[]>([]);

    const [searchQuery, setSearchQuery] = useState("");
    const [expandedAudit, setExpandedAudit] = useState<string | null>(null);
    const [newAdminId, setNewAdminId] = useState("");
    const [newAdminPassword, setNewAdminPassword] = useState("");
    const [adminActionError, setAdminActionError] = useState<string | null>(null);

    const [selectedProgramCode, setSelectedProgramCode] = useState<string>(NEW_PROGRAM);
    const [programEditorCode, setProgramEditorCode] = useState("");
    const [programEditorRows, setProgramEditorRows] = useState<EditableProgramCourse[]>([]);
    const [programActionError, setProgramActionError] = useState<string | null>(null);
    const [programActionSuccess, setProgramActionSuccess] = useState<string | null>(null);
    const selectedProgramCodeRef = useRef(selectedProgramCode);

    useEffect(() => {
        selectedProgramCodeRef.current = selectedProgramCode;
    }, [selectedProgramCode]);

    const programCodes = useMemo(
        () => Array.from(new Set(allPrograms.map((row) => row.program_code))).sort(),
        [allPrograms]
    );

    const filteredStudents = students.filter((student) => {
        const search = searchQuery.toLowerCase();
        return [student.email, student.full_name, student.student_id, student.program]
            .filter(Boolean)
            .some((value) => String(value).toLowerCase().includes(search));
    });

    const loadProgramEditor = (rows: ProgramCourse[], programCode: string) => {
        const filtered = rows
            .filter((row) => row.program_code === programCode)
            .sort((a, b) => a.course_code.localeCompare(b.course_code));

        setSelectedProgramCode(programCode);
        setProgramEditorCode(programCode);
        setProgramEditorRows(toEditableProgramRows(filtered));
        setProgramActionError(null);
        setProgramActionSuccess(null);
    };

    const startNewProgramEditor = () => {
        setSelectedProgramCode(NEW_PROGRAM);
        setProgramEditorCode("");
        setProgramEditorRows([]);
        setProgramActionError(null);
        setProgramActionSuccess(null);
    };

    const reloadPrograms = async (preferredProgramCode?: string) => {
        const result = await api.listPrograms();
        if (!result.success) {
            setProgramActionError(result.error || "Failed to load programs.");
            return false;
        }

        const rows = ((result.data as ProgramCourse[] | null) ?? []).map((row) => ({
            ...row,
            program_code: String(row.program_code || "").toUpperCase(),
            course_code: String(row.course_code || "").toUpperCase(),
        }));

        setAllPrograms(rows);

        const nextCode = preferredProgramCode && rows.some((row) => row.program_code === preferredProgramCode)
            ? preferredProgramCode
            : rows[0]?.program_code;

        if (nextCode) {
            loadProgramEditor(rows, nextCode);
        } else {
            startNewProgramEditor();
        }
        return true;
    };

    useEffect(() => {
        if (!hasAdminToken) {
            router.replace("/admin/login");
        }
    }, [hasAdminToken, router]);

    useEffect(() => {
        if (!hasAdminToken) return;

        let cancelled = false;

        const load = async () => {
            setIsLoading(true);
            setError(null);

            const result =
                activeTab === "overview"
                    ? await api.getAdminStats()
                    : activeTab === "students"
                        ? await api.listStudents()
                        : activeTab === "audits"
                            ? await api.listAdminAudits()
                            : activeTab === "programs"
                                ? await api.listPrograms()
                                : await api.listAdmins();

            if (cancelled) return;

            if (!result.success) {
                const message = result.error || "Failed to load admin data.";
                setError(message);
                if (message.toLowerCase().includes("401") || message.toLowerCase().includes("403")) {
                    window.localStorage.removeItem("admin_token");
                    router.replace("/admin/login");
                }
                setIsLoading(false);
                return;
            }

            if (activeTab === "overview") {
                setStats((result.data as AdminStats | null) ?? null);
            } else if (activeTab === "students") {
                setStudents((result.data as AdminStudent[] | null) ?? []);
            } else if (activeTab === "audits") {
                setAudits((result.data as AdminAudit[] | null) ?? []);
            } else if (activeTab === "programs") {
                const rows = ((result.data as ProgramCourse[] | null) ?? []).map((row) => ({
                    ...row,
                    program_code: String(row.program_code || "").toUpperCase(),
                    course_code: String(row.course_code || "").toUpperCase(),
                }));
                setAllPrograms(rows);

                const currentProgramCode = selectedProgramCodeRef.current;
                const nextCode =
                    currentProgramCode !== NEW_PROGRAM && rows.some((row) => row.program_code === currentProgramCode)
                        ? currentProgramCode
                        : rows[0]?.program_code;

                if (nextCode) {
                    loadProgramEditor(rows, nextCode);
                } else {
                    startNewProgramEditor();
                }
            } else {
                setAdmins((result.data as string[] | null) ?? []);
            }

            setIsLoading(false);
        };

        load();
        return () => {
            cancelled = true;
        };
    }, [activeTab, hasAdminToken, router]);

    const handleLogout = () => {
        window.localStorage.removeItem("admin_token");
        router.replace("/admin/login");
    };

    const handleAddAdmin = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setAdminActionError(null);

        const result = await api.addAdmin(newAdminId, newAdminPassword);
        if (!result.success) {
            setAdminActionError(result.error || "Failed to add admin.");
            return;
        }

        setNewAdminId("");
        setNewAdminPassword("");
        const refreshed = await api.listAdmins();
        if (refreshed.success) {
            setAdmins((refreshed.data as string[] | null) ?? []);
        }
    };

    const handleRemoveAdmin = async (adminId: string) => {
        setAdminActionError(null);
        if (!window.confirm(`Remove admin '${adminId}'?`)) return;

        const result = await api.removeAdmin(adminId);
        if (!result.success) {
            setAdminActionError(result.error || "Failed to remove admin.");
            return;
        }

        setAdmins((current) => current.filter((entry) => entry !== adminId));
    };

    const handleProgramRowChange = (
        index: number,
        field: keyof EditableProgramCourse,
        value: string
    ) => {
        setProgramEditorRows((current) =>
            current.map((row, rowIndex) => (rowIndex === index ? { ...row, [field]: value } : row))
        );
        setProgramActionError(null);
        setProgramActionSuccess(null);
    };

    const handleAddProgramRow = () => {
        setProgramEditorRows((current) => [
            ...current,
            { course_code: "", course_name: "", credits: "3", category: "" },
        ]);
        setProgramActionError(null);
        setProgramActionSuccess(null);
    };

    const handleRemoveProgramRow = (index: number) => {
        setProgramEditorRows((current) => current.filter((_, rowIndex) => rowIndex !== index));
        setProgramActionError(null);
        setProgramActionSuccess(null);
    };

    const handleSaveProgram = async () => {
        const normalizedProgramCode = programEditorCode.trim().toUpperCase();
        if (!normalizedProgramCode) {
            setProgramActionError("Program code is required.");
            return;
        }

        if (programEditorRows.length === 0) {
            setProgramActionError("Add at least one course, or delete the program.");
            return;
        }

        const payload: ProgramCourse[] = [];
        for (const row of programEditorRows) {
            const courseCode = normalizeCourseCode(row.course_code);
            const courseName = row.course_name.trim();
            const category = row.category.trim();
            const credits = Number(row.credits);

            if (!courseCode || !courseName || !category || !Number.isFinite(credits)) {
                setProgramActionError("Every course row needs code, name, category, and numeric credits.");
                return;
            }

            payload.push({
                program_code: normalizedProgramCode,
                course_code: courseCode,
                course_name: courseName,
                credits,
                category,
            });
        }

        const result = await api.updatePrograms(payload as unknown as Record<string, unknown>[]);
        if (!result.success) {
            setProgramActionError(result.error || "Failed to save program courses.");
            return;
        }

        const reloaded = await reloadPrograms(normalizedProgramCode);
        if (reloaded) {
            setProgramActionSuccess(`Saved ${payload.length} course${payload.length === 1 ? "" : "s"} for ${normalizedProgramCode}.`);
        }
    };

    const handleDeleteProgram = async () => {
        const normalizedProgramCode = programEditorCode.trim().toUpperCase();
        if (!normalizedProgramCode) return;
        if (!window.confirm(`Delete all courses for ${normalizedProgramCode}?`)) return;

        const result = await api.deleteProgram(normalizedProgramCode);
        if (!result.success) {
            setProgramActionError(result.error || "Failed to delete program.");
            return;
        }

        setProgramActionSuccess(`Deleted program ${normalizedProgramCode}.`);
        await reloadPrograms();
    };

    if (!hasAdminToken) {
        return <div className="min-h-screen bg-gray-50 dark:bg-gray-950" />;
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex text-neutral-900 dark:text-gray-100">
            <aside className="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col p-6 sticky top-0 h-screen">
                <div className="flex items-center justify-between mb-10 px-2">
                    <div className="flex items-center gap-2">
                        <Shield className="w-8 h-8 text-neutral-900 dark:text-gray-100" />
                        <span className="text-xl font-bold tracking-tight text-neutral-900 dark:text-gray-100">Admin</span>
                    </div>
                </div>

                <nav className="flex-1 space-y-2">
                    {TABS.map(({ key, label, icon: Icon }) => (
                        <button
                            key={key}
                            onClick={() => setActiveTab(key)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium ${
                                activeTab === key
                                    ? "bg-neutral-900 dark:bg-gray-100 text-white dark:text-gray-900 shadow-md"
                                    : "text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-neutral-900 dark:hover:text-gray-100"
                            }`}
                        >
                            <Icon className="w-5 h-5" />
                            {label}
                        </button>
                    ))}
                </nav>

                <button
                    onClick={handleLogout}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all font-medium mt-auto"
                >
                    <LogOut className="w-5 h-5" />
                    Sign Out
                </button>
            </aside>

            <main className="flex-1 p-10 max-h-screen overflow-y-auto relative">
                <div className="absolute top-8 right-10">
                    <ThemeToggle />
                </div>

                {isLoading ? (
                    <div className="flex h-full items-center justify-center">
                        <div className="animate-spin w-8 h-8 border-2 border-neutral-900 dark:border-gray-100 border-t-transparent rounded-full" />
                    </div>
                ) : error ? (
                    <div className="max-w-3xl mx-auto bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 p-8 mt-12">
                        <h1 className="text-2xl font-bold mb-3">Admin Access Error</h1>
                        <p className="text-gray-600 dark:text-gray-400">{error}</p>
                    </div>
                ) : (
                    <motion.div
                        key={activeTab}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        className="max-w-6xl mx-auto"
                    >
                        {activeTab === "overview" && stats && (
                            <div className="space-y-6">
                                <h1 className="text-3xl font-bold text-neutral-900 dark:text-gray-100 mb-8">System Overview</h1>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800">
                                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Total Students</p>
                                        <p className="text-4xl font-bold text-neutral-900 dark:text-gray-100">{stats.total_students}</p>
                                    </div>
                                    <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800">
                                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Total Audits</p>
                                        <p className="text-4xl font-bold text-neutral-900 dark:text-gray-100">{stats.total_audits}</p>
                                    </div>
                                    <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800">
                                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Audits Today</p>
                                        <p className="text-4xl font-bold text-green-600 dark:text-green-400">{stats.audits_today}</p>
                                    </div>
                                </div>

                                <div className="mt-8 bg-white dark:bg-gray-900 p-8 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800">
                                    <h3 className="text-lg font-bold text-neutral-900 dark:text-gray-100 mb-4">Most Recent Audit</h3>
                                    {stats.latest_audit ? (
                                        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
                                            <div>
                                                <p className="font-medium text-neutral-900 dark:text-gray-100">{stats.latest_audit.email}</p>
                                                <p className="text-sm text-gray-500 dark:text-gray-400">{new Date(stats.latest_audit.created_at).toLocaleString()}</p>
                                            </div>
                                            <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full">New</span>
                                        </div>
                                    ) : (
                                        <p className="text-gray-500 dark:text-gray-400">No audits run yet.</p>
                                    )}
                                </div>
                            </div>
                        )}

                        {activeTab === "students" && (
                            <div className="space-y-6">
                                <div className="flex items-center justify-between mb-8 gap-4">
                                    <h1 className="text-3xl font-bold text-neutral-900 dark:text-gray-100">Registered Students</h1>
                                    <div className="relative">
                                        <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500" />
                                        <input
                                            type="text"
                                            placeholder="Search by name, email, ID, or program..."
                                            value={searchQuery}
                                            onChange={(event) => setSearchQuery(event.target.value)}
                                            className="pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 rounded-xl focus:ring-2 focus:ring-neutral-900 dark:focus:ring-gray-100 outline-none w-80 text-sm text-neutral-900 dark:text-gray-100"
                                        />
                                    </div>
                                </div>

                                <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 overflow-hidden">
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400">
                                                <th className="px-6 py-4">Name</th>
                                                <th className="px-6 py-4">Program</th>
                                                <th className="px-6 py-4">Email</th>
                                                <th className="px-6 py-4">Joined</th>
                                                <th className="px-6 py-4 text-center">Audits</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                            {filteredStudents.map((student) => (
                                                <tr
                                                    key={student.id}
                                                    className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer"
                                                    onClick={() => router.push(`/admin/student/${student.id}`)}
                                                >
                                                    <td className="px-6 py-4 font-medium text-neutral-900 dark:text-gray-100">
                                                        {student.full_name || student.student_id || "Unnamed Student"}
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                                                        {student.program || "-"}{student.bba_concentration ? ` / ${student.bba_concentration}` : ""}
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{student.email}</td>
                                                    <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{new Date(student.created_at).toLocaleDateString()}</td>
                                                    <td className="px-6 py-4 text-center">
                                                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-neutral-100 dark:bg-gray-800 text-sm font-semibold text-neutral-700 dark:text-gray-300">
                                                            {student.total_audits}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                            {filteredStudents.length === 0 && (
                                                <tr>
                                                    <td colSpan={5} className="px-6 py-8 text-center text-gray-400 dark:text-gray-500">No students found.</td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {activeTab === "audits" && (
                            <div className="space-y-6">
                                <h1 className="text-3xl font-bold text-neutral-900 dark:text-gray-100 mb-8">Audit History</h1>

                                <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 overflow-hidden">
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400">
                                                <th className="px-6 py-4">Student Email</th>
                                                <th className="px-6 py-4">Program</th>
                                                <th className="px-6 py-4">CGPA</th>
                                                <th className="px-6 py-4">Credits</th>
                                                <th className="px-6 py-4">Status</th>
                                                <th className="px-6 py-4">Date</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                            {audits.map((audit) => {
                                                const cgpa = audit.level_2?.cgpa;
                                                const credits = audit.level_2?.credits_earned ?? audit.level_1?.credits_earned ?? audit.level_1?.total_earned;
                                                const program = audit.level_1?.program ?? "-";
                                                const isEligible = Boolean(audit.level_3?.eligible ?? audit.level_3?.is_eligible);

                                                return (
                                                    <tr
                                                        key={audit.id}
                                                        className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer group"
                                                        onClick={() => setExpandedAudit(expandedAudit === audit.id ? null : audit.id)}
                                                    >
                                                        <td className="px-6 py-4 text-sm font-medium text-neutral-900 dark:text-gray-100">
                                                            <div className="flex items-center gap-2">
                                                                {audit.email || "Unknown"}
                                                                {expandedAudit === audit.id ? (
                                                                    <ChevronUp className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                                                                ) : (
                                                                    <ChevronDown className="w-4 h-4 text-gray-400 dark:text-gray-500 group-hover:text-gray-600 dark:group-hover:text-gray-300" />
                                                                )}
                                                            </div>
                                                        </td>
                                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{program}</td>
                                                        <td className="px-6 py-4 text-sm font-semibold text-neutral-900 dark:text-gray-100">
                                                            {typeof cgpa === "number" ? cgpa.toFixed(2) : "-"}
                                                        </td>
                                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{credits ?? "-"}</td>
                                                        <td className="px-6 py-4">
                                                            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide ${
                                                                isEligible
                                                                    ? "bg-green-100/80 text-green-700 dark:bg-emerald-500/10 dark:text-emerald-400"
                                                                    : "bg-red-100/80 text-red-700 dark:bg-rose-500/10 dark:text-rose-400"
                                                            }`}>
                                                                {isEligible ? "Eligible" : "Ineligible"}
                                                            </span>
                                                        </td>
                                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{new Date(audit.generated_at).toLocaleDateString()}</td>
                                                    </tr>
                                                );
                                            })}
                                            {audits.length === 0 && (
                                                <tr>
                                                    <td colSpan={6} className="px-6 py-8 text-center text-gray-400 dark:text-gray-500">No audits found.</td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {activeTab === "programs" && (
                            <div className="space-y-6">
                                <div className="flex items-start justify-between gap-6 mb-4">
                                    <div>
                                        <h1 className="text-3xl font-bold text-neutral-900 dark:text-gray-100">Program Courses</h1>
                                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                            View and manage the course list for each academic program.
                                        </p>
                                    </div>
                                    <div className="flex gap-3">
                                        <button
                                            onClick={startNewProgramEditor}
                                            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-2 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800"
                                        >
                                            <Plus className="w-4 h-4" /> New Program
                                        </button>
                                        {selectedProgramCode !== NEW_PROGRAM && (
                                            <button
                                                onClick={handleDeleteProgram}
                                                className="inline-flex items-center gap-2 rounded-lg border border-red-200 dark:border-red-800 px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30"
                                            >
                                                <Trash2 className="w-4 h-4" /> Delete Program
                                            </button>
                                        )}
                                    </div>
                                </div>

                                <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 p-6 space-y-5">
                                    <div className="grid grid-cols-1 md:grid-cols-[240px,1fr] gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Existing Programs</label>
                                            <select
                                                value={selectedProgramCode}
                                                onChange={(event) => {
                                                    const nextCode = event.target.value;
                                                    if (nextCode === NEW_PROGRAM) {
                                                        startNewProgramEditor();
                                                        return;
                                                    }
                                                    loadProgramEditor(allPrograms, nextCode);
                                                }}
                                                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 px-3 py-2 text-sm"
                                            >
                                                {programCodes.map((code) => (
                                                    <option key={code} value={code}>{code}</option>
                                                ))}
                                                <option value={NEW_PROGRAM}>Create new program...</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Program Code</label>
                                            <input
                                                value={programEditorCode}
                                                onChange={(event) => {
                                                    setProgramEditorCode(event.target.value.toUpperCase());
                                                    setProgramActionError(null);
                                                    setProgramActionSuccess(null);
                                                }}
                                                placeholder="e.g. CSE or BBA"
                                                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 px-3 py-2 text-sm"
                                            />
                                        </div>
                                    </div>

                                    {programActionError && (
                                        <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/30 px-4 py-3 text-sm text-red-600 dark:text-red-400">
                                            {programActionError}
                                        </div>
                                    )}
                                    {programActionSuccess && (
                                        <div className="rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/30 px-4 py-3 text-sm text-green-700 dark:text-green-400">
                                            {programActionSuccess}
                                        </div>
                                    )}

                                    <div className="flex items-center justify-between gap-3">
                                        <p className="text-sm text-gray-500 dark:text-gray-400">
                                            {programEditorRows.length} course{programEditorRows.length === 1 ? "" : "s"} in current editor.
                                        </p>
                                        <div className="flex gap-3">
                                            <button
                                                onClick={handleAddProgramRow}
                                                className="inline-flex items-center gap-2 rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-2 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800"
                                            >
                                                <Plus className="w-4 h-4" /> Add Course
                                            </button>
                                            <button
                                                onClick={handleSaveProgram}
                                                className="inline-flex items-center gap-2 rounded-lg bg-neutral-900 dark:bg-gray-100 px-4 py-2 text-sm font-medium text-white dark:text-gray-900 hover:bg-neutral-800 dark:hover:bg-gray-200"
                                            >
                                                <Save className="w-4 h-4" /> Save Program
                                            </button>
                                        </div>
                                    </div>

                                    <div className="overflow-x-auto rounded-xl border border-gray-100 dark:border-gray-800">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400">
                                                    <th className="px-4 py-3">Course Code</th>
                                                    <th className="px-4 py-3">Course Name</th>
                                                    <th className="px-4 py-3">Credits</th>
                                                    <th className="px-4 py-3">Category</th>
                                                    <th className="px-4 py-3 text-right">Action</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-100 dark:divide-gray-800 bg-white dark:bg-gray-900">
                                                {programEditorRows.map((row, index) => (
                                                    <tr key={`${index}-${row.course_code}-${row.category}`}>
                                                        <td className="px-4 py-3">
                                                            <input
                                                                value={row.course_code}
                                                                onChange={(event) => handleProgramRowChange(index, "course_code", event.target.value.toUpperCase())}
                                                                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 px-3 py-2 text-sm"
                                                            />
                                                        </td>
                                                        <td className="px-4 py-3">
                                                            <input
                                                                value={row.course_name}
                                                                onChange={(event) => handleProgramRowChange(index, "course_name", event.target.value)}
                                                                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 px-3 py-2 text-sm"
                                                            />
                                                        </td>
                                                        <td className="px-4 py-3 w-28">
                                                            <input
                                                                type="number"
                                                                min="0"
                                                                step="1"
                                                                value={row.credits}
                                                                onChange={(event) => handleProgramRowChange(index, "credits", event.target.value)}
                                                                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 px-3 py-2 text-sm"
                                                            />
                                                        </td>
                                                        <td className="px-4 py-3">
                                                            <input
                                                                value={row.category}
                                                                onChange={(event) => handleProgramRowChange(index, "category", event.target.value)}
                                                                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 px-3 py-2 text-sm"
                                                            />
                                                        </td>
                                                        <td className="px-4 py-3 text-right">
                                                            <button
                                                                onClick={() => handleRemoveProgramRow(index)}
                                                                className="inline-flex items-center gap-2 rounded-lg border border-red-200 dark:border-red-800 px-3 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30"
                                                            >
                                                                <Trash2 className="w-4 h-4" /> Remove
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                                {programEditorRows.length === 0 && (
                                                    <tr>
                                                        <td colSpan={5} className="px-6 py-10 text-center text-sm text-gray-400 dark:text-gray-500">
                                                            No courses in this editor yet. Add a course to begin.
                                                        </td>
                                                    </tr>
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === "admins" && (
                            <div className="space-y-6">
                                <h1 className="text-3xl font-bold text-neutral-900 dark:text-gray-100 mb-8">Admin Accounts</h1>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 p-6">
                                        <h3 className="text-lg font-bold text-neutral-900 dark:text-gray-100 mb-6 flex items-center gap-2">
                                            <Shield className="w-5 h-5 text-neutral-900 dark:text-gray-100" />
                                            Active Administrators
                                        </h3>
                                        <div className="space-y-3">
                                            {admins.map((adminId) => (
                                                <div key={adminId} className="flex items-center justify-between p-4 border border-gray-100 dark:border-gray-800 rounded-xl bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-10 h-10 rounded-full bg-neutral-200 dark:bg-gray-700 flex items-center justify-center text-neutral-500 dark:text-gray-300 font-bold uppercase">
                                                            {adminId.charAt(0)}
                                                        </div>
                                                        <span className="font-medium text-neutral-900 dark:text-gray-100">{adminId}</span>
                                                    </div>
                                                    <button
                                                        onClick={() => handleRemoveAdmin(adminId)}
                                                        className="p-2 text-gray-400 dark:text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
                                                        title="Remove Admin"
                                                    >
                                                        <Trash2 className="w-5 h-5" />
                                                    </button>
                                                </div>
                                            ))}
                                            {admins.length === 0 && <p className="text-gray-500 dark:text-gray-400 text-sm">No administrators configured.</p>}
                                        </div>
                                    </div>

                                    <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 p-6 self-start">
                                        <h3 className="text-lg font-bold text-neutral-900 dark:text-gray-100 mb-6 flex items-center gap-2">
                                            <Plus className="w-5 h-5 text-green-500" />
                                            Add New Admin
                                        </h3>
                                        <form onSubmit={handleAddAdmin} className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Admin ID</label>
                                                <input
                                                    type="text"
                                                    value={newAdminId}
                                                    onChange={(event) => setNewAdminId(event.target.value)}
                                                    required
                                                    className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 text-neutral-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-neutral-900 dark:focus:ring-gray-100 outline-none transition-all text-sm"
                                                    placeholder="e.g. admin_jdoe"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
                                                <input
                                                    type="password"
                                                    value={newAdminPassword}
                                                    onChange={(event) => setNewAdminPassword(event.target.value)}
                                                    required
                                                    className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 text-neutral-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-neutral-900 dark:focus:ring-gray-100 outline-none transition-all text-sm"
                                                    placeholder="Enter password"
                                                />
                                            </div>
                                            {adminActionError && <p className="text-sm text-red-600 dark:text-red-400">{adminActionError}</p>}
                                            <button
                                                type="submit"
                                                className="w-full bg-neutral-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-neutral-800 dark:hover:bg-gray-200 transition-all mt-6"
                                            >
                                                Create Account
                                            </button>
                                        </form>
                                    </div>
                                </div>
                            </div>
                        )}
                    </motion.div>
                )}
            </main>
        </div>
    );
}
