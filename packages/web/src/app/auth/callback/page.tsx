"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function AuthCallbackPage() {
    const router = useRouter();

    useEffect(() => {
        // Supabase processes the OAuth tokens from the URL hash automatically
        // We just need to wait for the session to be established
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            async (event, session) => {
                if (event === "SIGNED_IN" && session) {
                    if (session.user && !session.user.email?.endsWith("@northsouth.edu")) {
                        await supabase.auth.signOut();
                        router.replace("/auth/login?error=only_nsu_emails_allowed");
                        return;
                    }
                    router.replace("/dashboard");
                } else if (event === "SIGNED_OUT" || event === "TOKEN_REFRESHED") {
                    // ignore
                }
            }
        );

        // Fallback: check if session already exists
        const checkSession = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            if (session) {
                if (session.user && !session.user.email?.endsWith("@northsouth.edu")) {
                    await supabase.auth.signOut();
                    router.replace("/auth/login?error=only_nsu_emails_allowed");
                    return;
                }
                router.replace("/dashboard");
            }
        };

        // Small delay to let Supabase process the hash
        setTimeout(checkSession, 1000);

        return () => subscription.unsubscribe();
    }, [router]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-bg">
            <div className="text-center">
                <div className="animate-spin w-8 h-8 border-2 border-accent border-t-transparent rounded-full mx-auto mb-4" />
                <p className="text-muted text-sm">Signing you in...</p>
            </div>
        </div>
    );
}
