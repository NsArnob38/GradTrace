"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Users, FileText, BarChart3, Shield, LogOut, Search, Plus, Trash2, ChevronDown, ChevronUp } from "lucide-react";
import { motion } from "framer-motion";
import { ThemeToggle } from "@/components/theme-toggle";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Tab = "overview" | "students" | "audits" | "admins";

export default function AdminDashboard() {
    const router = useRouter();
    const [token, setToken] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<Tab>("overview");
    const [isLoading, setIsLoading] = useState(true);

    // Data states
    const [stats, setStats] = useState<any>(null);
    const [students, setStudents] = useState<any[]>([]);
    const [audits, setAudits] = useState<any[]>([]);
    const [admins, setAdmins] = useState<string[]>([]);

    // UI states
    const [searchQuery, setSearchQuery] = useState("");
    const [expandedAudit, setExpandedAudit] = useState<string | null>(null);
    const [newAdminId, setNewAdminId] = useState("");
    const [newAdminPassword, setNewAdminPassword] = useState("");

    useEffect(() => {
        const storedToken = localStorage.getItem("admin_token");
        if (!storedToken) {
            router.replace("/admin/login");
            return;
        }
        setToken(storedToken);
    }, [router]);

    useEffect(() => {
        fetchData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab]);

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const currentToken = localStorage.getItem("admin_token");
            if (!currentToken) {
                router.replace("/admin/login");
                return;
            }
            const headers = { Authorization: `Bearer ${currentToken}` };

            if (activeTab === "overview") {
                const res = await fetch(`${API_URL}/admin/stats`, { headers });
                if (res.ok) setStats(await res.json());
            } else if (activeTab === "students") {
                const res = await fetch(`${API_URL}/admin/students`, { headers });
                if (res.ok) setStudents(await res.json());
            } else if (activeTab === "audits") {
                const res = await fetch(`${API_URL}/admin/audits`, { headers });
                if (res.ok) setAudits(await res.json());
            } else if (activeTab === "admins") {
                const res = await fetch(`${API_URL}/admin/admins`, { headers });
                if (res.ok) setAdmins(await res.json());
            }
        } catch (error) {
            console.error("Failed to fetch data:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("admin_token");
        router.replace("/admin/login");
    };

    const handleAddAdmin = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await fetch(`${API_URL}/admin/admins`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ admin_id: newAdminId, password: newAdminPassword })
            });
            if (res.ok) {
                setNewAdminId("");
                setNewAdminPassword("");
                fetchData();
            } else {
                alert("Failed to add admin. ID may already exist.");
            }
        } catch (error) {
            console.error(error);
        }
    };

    const handleRemoveAdmin = async (aid: string) => {
        if (!confirm(`Are you sure you want to remove admin '${aid}'?`)) return;
        try {
            const res = await fetch(`${API_URL}/admin/admins/${aid}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                fetchData();
            }
        } catch (error) {
            console.error(error);
        }
    };

    if (!token) return <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center"><div className="animate-spin w-8 h-8 border-2 border-neutral-900 dark:border-gray-100 border-t-transparent rounded-full" /></div>;

    const SidebarItem = ({ icon: Icon, label, tab }: any) => (
        <button
            onClick={() => setActiveTab(tab)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium ${activeTab === tab
                ? "bg-neutral-900 dark:bg-gray-100 text-white dark:text-gray-900 shadow-md"
                : "text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-neutral-900 dark:hover:text-gray-100"
                }`}
        >
            <Icon className="w-5 h-5" />
            {label}
        </button>
    );

    const filteredStudents = students.filter(s =>
        s.email?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex text-neutral-900 dark:text-gray-100">
            {/* Sidebar */}
            <aside className="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col p-6 sticky top-0 h-screen">
                <div className="flex items-center justify-between mb-10 px-2">
                    <div className="flex items-center gap-2">
                        <Shield className="w-8 h-8 text-neutral-900 dark:text-gray-100" />
                        <span className="text-xl font-bold tracking-tight text-neutral-900 dark:text-gray-100">Admin</span>
                    </div>
                </div>

                <nav className="flex-1 space-y-2">
                    <SidebarItem icon={BarChart3} label="Overview" tab="overview" />
                    <SidebarItem icon={Users} label="Students" tab="students" />
                    <SidebarItem icon={FileText} label="Audits" tab="audits" />
                    <SidebarItem icon={Shield} label="Admin Accounts" tab="admins" />
                </nav>

                <button
                    onClick={handleLogout}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all font-medium mt-auto"
                >
                    <LogOut className="w-5 h-5" />
                    Sign Out
                </button>
            </aside>

            {/* Main Content */}
            <main className="flex-1 p-10 max-h-screen overflow-y-auto relative">
                <div className="absolute top-8 right-10">
                    <ThemeToggle />
                </div>
                {isLoading ? (
                    <div className="flex h-full items-center justify-center">
                        <div className="animate-spin w-8 h-8 border-2 border-neutral-900 dark:border-gray-100 border-t-transparent rounded-full" />
                    </div>
                ) : (
                    <motion.div
                        key={activeTab}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        className="max-w-5xl mx-auto"
                    >
                        {/* OVERVIEW */}
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

                        {/* STUDENTS */}
                        {activeTab === "students" && (
                            <div className="space-y-6">
                                <div className="flex items-center justify-between mb-8">
                                    <h1 className="text-3xl font-bold text-neutral-900 dark:text-gray-100">Registered Students</h1>
                                    <div className="relative">
                                        <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500" />
                                        <input
                                            type="text"
                                            placeholder="Search by email..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 rounded-xl focus:ring-2 focus:ring-neutral-900 dark:focus:ring-gray-100 outline-none w-64 text-sm text-neutral-900 dark:text-gray-100"
                                        />
                                    </div>
                                </div>

                                <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 overflow-hidden">
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400">
                                                <th className="px-6 py-4">Student Email</th>
                                                <th className="px-6 py-4">Joined Date</th>
                                                <th className="px-6 py-4 text-center">Total Audits</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                            {filteredStudents.map((s) => (
                                                <tr key={s.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                                    <td className="px-6 py-4 font-medium text-neutral-900 dark:text-gray-100">{s.email}</td>
                                                    <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{new Date(s.created_at).toLocaleDateString()}</td>
                                                    <td className="px-6 py-4 text-center">
                                                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-neutral-100 dark:bg-gray-800 text-sm font-semibold text-neutral-700 dark:text-gray-300">
                                                            {s.total_audits}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                            {filteredStudents.length === 0 && (
                                                <tr>
                                                    <td colSpan={3} className="px-6 py-8 text-center text-gray-400 dark:text-gray-500">No students found.</td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {/* AUDITS */}
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
                                            {audits.map((a) => {
                                                const cgpa = a.level_2?.cgpa ?? "—";
                                                const credits = a.level_2?.credits_earned ?? a.level_1?.total_earned ?? "—";
                                                const program = a.level_1?.program ?? "—";
                                                const isEligible = a.level_3?.is_eligible ?? false;

                                                return (
                                                    <tr
                                                        key={a.id}
                                                        className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer group"
                                                        onClick={() => setExpandedAudit(expandedAudit === a.id ? null : a.id)}
                                                    >
                                                        <td className="px-6 py-4 text-sm font-medium text-neutral-900 dark:text-gray-100">
                                                            <div className="flex items-center gap-2">
                                                                {a.email}
                                                                {expandedAudit === a.id ?
                                                                    <ChevronUp className="w-4 h-4 text-gray-400 dark:text-gray-500" /> :
                                                                    <ChevronDown className="w-4 h-4 text-gray-400 dark:text-gray-500 group-hover:text-gray-600 dark:group-hover:text-gray-300" />
                                                                }
                                                            </div>
                                                        </td>
                                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{program}</td>
                                                        <td className="px-6 py-4 text-sm font-semibold text-neutral-900 dark:text-gray-100">{typeof cgpa === "number" ? cgpa.toFixed(2) : cgpa}</td>
                                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{credits}</td>
                                                        <td className="px-6 py-4">
                                                            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${isEligible
                                                                ? "bg-green-100 text-green-700"
                                                                : "bg-red-100 text-red-700"
                                                                }`}>
                                                                {isEligible ? "Eligible" : "Ineligible"}
                                                            </span>
                                                        </td>
                                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{new Date(a.generated_at).toLocaleDateString()}</td>
                                                    </tr>
                                                )
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

                        {/* ADMINS */}
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
                                            {admins.map((aid) => (
                                                <div key={aid} className="flex items-center justify-between p-4 border border-gray-100 dark:border-gray-800 rounded-xl bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-10 h-10 rounded-full bg-neutral-200 dark:bg-gray-700 flex items-center justify-center text-neutral-500 dark:text-gray-300 font-bold uppercase">
                                                            {aid.charAt(0)}
                                                        </div>
                                                        <span className="font-medium text-neutral-900 dark:text-gray-100">{aid}</span>
                                                    </div>
                                                    <button
                                                        onClick={() => handleRemoveAdmin(aid)}
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
                                                    onChange={(e) => setNewAdminId(e.target.value)}
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
                                                    onChange={(e) => setNewAdminPassword(e.target.value)}
                                                    required
                                                    className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 text-neutral-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-neutral-900 dark:focus:ring-gray-100 outline-none transition-all text-sm"
                                                    placeholder="••••••••"
                                                />
                                            </div>
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
