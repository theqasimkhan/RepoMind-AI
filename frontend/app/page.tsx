"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Brain, GitBranch, Layers, MessageSquare, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: Layers,
    title: "Architecture map",
    desc: "Stack, patterns, and folder-level explanations inferred from the tree.",
  },
  {
    icon: GitBranch,
    title: "Diagrams & 3D view",
    desc: "Mermaid flows and an interactive galaxy of files and API touchpoints.",
  },
  {
    icon: MessageSquare,
    title: "Repo-grounded chat",
    desc: "Ask questions with citations tied to real paths and retrieval traces.",
  },
  {
    icon: Brain,
    title: "Architect mode",
    desc: "Staff-engineer style plans for features and refactors on your codebase.",
  },
] as const;

const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
};

export default function LandingPage() {
  return (
    <div className="space-y-16 pb-8">
      <section className="relative flex min-h-[72vh] flex-col justify-center gap-8 pt-4">
        <motion.div
          initial="initial"
          animate="animate"
          transition={{ staggerChildren: 0.08 }}
          className="space-y-6"
        >
          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.45 }}
            className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/[0.04] px-4 py-1.5 text-xs font-medium uppercase tracking-[0.18em] text-cyan-200/90 shadow-lg shadow-cyan-500/10"
          >
            <Zap className="h-3.5 w-3.5 text-cyan-300" />
            Open-source ready
          </motion.p>
          <motion.h1
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="max-w-4xl text-4xl font-bold leading-[1.08] tracking-tight sm:text-5xl md:text-6xl"
          >
            <span className="text-gradient">Understand any GitHub repo</span>
            <span className="mt-2 block text-white/90">
              with AI architecture intelligence.
            </span>
          </motion.h1>
          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="max-w-2xl text-base leading-relaxed text-white/65 sm:text-lg"
          >
            Scan structure, surface risks, generate diagrams, and chat with evidence-backed
            answers — built for READMEs that impress and workflows that scale.
          </motion.p>
          <motion.div
            variants={fadeUp}
            transition={{ duration: 0.45 }}
            className="flex flex-wrap gap-3 pt-2"
          >
            <Link href="/dashboard">
              <Button className="min-w-[160px] px-6 py-2.5 text-base">Open dashboard</Button>
            </Link>
            <Link href="/architect">
              <Button variant="outline" className="px-6 py-2.5 text-base">
                Try Architect
              </Button>
            </Link>
          </motion.div>
        </motion.div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {features.map(({ icon: Icon, title, desc }, i) => (
          <motion.div
            key={title}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: i * 0.06, duration: 0.4 }}
            className="card group hover:border-cyan-500/25 hover:shadow-glow"
          >
            <div className="mb-4 inline-flex rounded-xl bg-gradient-to-br from-cyan-500/20 to-violet-500/20 p-3 ring-1 ring-white/10 transition group-hover:from-cyan-400/30 group-hover:to-violet-400/25">
              <Icon className="h-5 w-5 text-cyan-200" strokeWidth={1.8} />
            </div>
            <h2 className="text-base font-semibold text-white">{title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-white/60">{desc}</p>
          </motion.div>
        ))}
      </section>

      <section className="card flex flex-col items-start justify-between gap-6 border-cyan-500/20 bg-gradient-to-br from-cyan-500/[0.07] to-violet-600/[0.06] sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-semibold text-white">Ship a sharper portfolio piece</h2>
          <p className="mt-2 max-w-xl text-sm text-white/65">
            Clone, run locally, and point it at public repos — the UI is tuned for dark mode demos
            and GitHub README screenshots.
          </p>
        </div>
        <Link href="/login">
          <Button variant="outline" className="shrink-0 border-white/25 bg-white/[0.04] hover:bg-white/[0.08]">
            Sign in with GitHub
          </Button>
        </Link>
      </section>
    </div>
  );
}
