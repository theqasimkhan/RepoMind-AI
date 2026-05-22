import { Cpu, Sliders } from "lucide-react";

export default function SettingsPage() {
  return (
    <section className="space-y-8">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Settings</h1>
        <p className="max-w-2xl text-sm text-white/55 sm:text-base">
          Environment-backed configuration lives on the API. This panel will grow with provider
          keys and analysis defaults.
        </p>
      </div>
      <div className="card flex flex-col gap-4 sm:flex-row sm:items-start">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500/25 to-violet-500/25 ring-1 ring-white/10">
          <Sliders className="h-6 w-6 text-cyan-200/90" />
        </div>
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
            <Cpu className="h-5 w-5 text-violet-300/80" />
            Coming soon
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-white/60">
            Configure API endpoints, model providers, and retrieval defaults in upcoming iterations.
            For now, use backend <code className="rounded bg-black/40 px-1.5 py-0.5 text-xs text-cyan-200/90">.env</code>{" "}
            and docs in the repo.
          </p>
        </div>
      </div>
    </section>
  );
}
