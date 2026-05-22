"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

type RepositoryFormProps = {
  onSubmit: (repoUrl: string) => Promise<void>;
};

export function RepositoryForm({ onSubmit }: RepositoryFormProps) {
  const [repoUrl, setRepoUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    try {
      await onSubmit(repoUrl);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form className="card space-y-4" onSubmit={handleSubmit}>
      <h2 className="text-xl font-semibold">Analyze GitHub Repository</h2>
      <input
        className="w-full rounded-xl border border-white/12 bg-black/35 px-4 py-3 text-white outline-none ring-cyan-400/0 transition placeholder:text-white/35 focus:border-cyan-400/50 focus:ring-2 focus:ring-cyan-400/20"
        type="url"
        placeholder="https://github.com/owner/repo"
        required
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
      />
      <Button className="gap-2 disabled:opacity-60" disabled={isLoading} type="submit">
        {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
        Run Analysis
      </Button>
    </form>
  );
}
