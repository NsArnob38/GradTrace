"use client";

import { ReactNode } from "react";
import { ToastProvider } from "./toast";
import { ThemeProvider } from "./theme-provider";

export function Providers({ children }: { children: ReactNode }) {
    return (
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
            <ToastProvider>
                {children}
            </ToastProvider>
        </ThemeProvider>
    );
}
