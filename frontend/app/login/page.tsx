"use client";

import { Github } from "lucide-react";
import { motion } from "framer-motion";

export default function LoginPage() {
  const handleLogin = () => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    window.location.href = `${apiBase}/api/v1/auth/github`;
  };

  return (
    <div className="flex min-h-[65vh] flex-col items-center justify-center px-2">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        className="w-full max-w-md overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.07] to-white/[0.02] p-8 shadow-2xl shadow-black/40 backdrop-blur-xl"
      >
        <div className="mb-8 text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-violet-500 text-slate-950 shadow-lg shadow-cyan-500/30">
            <Github className="h-7 w-7" strokeWidth={2} />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Welcome back</h1>
          <p className="mt-2 text-sm leading-relaxed text-white/55">
            Sign in with GitHub to sync analysis snapshots and unlock authenticated API routes.
          </p>
        </div>

        <button
          type="button"
          onClick={handleLogin}
          className="flex w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-cyan-400 via-sky-400 to-violet-400 px-4 py-3.5 text-sm font-bold text-slate-950 shadow-lg shadow-cyan-500/25 transition hover:brightness-110 hover:shadow-glow active:scale-[0.99]"
        >
          <Github className="h-5 w-5" />
          Continue with GitHub
        </button>

        <p className="mt-6 text-center text-xs text-white/40">
          By continuing you authorize RepoMind to read your public GitHub profile for login.
        </p>
      </motion.div>
    </div>
  );
}
