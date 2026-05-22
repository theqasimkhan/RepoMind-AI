"use client";

import { useAuth } from "@/components/AuthProvider";
import { Github, Loader2, LogOut } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

export function UserMenu() {
  const { user, isLoading, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const close = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [isOpen]);

  if (isLoading) {
    return (
      <Loader2 className="h-5 w-5 animate-spin text-cyan-400/80" aria-hidden />
    );
  }

  if (!user) {
    return (
      <Link
        href="/login"
        className="flex items-center gap-2 rounded-xl border border-white/15 bg-white/[0.06] px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-black/20 transition hover:border-cyan-500/40 hover:bg-white/[0.1]"
      >
        <Github className="h-4 w-4" />
        Sign in
      </Link>
    );
  }

  return (
    <div className="relative" ref={rootRef}>
      <button
        type="button"
        aria-expanded={isOpen}
        aria-haspopup="true"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 overflow-hidden rounded-full border border-white/15 bg-white/[0.06] p-0.5 shadow-md shadow-black/30 ring-0 transition hover:border-cyan-400/35 hover:ring-2 hover:ring-cyan-400/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/50"
      >
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt=""
            className="h-8 w-8 rounded-full object-cover"
          />
        ) : (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500/40 to-violet-500/40 text-xs font-bold text-white">
            {user.login.charAt(0).toUpperCase()}
          </div>
        )}
      </button>

      {isOpen ? (
        <div className="absolute right-0 mt-2 w-52 overflow-hidden rounded-xl border border-white/10 bg-surface/95 py-1 shadow-2xl shadow-black/50 backdrop-blur-xl">
          <div className="border-b border-white/10 px-3 py-2.5">
            <p className="text-[10px] font-medium uppercase tracking-wider text-white/40">
              Signed in
            </p>
            <p className="truncate text-sm font-medium text-white">{user.login}</p>
          </div>
          <button
            type="button"
            onClick={() => {
              setIsOpen(false);
              logout();
            }}
            className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm text-white/80 transition hover:bg-white/[0.06] hover:text-white"
          >
            <LogOut className="h-4 w-4 text-cyan-400/90" />
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  );
}
