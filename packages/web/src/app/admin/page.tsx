"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
    BarChart3,
    ChevronDown,
    ChevronUp,
    FileText,
    LogOut,
    Plus,
    Search,
    Shield,
    Trash2,
    Users,
} from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";
import { api } from "@/lib/api";

type Tab = "overview" | "students" | "audits" | "admins";

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
    latest_audit?: {
        summary?: {
            cgpa?: number;
            earned_credits?: number;
            probation_phase?: string;
            graduation_eligible?: boolean;
        };
        scanned_at?: string;
    } | null;
};

type AdminAudit = {
    id: string;
    email?: string;
    generated_at: string;
    level_1?: { program?: string; credits_earned?: number; total_earned?: number };
    level_2?: { cgpa?: number; credits_earned?: number };
    level_3?: { eligible?: boolean; is_eligible?: boolean };
};

const TABS: Array<{ key: Tab; label: string; icon: typeof BarChart3 }> = [
    { key: "overview", label: "Overview", icon: BarChart3 },
    { key: "students", label: "Students", icon: Users },
    { key: "audits", label: "Audits", icon: FileText },
    { key: "admins", label: "Admin Accounts", icon: Shield },
];

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

    const [searchQuery, setSearchQuery] = useState("");
    const [expandedAudit, setExpandedAudit] = useState<string | null>(null);
    const [newAdminId, setNewAdminId] = useState("");
    const [newAdminPassword, setNewAdminPassword] = useState("");
    const [adminActionError, setAdminActionError] = useState<string | null>(null);

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

    if (!hasAdminToken) {
        return <div className="min-h-screen bg-gray-50 dark:bg-gray-950" />;
    }

    const filteredStudents = students.filter((student) => {
        const search = searchQuery.toLowerCase();
        return [student.email, student.full_name, student.student_id, student.program]
            .filter(Boolean)
            .some((value) => String(value).toLowerCase().includes(search));
    });

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
                        className="max-w-5xl mx-auto"
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
                                <div className="flex items-center justify-between mb-8">
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
