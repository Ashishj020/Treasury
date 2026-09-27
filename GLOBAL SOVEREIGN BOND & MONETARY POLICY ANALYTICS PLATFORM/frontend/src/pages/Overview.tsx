import { useState } from "react";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { useUI } from "../lib/store";
import { MARKET_META, type Mkt, fmtBp, fmtPct } from "../lib/format";
import { MetricCard } from "../components/ui/MetricCard";
import { ErrorState, GlassCard, Kicker, Learn, Skeleton } from "../components/ui/Card";
import { TooltipInfo } from "../components/ui/TooltipInfo";
import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Tip,
  tick,
} from "../components/charts/Chart";

export default function Overview() {
  const { market, range, frequency, mode, setMarket } = useUI();
  const { data, error, loading } = useFetch(() => api.overview(range, frequency), [range, frequency]);
  const series = useFetch(() => api.series(market, "10Y", range, frequency), [market, range, frequency]);
  const [event, setEvent] = useState<{ category: string; title: string; description: string; date: string; markets: string } | null>(null);
  const ev = series.data?.events ?? [];

  if (loading) return <Skeleton className="h-[70vh]" />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  const policyNames: Record<string, string> = {
    US: "Fed Funds Rate",
    IN: "RBI Repo Rate",
    UK: "BoE Bank Rate",
    EZ: "ECB Deposit Rate",
  };

  return (
    <div className="space-y-6">
      <div>
        <Kicker>01 — Global overview</Kicker>
        <h1 className="font-serif text-3xl md:text-4xl mt-1">Sovereign bond monitor</h1>
        <p className="text-sm text-mist-400 mt-1">SIMULATED DATA — FOR ANALYTICAL DEMONSTRATION. As of {data.asof}.</p>
      </div>

      <div className="flex items-center gap-3 text-sm">
        <span className="kicker">Bond market mood</span>
        <span
          className={`px-3 py-1 rounded-full border text-xs ${
            data.mood.tone === "green"
              ? "border-emerald/40 text-emerald"
              : data.mood.tone === "red"
                ? "border-rose-400/40 text-rose-300"
                : data.mood.tone === "violet"
                  ? "border-violet/40 text-orchid"
                  : "border-amber-400/40 text-amber-200"
          }`}
        >
          {data.mood.code}
        </span>
        <span className="text-xs text-mist-600">Explanatory label, not a recommendation.</span>
      </div>

      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-3">
        {data.kpis.map((k) => (
          <button key={k.market} onClick={() => setMarket(k.market as Mkt)} className="text-left">
            <MetricCard
              kicker={k.label}
              value={k.current}
              delta={k.change_1d_bp}
              spark={k.sparkline}
              color={MARKET_META[k.market as Mkt].color}
              term="Bond yield"
            />
            <div className="flex gap-3 px-1 mt-1 text-[11px] num text-mist-400">
              <span>1M {fmtBp(k.change_1m_bp)}</span>
              <span>1Y {fmtBp(k.change_1y_bp)}</span>
            </div>
          </button>
        ))}
      </div>

      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-3">
        {data.policy.map((p) => (
          <MetricCard
            key={p.market}
            kicker={policyNames[p.market]}
            value={p.current}
            delta={p.change_90d_bp}
            spark={p.sparkline}
            color={MARKET_META[p.market as Mkt].color}
            term="Policy rate"
          />
        ))}
      </div>

      <GlassCard>
        <Kicker>Global policy heatmap</Kicker>
        <h3 className="font-serif text-xl mt-1 mb-4">Where is each central bank in the cycle?</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-[11px] text-mist-600">
              <tr>
                {["Market", "Rate", "Cycle", "Regime", "CUTTING", "HOLDING", "HIKING", "QE", "QT", "2s10s"].map((h) => (
                  <th key={h} className="text-left font-medium pb-2 pr-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.heatmap.map((h) => (
                <tr key={h.market} className="border-t border-white/5">
                  <td className="py-2 pr-3" style={{ color: MARKET_META[h.market as Mkt].color }}>
                    {h.market}
                  </td>
                  <td className="num">{fmtPct(h.policy_rate)}</td>
                  <td className="num">{h.cycle}</td>
                  <td className="num">{h.regime}</td>
                  {(["cutting", "holding", "hiking", "qe", "qt"] as const).map((k) => (
                    <td key={k}>
                      <span className={`inline-block w-2.5 h-2.5 rounded-full ${h[k] ? "bg-cyan" : "bg-white/10"}`} />
                    </td>
                  ))}
                  <td className="num">{h.slope_2s10s == null ? "—" : fmtPct(h.slope_2s10s)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {mode === "learn" && (
          <Learn title="Learn the classification">
            Hiking / cutting / holding uses a 90-session change in the policy rate (±12 bp). Hawkish / dovish / neutral uses ±25 bp, with QE/QT as
            modifiers. These are transparent rules, not a hidden model.
          </Learn>
        )}
      </GlassCard>

      <div className="panel rounded-2xl p-4 md:p-5">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <Kicker>Hero visualization</Kicker>
            <h3 className="font-serif text-xl mt-1">
              Policy rate vs 10Y sovereign yield · {MARKET_META[market].name}
            </h3>
          </div>
          <TooltipInfo term="Policy transmission">POLICY → 10Y</TooltipInfo>
        </div>
        <div className="h-[360px] mt-4">
          <ResponsiveContainer>
            <ComposedChart data={series.data?.points || []}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="date" tick={tick} minTickGap={48} />
              <YAxis tick={tick} domain={["auto", "auto"]} />
              <Tooltip content={<Tip />} />
              <Legend />
              <Line type="monotone" dataKey="policy" name="Policy rate" stroke="#C084FC" dot={false} strokeWidth={1.6} />
              <Line type="monotone" dataKey="yield" name="10Y yield" stroke={MARKET_META[market].color} dot={false} strokeWidth={1.8} />
              {ev.map((e) => (
                <ReferenceLine
                  key={e.code}
                  x={e.date}
                  stroke="rgba(255,255,255,0.18)"
                  strokeDasharray="3 3"
                  ifOverflow="extendDomain"
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          {ev.map((e) => (
            <button
              key={e.code}
              onClick={() => setEvent(e)}
              className="text-[11px] px-2 py-1 rounded-full border border-white/10 text-mist-400 hover:text-cyan"
            >
              {e.category}
            </button>
          ))}
        </div>
        {event && (
          <div className="mt-4 glass rounded-xl p-4">
            <div className="kicker">{event.category}</div>
            <div className="font-serif text-lg">{event.title}</div>
            <p className="text-sm text-mist-400 mt-1">{event.description}</p>
            <p className="text-[11px] text-mist-600 mt-2">
              {event.date} · {event.markets}
            </p>
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-3">
        {data.insights.map((ins) => (
          <div key={ins.title} className="panel rounded-2xl p-4">
            <div className="kicker text-cyan">{ins.title}</div>
            <p className="text-sm mt-2 text-mist-200 leading-relaxed">{ins.body}</p>
            {ins.a !== undefined && (
              <div className="num text-xs mt-2 text-mist-400">
                {fmtBp(ins.a)} vs {fmtBp(ins.b ?? null)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
