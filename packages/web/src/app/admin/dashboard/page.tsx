"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Users, FileText, BarChart3, Shield, LogOut, Search, Plus, Trash2, ChevronDown, ChevronUp } from "lucide-react";
import { motion } from "framer-motion";

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
        if (!token) return;
        fetchData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token, activeTab]);

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const headers = { Authorization: `Bearer ${token}` };

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

    if (!token) return <div className="min-h-screen bg-gray-50 flex items-center justify-center"><div className="animate-spin w-8 h-8 border-2 border-neutral-900 border-t-transparent rounded-full" /></div>;

    const SidebarItem = ({ icon: Icon, label, tab }: any) => (
        <button
            onClick={() => setActiveTab(tab)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium ${activeTab === tab
                    ? "bg-neutral-900 text-white shadow-md"
                    : "text-gray-500 hover:bg-gray-100 hover:text-neutral-900"
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
        <div className="min-h-screen bg-gray-50 flex">
            {/* Sidebar */}
            <aside className="w-64 bg-white border-r border-gray-200 flex flex-col p-6 sticky top-0 h-screen">
                <div className="flex items-center gap-2 mb-10 px-2">
                    <Shield className="w-8 h-8 text-neutral-900" />
                    <span className="text-xl font-bold tracking-tight text-neutral-900">Admin Panel</span>
                </div>

                <nav className="flex-1 space-y-2">
                    <SidebarItem icon={BarChart3} label="Overview" tab="overview" />
                    <SidebarItem icon={Users} label="Students" tab="students" />
                    <SidebarItem icon={FileText} label="Audits" tab="audits" />
                    <SidebarItem icon={Shield} label="Admin Accounts" tab="admins" />
                </nav>

                <button
                    onClick={handleLogout}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl text-red-500 hover:bg-red-50 transition-all font-medium mt-auto"
                >
                    <LogOut className="w-5 h-5" />
                    Sign Out
                </button>
            </aside>

            {/* Main Content */}
            <main className="flex-1 p-10 max-h-screen overflow-y-auto">
                {isLoading ? (
                    <div className="flex h-full items-center justify-center">
                        <div className="animate-spin w-8 h-8 border-2 border-neutral-900 border-t-transparent rounded-full" />
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
                                <h1 className="text-3xl font-bold text-neutral-900 mb-8">System Overview</h1>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                                        <p className="text-sm font-medium text-gray-500 mb-1">Total Students</p>
                                        <p className="text-4xl font-bold text-neutral-900">{stats.total_students}</p>
                                    </div>
                                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                                        <p className="text-sm font-medium text-gray-500 mb-1">Total Audits</p>
                                        <p className="text-4xl font-bold text-neutral-900">{stats.total_audits}</p>
                                    </div>
                                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                                        <p className="text-sm font-medium text-gray-500 mb-1">Audits Today</p>
                                        <p className="text-4xl font-bold text-green-600">{stats.audits_today}</p>
                                    </div>
                                </div>

                                <div className="mt-8 bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
                                    <h3 className="text-lg font-bold text-neutral-900 mb-4">Most Recent Audit</h3>
                                    {stats.latest_audit ? (
                                        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                                            <div>
                                                <p className="font-medium text-neutral-900">{stats.latest_audit.email}</p>
                                                <p className="text-sm text-gray-500">{new Date(stats.latest_audit.created_at).toLocaleString()}</p>
                                            </div>
                                            <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full">New</span>
                                        </div>
                                    ) : (
                                        <p className="text-gray-500">No audits run yet.</p>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* STUDENTS */}
                        {activeTab === "students" && (
                            <div className="space-y-6">
                                <div className="flex items-center justify-between mb-8">
                                    <h1 className="text-3xl font-bold text-neutral-900">Registered Students</h1>
                                    <div className="relative">
                                        <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                        <input
                                            type="text"
                                            placeholder="Search by email..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="pl-10 pr-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-neutral-900 outline-none w-64 text-sm"
                                        />
                                    </div>
                                </div>

                                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="bg-gray-50 border-b border-gray-100 text-sm font-medium text-gray-500">
                                                <th className="px-6 py-4">Student Email</th>
                                                <th className="px-6 py-4">Joined Date</th>
                                                <th className="px-6 py-4 text-center">Total Audits</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100">
                                            {filteredStudents.map((s) => (
                                                <tr key={s.id} className="hover:bg-gray-50 transition-colors">
                                                    <td className="px-6 py-4 font-medium text-neutral-900">{s.email}</td>
                                                    <td className="px-6 py-4 text-sm text-gray-500">{new Date(s.created_at).toLocaleDateString()}</td>
                                                    <td className="px-6 py-4 text-center">
                                                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-neutral-100 text-sm font-semibold text-neutral-700">
                                                            {s.total_audits}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                            {filteredStudents.length === 0 && (
                                                <tr>
                                                    <td colSpan={3} className="px-6 py-8 text-center text-gray-400">No students found.</td>
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
                                <h1 className="text-3xl font-bold text-neutral-900 mb-8">Audit History</h1>

                                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="bg-gray-50 border-b border-gray-100 text-sm font-medium text-gray-500">
                                                <th className="px-6 py-4">Student Email</th>
                                                <th className="px-6 py-4">Program</th>
                                                <th className="px-6 py-4">CGPA</th>
                                                <th className="px-6 py-4">Credits</th>
                                                <th className="px-6 py-4">Status</th>
                                                <th className="px-6 py-4">Date</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100">
                                            {audits.map((a) => (
                                                <tr
                                                    key={a.id}
                                                    className="hover:bg-gray-50 transition-colors cursor-pointer group"
                                                    onClick={() => setExpandedAudit(expandedAudit === a.id ? null : a.id)}
                                                >
                                                    <td className="px-6 py-4 text-sm font-medium text-neutral-900">
                                                        <div className="flex items-center gap-2">
                                                            {a.email}
                                                            {expandedAudit === a.id ?
                                                                <ChevronUp className="w-4 h-4 text-gray-400" /> :
                                                                <ChevronDown className="w-4 h-4 text-gray-400 group-hover:text-gray-600" />
                                                            }
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-gray-500">{a.program}</td>
                                                    <td className="px-6 py-4 text-sm font-semibold text-neutral-900">{typeof a.cgpa === "number" ? a.cgpa.toFixed(2) : a.cgpa}</td>
                                                    <td className="px-6 py-4 text-sm text-gray-500">{a.credits_earned}</td>
                                                    <td className="px-6 py-4">
                                                        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${a.is_eligible
                                                                ? "bg-green-100 text-green-700"
                                                                : "bg-red-100 text-red-700"
                                                            }`}>
                                                            {a.is_eligible ? "Eligible" : "Ineligible"}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-gray-500">{new Date(a.created_at).toLocaleDateString()}</td>
                                                </tr>
                                            ))}
                                            {audits.length === 0 && (
                                                <tr>
                                                    <td colSpan={6} className="px-6 py-8 text-center text-gray-400">No audits found.</td>
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
                                <h1 className="text-3xl font-bold text-neutral-900 mb-8">Admin Accounts</h1>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                                        <h3 className="text-lg font-bold text-neutral-900 mb-6 flex items-center gap-2">
                                            <Shield className="w-5 h-5 text-neutral-900" />
                                            Active Administrators
                                        </h3>
                                        <div className="space-y-3">
                                            {admins.map((aid) => (
                                                <div key={aid} className="flex items-center justify-between p-4 border border-gray-100 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-10 h-10 rounded-full bg-neutral-200 flex items-center justify-center text-neutral-500 font-bold uppercase">
                                                            {aid.charAt(0)}
                                                        </div>
                                                        <span className="font-medium text-neutral-900">{aid}</span>
                                                    </div>
                                                    <button
                                                        onClick={() => handleRemoveAdmin(aid)}
                                                        className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                                                        title="Remove Admin"
                                                    >
                                                        <Trash2 className="w-5 h-5" />
                                                    </button>
                                                </div>
                                            ))}
                                            {admins.length === 0 && <p className="text-gray-500 text-sm">No administrators configured.</p>}
                                        </div>
                                    </div>

                                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 self-start">
                                        <h3 className="text-lg font-bold text-neutral-900 mb-6 flex items-center gap-2">
                                            <Plus className="w-5 h-5 text-green-500" />
                                            Add New Admin
                                        </h3>
                                        <form onSubmit={handleAddAdmin} className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">Admin ID</label>
                                                <input
                                                    type="text"
                                                    value={newAdminId}
                                                    onChange={(e) => setNewAdminId(e.target.value)}
                                                    required
                                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-neutral-900 outline-none transition-all text-sm"
                                                    placeholder="e.g. admin_jdoe"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                                                <input
                                                    type="password"
                                                    value={newAdminPassword}
                                                    onChange={(e) => setNewAdminPassword(e.target.value)}
                                                    required
                                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-neutral-900 outline-none transition-all text-sm"
                                                    placeholder="••••••••"
                                                />
                                            </div>
                                            <button
                                                type="submit"
                                                className="w-full bg-neutral-900 text-white rounded-lg px-4 py-2.5 text-sm font-medium hover:bg-neutral-800 transition-all mt-6"
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
