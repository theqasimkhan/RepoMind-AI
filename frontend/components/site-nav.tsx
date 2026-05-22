"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles } from "lucide-react";
import { UserMenu } from "@/components/UserMenu";
import { cn } from "@/lib/utils";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/architect", label: "Architect" },
  { href: "/diagrams", label: "Diagrams" },
  { href: "/analyze", label: "Analyze" },
  { href: "/chat", label: "Chat" },
  { href: "/settings", label: "Settings" },
] as const;

export function SiteNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-4 z-50 mb-10">
      <div className="flex flex-wrap items-center gap-x-2 gap-y-3 rounded-2xl border border-white/[0.08] bg-surface/65 px-3 py-3 shadow-xl shadow-black/40 backdrop-blur-xl sm:gap-x-3 sm:px-4 md:px-5">
        <Link
          href="/"
          className="group flex shrink-0 items-center gap-2.5 text-white transition hover:opacity-95"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-violet-500 text-slate-950 shadow-lg shadow-cyan-500/25 ring-1 ring-white/25 transition group-hover:shadow-glow">
            <Sparkles className="h-[18px] w-[18px]" strokeWidth={2.2} />
          </span>
          <span className="font-semibold tracking-tight">
            RepoMind
            <span className="ml-1.5 text-[10px] font-medium uppercase tracking-[0.2em] text-white/40">
              AI
            </span>
          </span>
        </Link>

        <nav className="flex min-w-0 flex-1 flex-wrap items-center justify-center gap-0.5 sm:justify-center md:gap-1">
          {links.map(({ href, label }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "whitespace-nowrap rounded-lg px-2.5 py-2 text-xs font-medium transition-colors sm:px-3 sm:text-sm",
                  active
                    ? "bg-white/10 text-white shadow-inner shadow-white/5 ring-1 ring-white/10"
                    : "text-white/55 hover:bg-white/[0.06] hover:text-white"
                )}
              >
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto flex shrink-0 items-center pl-1">
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
