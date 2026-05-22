import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";

import { AuthProvider } from "@/components/AuthProvider";
import { AmbientBackground } from "@/components/ambient-background";
import { SiteNav } from "@/components/site-nav";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  title: "RepoMind AI — GitHub intelligence",
  description:
    "AI-powered repository analysis: architecture insights, diagrams, and chat grounded in your codebase.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={outfit.variable} suppressHydrationWarning>
      <body className="font-sans antialiased" suppressHydrationWarning>
        <AmbientBackground />
        <AuthProvider>
          <main className="relative mx-auto min-h-screen w-full max-w-6xl px-4 pb-20 pt-4 sm:px-6 sm:pt-6">
            <SiteNav />
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
