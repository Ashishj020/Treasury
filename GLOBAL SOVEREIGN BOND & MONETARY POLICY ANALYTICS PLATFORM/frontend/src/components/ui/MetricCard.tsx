import { TooltipInfo } from "./TooltipInfo";
import { fmtBp, fmtPct } from "../../lib/format";

export function MetricCard({
  kicker,
  value,
  suffix,
  delta,
  term,
  spark,
  color = "#22D3EE",
}: {
  kicker: string;
  value: string | number;
  suffix?: string;
  delta?: number | null;
  term?: string;
  spark?: number[];
  color?: string;
}) {
  const min = spark && spark.length ? Math.min(...spark) : 0;
  const max = spark && spark.length ? Math.max(...spark) : 1;
  const pts = (spark || [])
    .map((v, i) => {
      const x = (i / Math.max(spark!.length - 1, 1)) * 100;
      const y = 28 - ((v - min) / Math.max(max - min, 1e-6)) * 24;
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <div className="panel rounded-2xl p-4 hover:border-white/15 transition">
      <div className="flex items-center justify-between">
        <div className="kicker">{kicker}</div>
        {term && <TooltipInfo term={term} />}
      </div>
      <div className="mt-2 flex items-end justify-between gap-3">
        <div>
          <div className="num text-3xl tracking-tight" style={{ color }}>
            {typeof value === "number" ? fmtPct(value) : value}
            {suffix}
          </div>
          {delta !== undefined && (
            <div className={`num text-xs mt-1 ${delta && delta > 0 ? "text-[#FB7185]" : "text-emerald"}`}>{fmtBp(delta ?? null)}</div>
          )}
        </div>
        {spark && spark.length > 2 && (
          <svg viewBox="0 0 100 32" className="w-24 h-8 opacity-80">
            <polyline fill="none" stroke={color} strokeWidth="1.4" points={pts} />
          </svg>
        )}
      </div>
    </div>
  );
}
