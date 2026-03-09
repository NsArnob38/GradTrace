"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Lock } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AdminLogin() {
    const [adminId, setAdminId] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const res = await fetch(`${API_URL}/admin/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ admin_id: adminId, password }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Login failed");
            }

            const { token } = await res.json();
            localStorage.setItem("admin_token", token);
            router.push("/admin/dashboard");
        } catch (err: any) {
            setError(err.message || "Failed to connect to the server.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4 relative">
            <div className="absolute top-6 right-8">
                <ThemeToggle />
            </div>
            <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl p-10 w-full max-w-md text-center border border-transparent dark:border-gray-800">
                <div className="flex items-center justify-center gap-2 mb-2">
                    <Lock className="w-8 h-8 text-neutral-800 dark:text-gray-100" />
                    <span className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-gray-100">Admin Portal</span>
                </div>
                <p className="text-gray-500 dark:text-gray-400 text-sm mb-10">
                    Sign in with your secret admin credentials
                </p>

                {error && (
                    <div className="mb-6 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-sm text-left">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="text-left">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Admin ID
                        </label>
                        <input
                            type="text"
                            value={adminId}
                            onChange={(e) => setAdminId(e.target.value)}
                            required
                            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-neutral-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-neutral-800 dark:focus:ring-gray-100 focus:border-neutral-800 dark:focus:border-gray-100 outline-none transition-all"
                            placeholder="e.g. admin1"
                        />
                    </div>

                    <div className="text-left">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Password
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-neutral-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-neutral-800 dark:focus:ring-gray-100 focus:border-neutral-800 dark:focus:border-gray-100 outline-none transition-all"
                            placeholder="••••••••"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-neutral-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-xl px-6 py-3 text-sm font-medium hover:bg-neutral-800 dark:hover:bg-gray-200 transition-all disabled:opacity-50 mt-6"
                    >
                        {loading ? "Authenticating..." : "Login"}
                    </button>
                </form>
            </div>
        </div>
    );
}
