"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
    id: number;
    message: string;
    type: ToastType;
}

interface ToastContextType {
    toast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType>({ toast: () => { } });

export function useToast() {
    return useContext(ToastContext);
}

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = useCallback((message: string, type: ToastType = "info") => {
        const id = nextId++;
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 4000);
    }, []);

    const removeToast = useCallback((id: number) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const icons = {
        success: CheckCircle2,
        error: XCircle,
        warning: AlertTriangle,
        info: Info,
    };

    const colors = {
        success: "bg-success/10 border-success/20 text-success",
        error: "bg-danger/10 border-danger/20 text-danger",
        warning: "bg-warning/10 border-warning/20 text-warning",
        info: "bg-accent/10 border-accent/20 text-accent",
    };

    return (
        <ToastContext.Provider value={{ toast: addToast }}>
            {children}
            <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 pointer-events-none">
                <AnimatePresence>
                    {toasts.map(t => {
                        const Icon = icons[t.type];
                        return (
                            <motion.div
                                key={t.id}
                                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                                transition={{ duration: 0.2 }}
                                className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg bg-white min-w-[300px] max-w-[420px]`}
                            >
                                <Icon className={`w-5 h-5 shrink-0 ${colors[t.type].split(" ").pop()}`} />
                                <span className="text-sm text-primary flex-1">{t.message}</span>
                                <button
                                    onClick={() => removeToast(t.id)}
                                    className="text-muted hover:text-primary transition-colors shrink-0"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </motion.div>
                        );
                    })}
                </AnimatePresence>
            </div>
        </ToastContext.Provider>
    );
}
