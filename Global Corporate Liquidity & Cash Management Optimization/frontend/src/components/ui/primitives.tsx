import type { ReactNode } from "react";

export function Panel({
  children,
  className = "",
  pad = true,
}: {
  children: ReactNode;
  className?: string;
  pad?: boolean;
}) {
  return <section className={`panel ${pad ? "p-5" : ""} ${className}`}>{children}</section>;
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <div className="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.22em] text-faint">
      <span className="h-px w-4 bg-cyan/50" />
      {children}
    </div>
  );
}

export function Tip({ title, children }: { title: string; children: ReactNode }) {
  return (
    <span className="group relative inline-flex">
      <button
        type="button"
        className="ml-1 text-[10px] text-faint underline decoration-dotted"
        aria-label={`About ${title}`}
      >
        i
      </button>
      <span className="pointer-events-none absolute left-0 top-5 z-30 hidden w-64 rounded-md border border-white/10 bg-[#0B0F14] p-3 text-[11px] leading-relaxed text-mute shadow-xl group-hover:block group-focus-within:block">
        <strong className="mb-1 block text-ink">{title}</strong>
        {children}
      </span>
    </span>
  );
}

export function Stat({
  label,
  value,
  hint,
  delta,
  tone = "default",
}: {
  label: string;
  value: string;
  hint?: string;
  delta?: string;
  tone?: "default" | "pos" | "neg" | "warn" | "idle";
}) {
  const color =
    tone === "pos" ? "text-emerald" : tone === "neg" ? "text-danger" : tone === "warn" ? "text-pink" : tone === "idle" ? "text-mint" : "text-ink";
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.18em] text-faint">{label}</div>
      <div className={`num mt-1 text-2xl ${color}`}>{value}</div>
      <div className="mt-1 flex gap-2 text-[11px] text-mute">
        {delta && <span>{delta}</span>}
        {hint && <span>{hint}</span>}
      </div>
    </div>
  );
}

export function Skeleton({ className = "h-24" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-white/[0.04] ${className}`} />;
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="panel p-6 text-sm text-pink">
      <div className="text-[10px] uppercase tracking-[0.2em] text-faint">Data feed interrupted</div>
      <p className="mt-2 text-mute">Unable to retrieve the simulated book. {message}</p>
    </div>
  );
}

export function Learn({ children, on }: { children: ReactNode; on: boolean }) {
  if (!on) return null;
  return (
    <div className="mt-3 border-l border-cyan/30 pl-3 text-[12px] leading-relaxed text-mute">{children}</div>
  );
}

export function Segment<T extends string>({
  value,
  onChange,
  options,
}: {
  value: T;
  onChange: (v: T) => void;
  options: { id: T; label: string }[];
}) {
  return (
    <div className="inline-flex rounded-full border border-white/10 bg-white/[0.03] p-0.5">
      {options.map((o) => (
        <button
          key={o.id}
          type="button"
          onClick={() => onChange(o.id)}
          className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-wider transition ${
            value === o.id ? "bg-cyan text-bg" : "text-mute hover:text-ink"
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function SliderRow({
  label,
  value,
  min,
  max,
  step,
  onChange,
  suffix,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
  suffix?: string;
}) {
  return (
    <label className="block">
      <div className="mb-1 flex justify-between text-[11px] uppercase tracking-wider text-faint">
        <span>{label}</span>
        <span className="num text-cyan">
          {value}
          {suffix}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-cyan"
      />
    </label>
  );
}

export function Table({
  columns,
  rows,
}: {
  columns: { key: string; label: string; align?: "left" | "right" }[];
  rows: Record<string, string | number>[];
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-[12px]">
        <thead className="sticky top-0 text-[10px] uppercase tracking-[0.16em] text-faint">
          <tr>
            {columns.map((c) => (
              <th key={c.key} className={`border-b border-white/10 py-2 font-medium ${c.align === "right" ? "text-right" : ""}`}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-white/[0.04] hover:bg-white/[0.03]">
              {columns.map((c) => (
                <td key={c.key} className={`py-2.5 ${c.align === "right" ? "num text-right" : ""}`}>
                  {r[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
