import { useState } from "react";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { useUI } from "../lib/store";
import { MARKET_META, type Mkt, fmtNum } from "../lib/format";
import { ErrorState, GlassCard, Kicker, Learn, Skeleton } from "../components/ui/Card";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Tip, tick } from "../components/charts/Chart";

export default function Cross() {
  const { range, mode } = useUI();
  const { data, error, loading } = useFetch(() => api.comparison(range), [range]);
  const corr = useFetch(() => api.corr("1Y", "change"), []);
  const lags = useFetch(() => api.lags("IN:10Y", "US:10Y"), []);
  const [cell, setCell] = useState<{ a: string; b: string; v: number | null } | null>(null);
  const [node, setNode] = useState("FED");

  if (loading) return <Skeleton className="h-[70vh]" />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  const rows = Object.keys(data.matrix);
  const mkts = ["US", "IN", "UK", "EZ"];
  const y10 = merge(data.series.y10);
  const pol = merge(data.series.policy);

  return (
    <div className="space-y-6">
      <div>
        <Kicker>04 — Cross-market analysis</Kicker>
        <h1 className="font-serif text-3xl md:text-4xl mt-1">Four curves, one dollar discount rate</h1>
      </div>

      <div className="panel rounded-2xl p-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-[11px] text-mist-600">
              <th className="text-left pb-2" />
              {mkts.map((m) => (
                <th key={m} className="text-left pb-2" style={{ color: MARKET_META[m as Mkt].color }}>
                  {m}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r} className="border-t border-white/5">
                <td className="py-2 pr-3 text-mist-400">{r}</td>
                {mkts.map((m) => (
                  <td key={m} className="num">
                    {fmtCell(data.matrix[r][m])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <ChartBlock title="10Y yields" data={y10} />
        <ChartBlock title="Policy rates" data={pol} />
      </div>

      <GlassCard>
        <Kicker>Correlation heatmap · Δyield · 1Y window</Kicker>
        <div className="overflow-x-auto mt-3">
          {corr.data && (
            <table className="text-[11px] num">
              <thead>
                <tr>
                  <th />
                  {corr.data.labels.map((l) => (
                    <th key={l} className="px-1 pb-1 font-normal text-mist-600">
                      {l}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {corr.data.labels.map((row, i) => (
                  <tr key={row}>
                    <td className="pr-2 text-mist-400">{row}</td>
                    {corr.data!.matrix[i].map((v, j) => (
                      <td key={j}>
                        <button
                          onClick={() => setCell({ a: row, b: corr.data!.labels[j], v })}
                          className="w-9 h-7 rounded"
                          style={{ background: heat(v) }}
                        >
                          {v == null ? "" : v.toFixed(2)}
                        </button>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        {cell && (
          <p className="text-sm mt-3 text-mist-300">
            {cell.a} vs {cell.b}: ρ = {cell.v?.toFixed(3)}. Observed co-movement in this window — not causation.
          </p>
        )}
        {mode === "learn" && (
          <Learn title="Correlation vs transmission">
            A high US–UK 10Y correlation can come from a shared inflation shock, a shared Fed discount-rate shock, or coincidental hiking cycles. The
            lag explorer below is still just correlation at a delay.
          </Learn>
        )}
      </GlassCard>

      <div className="panel rounded-2xl p-5">
        <Kicker>Lag explorer · Δ India 10Y on lagged Δ US 10Y</Kicker>
        <p className="text-xs text-mist-600 mt-1">{lags.data?.label}</p>
        <div className="grid grid-cols-6 gap-2 mt-4">
          {lags.data?.lags.map((l) => (
            <div key={l.lag} className="rounded-xl border border-white/10 p-3 text-center">
              <div className="num text-mist-600 text-[11px]">k={l.lag}</div>
              <div className="num text-lg text-cyan">{l.correlation?.toFixed(3)}</div>
            </div>
          ))}
        </div>
        <p className="text-sm mt-3 text-mist-300">{lags.data?.interpretation}</p>
      </div>

      <Transmission node={node} setNode={setNode} />
    </div>
  );
}

function ChartBlock({ title, data }: { title: string; data: Record<string, unknown>[] }) {
  return (
    <div className="panel rounded-2xl p-4">
      <div className="kicker">{title}</div>
      <div className="h-56 mt-2">
        <ResponsiveContainer>
          <LineChart data={data}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="date" tick={tick} minTickGap={40} />
            <YAxis tick={tick} />
            <Tooltip content={<Tip />} />
            <Legend />
            {(["US", "IN", "UK", "EZ"] as Mkt[]).map((m) => (
              <Line key={m} type="monotone" dataKey={m} stroke={MARKET_META[m].color} dot={false} strokeWidth={1.5} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function merge(src: Record<string, { date: string; value: number }[]>) {
  const map = new Map<string, Record<string, string | number>>();
  Object.entries(src || {}).forEach(([m, pts]) => {
    pts.forEach((p) => {
      const row = map.get(p.date) || { date: p.date };
      row[m] = p.value;
      map.set(p.date, row);
    });
  });
  return [...map.values()].sort((a, b) => String(a.date).localeCompare(String(b.date)));
}

function fmtCell(v: number | string | null) {
  if (v === null || v === undefined) return "—";
  if (typeof v === "string") return v;
  return fmtNum(v, 2);
}

function heat(v: number | null) {
  if (v == null) return "transparent";
  const a = Math.min(Math.abs(v), 1);
  return v >= 0 ? `rgba(34,211,238,${0.15 + a * 0.55})` : `rgba(244,114,182,${0.15 + a * 0.55})`;
}

const NODES: Record<string, string> = {
  FED: "The dollar is the global discount rate. A Fed hike reprices duration everywhere via expected US shorts, USD funding, and risk appetite. Correlation still is not a proof of this channel.",
  RBI: "India’s local policy rate still dominates the G-Sec front end. Spillovers from UST 10Y typically show up as a risk-premium / FX residual, not one-for-one.",
  BOE: "Gilts trade a G7 peer to Treasuries with a gilt-specific fiscal/LDI overlay (see Sep 2022).",
  ECB: "Bunds are the euro duration benchmark. ECB deposit rate sets the floor; PEPP/PSPP and TPI are the fragmentation tools.",
  "US 2Y": "Most tightly bound to Fed funds path and forward guidance.",
  "US 10Y": "Mix of expected shorts + term premium. This is the node global real-money often hedges.",
  "Global Duration": "When US long-end cheapens, duration-sensitive portfolios rebalance. That can move India, gilts, and Bunds the same morning — or not.",
};

function Transmission({ node, setNode }: { node: string; setNode: (s: string) => void }) {
  const chain = ["FED", "US 2Y", "US 10Y", "Global Duration", "RBI", "BOE", "ECB"];
  return (
    <GlassCard>
      <Kicker>Cross-market transmission</Kicker>
      <h3 className="font-serif text-xl mt-1">Click a node. Ask why it could matter.</h3>
      <div className="flex flex-wrap gap-2 mt-4">
        {chain.map((n, i) => (
          <button key={n} onClick={() => setNode(n)} className={`px-3 py-2 rounded-full border text-sm ${node === n ? "border-cyan text-cyan" : "border-white/10 text-mist-400"}`}>
            {n}
            {i < chain.length - 1 && <span className="text-mist-600 ml-2">↓</span>}
          </button>
        ))}
      </div>
      <p className="text-sm text-mist-300 mt-4 leading-relaxed">{NODES[node]}</p>
    </GlassCard>
  );
}
