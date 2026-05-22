"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { fetchWithAuth } from "@/lib/auth";
import { Loader2 } from "lucide-react";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    async function verifySession() {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      const res = await fetchWithAuth(`${apiBase}/api/v1/auth/me`);
      if (res.ok) {
        router.replace("/dashboard");
      } else {
        router.replace("/login?error=session");
      }
    }
    void verifySession();
  }, [router]);

  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <div className="flex flex-col items-center gap-5 rounded-2xl border border-white/10 bg-white/[0.03] px-10 py-12 shadow-2xl shadow-black/30 backdrop-blur-md">
        <Loader2 className="h-10 w-10 animate-spin text-cyan-400" aria-hidden />
        <p className="text-sm font-medium text-white/70">Completing sign-in…</p>
      </div>
    </div>
  );
}
