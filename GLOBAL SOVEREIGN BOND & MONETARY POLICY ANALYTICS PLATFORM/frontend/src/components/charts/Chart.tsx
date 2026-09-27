import type { ReactNode } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Area,
  AreaChart,
  Bar,
  BarChart,
  ReferenceLine,
  Scatter,
  ScatterChart,
  ZAxis,
  Legend,
  ComposedChart,
} from "recharts";

export const tick = { fill: "#8B95A5", fontSize: 11, fontFamily: "IBM Plex Mono" };

export function ChartFrame({ title, kicker, children, height = 280 }: { title?: string; kicker?: string; children: ReactNode; height?: number }) {
  return (
    <div>
      {kicker && <div className="kicker">{kicker}</div>}
      {title && <h3 className="font-serif text-xl mt-1 mb-3">{title}</h3>}
      <div style={{ height }}>{children}</div>
    </div>
  );
}

export function Tip({ active, payload, label }: { active?: boolean; payload?: { name: string; value: number; color: string }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-lg px-3 py-2 text-xs">
      <div className="num text-mist-400">{label}</div>
      {payload.map((p) => (
        <div key={p.name} className="num" style={{ color: p.color }}>
          {p.name}: {typeof p.value === "number" ? p.value.toFixed(3) : p.value}
        </div>
      ))}
    </div>
  );
}

export {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Area,
  AreaChart,
  Bar,
  BarChart,
  ReferenceLine,
  Scatter,
  ScatterChart,
  ZAxis,
  Legend,
  ComposedChart,
};
