import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Workflow } from "lucide-react";

export default function AnalyzePage() {
  return (
    <section className="space-y-8">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Analysis</h1>
        <p className="max-w-2xl text-sm text-white/55 sm:text-base">
          Submit repos and track jobs from the dashboard — this route is a quick entry point for
          READMEs and deep links.
        </p>
      </div>
      <div className="card flex flex-col items-start gap-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500/25 to-violet-500/25 ring-1 ring-white/10">
            <Workflow className="h-6 w-6 text-cyan-200" />
          </div>
          <p className="text-sm leading-relaxed text-white/65">
            Use the dashboard workflow to submit a repository URL and inspect generated analysis,
            diagrams, and chat context.
          </p>
        </div>
        <Link href="/dashboard" className="shrink-0">
          <Button>Open dashboard</Button>
        </Link>
      </div>
    </section>
  );
}
