import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const tooltipStyle = {
  background: "#0B0F14",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  fontSize: 12,
  color: "#F5F7FA",
};

export function LineArea({
  data,
  x,
  series,
  height = 220,
}: {
  data: object[];
  x: string;
  series: { key: string; color: string; name?: string }[];
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <defs>
          {series.map((s) => (
            <linearGradient key={s.key} id={`g-${s.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={s.color} stopOpacity={0.28} />
              <stop offset="100%" stopColor={s.color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid vertical={false} />
        <XAxis dataKey={x} tickLine={false} axisLine={false} />
        <YAxis tickLine={false} axisLine={false} width={42} />
        <Tooltip contentStyle={tooltipStyle} />
        {series.map((s) => (
          <Area key={s.key} type="monotone" dataKey={s.key} name={s.name || s.key} stroke={s.color} fill={`url(#g-${s.key})`} strokeWidth={1.6} />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function Bars({
  data,
  x,
  series,
  height = 220,
  stacked = false,
}: {
  data: object[];
  x: string;
  series: { key: string; color: string; name?: string }[];
  height?: number;
  stacked?: boolean;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey={x} tickLine={false} axisLine={false} />
        <YAxis tickLine={false} axisLine={false} width={42} />
        <Tooltip contentStyle={tooltipStyle} />
        {series.length > 1 && <Legend />}
        {series.map((s) => (
          <Bar key={s.key} dataKey={s.key} name={s.name || s.key} fill={s.color} stackId={stacked ? "a" : undefined} radius={[3, 3, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function Lines({
  data,
  x,
  series,
  height = 220,
}: {
  data: object[];
  x: string;
  series: { key: string; color: string; name?: string }[];
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey={x} tickLine={false} axisLine={false} />
        <YAxis tickLine={false} axisLine={false} width={42} />
        <Tooltip contentStyle={tooltipStyle} />
        <Legend />
        {series.map((s) => (
          <Line key={s.key} type="monotone" dataKey={s.key} name={s.name || s.key} stroke={s.color} strokeWidth={1.7} dot={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export function WaterfallChart({ data, height = 260 }: { data: { label: string; value: number; type?: string }[]; height?: number }) {
  let acc = 0;
  const shaped = data.map((d) => {
    if (d.type === "total") {
      acc = d.value;
      return { ...d, start: 0, display: d.value, fill: "#22D3EE" };
    }
    const start = acc;
    acc += d.value;
    return { ...d, start: Math.min(start, acc), display: Math.abs(d.value), fill: d.value >= 0 ? "#34D399" : "#FB7185" };
  });
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={shaped} margin={{ top: 8, right: 8, left: 0, bottom: 24 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="label" tickLine={false} axisLine={false} interval={0} angle={-18} textAnchor="end" height={50} />
        <YAxis tickLine={false} axisLine={false} width={42} />
        <Tooltip contentStyle={tooltipStyle} />
        <Bar dataKey="start" stackId="w" fill="transparent" />
        <Bar dataKey="display" stackId="w" radius={[3, 3, 0, 0]}>
          {shaped.map((d, i) => (
            <Cell key={i} fill={d.fill} />
          ))}
        </Bar>
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function Donut({ data, height = 200 }: { data: { name: string; value: number; color: string }[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={48} outerRadius={74} paddingAngle={2}>
          {data.map((d) => (
            <Cell key={d.name} fill={d.color} />
          ))}
        </Pie>
        <Tooltip contentStyle={tooltipStyle} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function Spark({ data, color = "#22D3EE" }: { data: number[]; color?: string }) {
  const series = data.map((v, i) => ({ i, v }));
  return (
    <ResponsiveContainer width="100%" height={36}>
      <LineChart data={series} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
        <Line type="monotone" dataKey="v" stroke={color} strokeWidth={1.4} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
