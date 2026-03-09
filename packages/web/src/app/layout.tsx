import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "GradeTrace — Academic Audit Platform",
  description: "Track credits, CGPA, and graduation eligibility for NSU students",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className="min-h-screen bg-bg dark:bg-gray-950 text-primary dark:text-gray-100 antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

