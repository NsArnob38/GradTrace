"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminDashboardRedirect() {
    const router = useRouter();

    useEffect(() => {
        router.replace("/admin");
    }, [router]);

    return <div className="min-h-screen bg-gray-50 dark:bg-gray-950" />;
}
