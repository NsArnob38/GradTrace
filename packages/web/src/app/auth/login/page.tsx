"use client";

import { supabase } from "@/lib/supabase";
import { Star } from "lucide-react";
import { motion } from "framer-motion";

export default function LoginPage() {
    const handleGoogleLogin = async () => {
        await supabase.auth.signInWithOAuth({
            provider: "google",
            options: {
                redirectTo: `${window.location.origin}/auth/callback`,
                queryParams: { hd: "northsouth.edu" },
            },
        });
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-bg px-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-white rounded-2xl shadow-xl p-10 w-full max-w-md text-center"
            >
                <div className="flex items-center justify-center gap-2 mb-2">
                    <Star className="w-8 h-8 text-accent fill-accent" />
                    <span className="text-2xl font-bold tracking-tight">GradeTrace</span>
                </div>
                <p className="text-muted text-sm mb-10">
                    Sign in with your NSU Google account
                </p>

                <button
                    onClick={handleGoogleLogin}
                    className="w-full flex items-center justify-center gap-3 bg-white border border-border rounded-xl px-6 py-3.5 text-sm font-medium hover:bg-gray-50 hover:shadow-sm transition-all"
                >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                    </svg>
                    Continue with Google
                </button>

                <p className="text-xs text-muted mt-6">
                    Only <span className="font-medium">@northsouth.edu</span> accounts are allowed
                </p>
            </motion.div>
        </div>
    );
}
