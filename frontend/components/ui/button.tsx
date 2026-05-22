import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline";
};

export function Button({
  className,
  variant = "default",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50",
        variant === "default"
          ? "bg-gradient-to-r from-cyan-400 via-sky-400 to-violet-400 bg-[length:120%_100%] text-slate-950 shadow-lg shadow-cyan-500/25 hover:brightness-110 hover:shadow-glow active:scale-[0.98]"
          : "border border-white/20 bg-white/[0.04] text-white/95 backdrop-blur-sm hover:border-white/30 hover:bg-white/[0.08]",
        className
      )}
      {...props}
    />
  );
}
