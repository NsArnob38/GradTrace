"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { GraduationCap, BarChart3, Target, ArrowRight, Star, CheckCircle2 } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

const features = [
  {
    icon: GraduationCap,
    title: "Credit Tracking",
    description: "Instantly tally attempted and earned credits with retake resolution",
  },
  {
    icon: BarChart3,
    title: "CGPA Analysis",
    description: "Semester-by-semester CGPA with probation detection and standing history",
  },
  {
    icon: Target,
    title: "Graduation Roadmap",
    description: "See exactly which courses remain and get a prioritized action plan",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-4 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-border dark:border-gray-800 sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <Star className="w-7 h-7 text-accent fill-accent" />
          <span className="text-xl font-semibold tracking-tight">GradeTrace</span>
        </div>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <Link
            href="/auth/login"
            className="bg-primary dark:bg-gray-100 text-white dark:text-gray-950 px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-primary/90 dark:hover:bg-gray-200 transition-colors"
          >
            Sign In
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center px-6 py-20 relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-gradient-to-tr from-accent/10 to-transparent rounded-full blur-3xl opacity-50 -z-10" />

        <div className="w-full max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-12">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="flex-1 text-center md:text-left"
          >
            <div className="inline-flex items-center gap-2 bg-accent/10 text-accent px-4 py-1.5 rounded-full text-sm font-medium mb-6">
              <Star className="w-4 h-4 fill-accent" />
              Built for NSU Students
            </div>
            <h1 className="text-5xl md:text-6xl font-bold tracking-tight leading-tight mb-6 text-gray-900 dark:text-gray-100">
              Know exactly where you
              <span className="text-accent relative inline-block">
                <span className="relative z-10"> stand.</span>
                <span className="absolute bottom-2 left-0 w-full h-3 bg-accent/20 -z-10 -rotate-1" />
              </span>
            </h1>
            <p className="text-lg text-muted dark:text-gray-400 max-w-xl mx-auto md:mx-0 mb-10 leading-relaxed">
              Upload your transcript, get a complete audit in seconds.
              Credits, CGPA, probation status, missing courses, and a
              clear path to graduation.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center md:justify-start gap-4">
              <Link
                href="/auth/login"
                className="group w-full sm:w-auto bg-primary dark:bg-gray-800 text-white dark:text-white px-8 py-3.5 rounded-xl text-base font-medium hover:bg-primary/90 dark:hover:bg-gray-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/20 dark:shadow-none"
              >
                Get Started
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="#features"
                className="w-full sm:w-auto text-muted dark:text-gray-400 hover:text-primary dark:hover:text-gray-100 px-6 py-3.5 rounded-xl text-base font-medium hover:bg-white dark:hover:bg-gray-800 transition-all border border-border dark:border-gray-800 flex items-center justify-center"
              >
                Learn More
              </Link>
            </div>
          </motion.div>

          {/* Floating animated hero car */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
            className="flex-1 w-full max-w-md relative hidden md:block perspective-1000"
          >
            <motion.div
              animate={{ y: [-10, 10, -10] }}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
              className="relative bg-white dark:bg-gray-900 border border-border dark:border-gray-800 shadow-2xl rounded-2xl p-6 overflow-hidden rotate-y-[-5deg] rotate-x-[5deg]"
            >
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center">
                    <Star className="w-6 h-6 text-accent fill-accent" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg leading-tight">Audit Report</h3>
                    <p className="text-xs text-muted font-medium uppercase tracking-wider">CSE Program</p>
                  </div>
                </div>
                <div className="px-3 py-1 bg-success/10 text-success rounded-full text-xs font-bold">
                  PASS
                </div>
              </div>
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-semibold text-primary dark:text-gray-100">Degree Progress</span>
                    <span className="text-muted dark:text-gray-400">102 / 130</span>
                  </div>
                  <div className="h-2.5 w-full bg-bg dark:bg-gray-800 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }} animate={{ width: "78%" }}
                      transition={{ duration: 1.5, delay: 0.6, ease: "easeOut" }}
                      className="h-full bg-gradient-to-r from-accent to-accent/70 rounded-full"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-bg dark:bg-gray-800 rounded-xl p-4 border border-border/50 dark:border-gray-700/50">
                    <p className="text-xs text-muted dark:text-gray-400 font-medium mb-1 relative z-10">CGPA</p>
                    <motion.p
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }}
                      className="text-2xl font-bold text-success"
                    >
                      3.85
                    </motion.p>
                  </div>
                  <div className="bg-bg dark:bg-gray-800 rounded-xl p-4 border border-border/50 dark:border-gray-700/50">
                    <p className="text-xs text-muted dark:text-gray-400 font-medium mb-1">Standing</p>
                    <p className="text-2xl font-bold text-primary dark:text-gray-100">Normal</p>
                  </div>
                </div>
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 1.2 }}
                  className="bg-success/10 text-success border border-success/20 rounded-xl p-4 flex items-center gap-3"
                >
                  <CheckCircle2 className="w-6 h-6 shrink-0" />
                  <span className="text-sm font-medium leading-tight">All prerequisites satisfied. You are on track to graduate.</span>
                </motion.div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-6 py-20 bg-white dark:bg-gray-950">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-14">
            Three levels of audit, one click.
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, duration: 0.5 }}
                className="bg-bg dark:bg-gray-900 rounded-2xl p-7 hover:shadow-md transition-shadow dark:border dark:border-gray-800"
              >
                <div className="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center mb-4">
                  <f.icon className="w-6 h-6 text-accent" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-primary dark:text-gray-100">{f.title}</h3>
                <p className="text-muted dark:text-gray-400 text-sm leading-relaxed">{f.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-8 py-6 border-t border-border dark:border-gray-800 text-center text-sm text-muted dark:text-gray-500">
        <p>GradeTrace © 2026 — North South University</p>
      </footer>
    </div>
  );
}
