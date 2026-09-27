import type { ReactNode } from "react";

export function GlassCard({
  children,
  className = "",
  padded = true,
}: {
  children: ReactNode;
  className?: string;
  padded?: boolean;
}) {
  return <div className={`glass rounded-[18px] ${padded ? "p-4 md:p-5" : ""} ${className}`}>{children}</div>;
}

export function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`panel rounded-[16px] p-4 md:p-5 ${className}`}>{children}</div>;
}

export function Kicker({ children }: { children: ReactNode }) {
  return <div className="kicker">{children}</div>;
}

export function Learn({ title, children }: { title: string; children: ReactNode }) {
  return (
    <details className="mt-3 rounded-xl border border-white/10 bg-white/[0.02] p-3">
      <summary className="cursor-pointer text-xs tracking-[0.16em] uppercase text-cyan">{title}</summary>
      <div className="mt-2 text-sm text-mist-400 leading-relaxed">{children}</div>
    </details>
  );
}

export function EmptyState({ title, hint }: { title: string; hint: string }) {
  return (
    <div className="py-10 text-center">
      <div className="kicker">{title}</div>
      <p className="mt-2 text-sm text-mist-400">{hint}</p>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="panel rounded-2xl p-5 border-rose-500/30">
      <div className="kicker text-rose-300">DATA FEED INTERRUPTED</div>
      <p className="mt-2 text-sm text-mist-400">{message || "Data temporarily unavailable. Demo series should still load from the local API."}</p>
    </div>
  );
}

export function Skeleton({ className = "h-24" }: { className?: string }) {
  return <div className={`animate-pulse rounded-2xl bg-white/[0.04] ${className}`} />;
}
