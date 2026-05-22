/** Fixed decorative layers — pointer-events none so UI stays usable. */
export function AmbientBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute -left-[20%] -top-[10%] h-[min(70vw,520px)] w-[min(70vw,520px)] rounded-full bg-violet-600/25 blur-[100px] motion-safe:animate-ambient-drift" />
      <div className="absolute -right-[15%] top-[20%] h-[min(65vw,480px)] w-[min(65vw,480px)] rounded-full bg-cyan-500/20 blur-[110px] motion-safe:animate-ambient-drift motion-safe:[animation-delay:-8s]" />
      <div className="absolute bottom-[-10%] left-[25%] h-[min(50vw,400px)] w-[min(50vw,400px)] rounded-full bg-blue-600/15 blur-[90px]" />
      <div
        className="absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.06) 1px, transparent 0)`,
          backgroundSize: "48px 48px",
        }}
      />
    </div>
  );
}
