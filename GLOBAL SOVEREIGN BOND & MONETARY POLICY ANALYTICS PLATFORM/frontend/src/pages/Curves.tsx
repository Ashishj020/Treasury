import { useState } from "react";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { useUI } from "../lib/store";
import { MARKET_META, fmtPct } from "../lib/format";
import { ErrorState, GlassCard, Kicker, Learn, Skeleton } from "../components/ui/Card";
import { TooltipInfo } from "../components/ui/TooltipInfo";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Tip, tick } from "../components/charts/Chart";

export default function Curves() {
  const { market, mode } = useUI();
  const [asof, setAsof] = useState<string>("");
  const [reveal, setReveal] = useState(false);
  const curve = useFetch(() => api.curve(market, asof || undefined, "1M,3M,1Y,5Y"), [market, asof]);
  const guess = useFetch(() => api.guess(), []);
  const series = useFetch(() => api.series(market, "10Y", "MAX", "weekly"), [market]);

  if (curve.loading) return <Skeleton className="h-[70vh]" />;
  if (curve.error) return <ErrorState message={curve.error} />;
  const c = curve.data;
  if (!c) return null;

  const chart = [
    ...c.points.map((p) => {
      const row: Record<string, number | string> = { tenor: p.tenor_years, [c.asof]: p.yield_pct, maturity: p.maturity };
      c.overlays.forEach((o) => {
        const m = o.points.find((x) => x.maturity === p.maturity);
        if (m) row[o.label] = m.yield_pct;
      });
      return row;
    }),
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <Kicker>03 — Yield curve lab</Kicker>
          <h1 className="font-serif text-3xl md:text-4xl mt-1">{MARKET_META[market].name} par curve</h1>
        </div>
        <label className="text-xs text-mist-400">
          Custom date
          <input
            type="date"
            value={asof}
            onChange={(e) => setAsof(e.target.value)}
            className="ml-2 bg-ink-2 border border-white/10 rounded-lg px-2 py-1 num"
          />
        </label>
      </div>

      <div className="grid lg:grid-cols-[1fr_280px] gap-4">
        <div className="panel rounded-2xl p-4">
          <div className="h-[380px]">
            <ResponsiveContainer>
              <LineChart data={chart}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="tenor" tick={tick} unit="y" />
                <YAxis tick={tick} domain={["auto", "auto"]} />
                <Tooltip content={<Tip />} />
                <Legend />
                <Line type="monotone" dataKey={c.asof} name="Selected" stroke={MARKET_META[market].color} strokeWidth={2.2} dot={{ r: 3 }} />
                {c.overlays.map((o, i) => (
                  <Line
                    key={o.label}
                    type="monotone"
                    dataKey={o.label}
                    stroke={["#8B95A5", "#C084FC", "#F472B6", "#34D399"][i % 4]}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="space-y-3">
          <div className="panel rounded-2xl p-4">
            <div className="kicker">Curve shape</div>
            <div className="font-serif text-3xl mt-2">{c.shape}</div>
            <div className="text-sm text-orchid mt-1">{c.personality}</div>
            <p className="text-[11px] text-mist-600 mt-2">Explanatory nickname, not a trade idea.</p>
          </div>
          <div className="panel rounded-2xl p-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <TooltipInfo term="Yield-curve steepening">2s10s</TooltipInfo>
              <span className="num">{fmtPct(c.spread_2s10s)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-mist-400">5s30s</span>
              <span className="num">{fmtPct(c.spread_5s30s)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-mist-400">10s30s</span>
              <span className="num">{fmtPct(c.spread_10s30s)}</span>
            </div>
            <p className="text-xs text-mist-600 pt-2">Spread = longer yield − shorter yield.</p>
          </div>
        </div>
      </div>

      <div className="panel rounded-2xl p-4">
        <Kicker>2s10s through time</Kicker>
        <div className="h-56 mt-3">
          <ResponsiveContainer>
            <LineChart data={series.data?.points || []}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="date" tick={tick} minTickGap={48} />
              <YAxis tick={tick} />
              <Tooltip content={<Tip />} />
              <Line type="monotone" dataKey="spread_2s10s" name="2s10s" stroke="#22D3EE" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <GlassCard>
        <Kicker>Yield curve anatomy</Kicker>
        <h3 className="font-serif text-2xl mt-1">Short end listens to the central bank. Long end argues with it.</h3>
        <div className="grid md:grid-cols-2 gap-4 mt-4 text-sm text-mist-300">
          <div>
            <div className="text-cyan">SHORT-END</div>
            <p className="mt-1">3M–2Y yields sit close to the policy path plus a small risk/liquidity premium. Hiking cycles show up here first.</p>
          </div>
          <div>
            <div className="text-orchid">LONG-END</div>
            <p className="mt-1">
              10Y–30Y mix expected future short rates, inflation expectations, growth, global risk sentiment, and term premium.
            </p>
          </div>
        </div>
        <div className="mt-5 rounded-xl border border-white/10 p-4 font-serif text-center">
          10Y yield <span className="text-mist-600">=</span> expected future short rates <span className="text-mist-600">+</span> term premium
        </div>
        <p className="text-xs text-mist-600 mt-2">
          Conceptual decomposition only. This DEMO dataset does not identify term premium (no ACM / Kim-Wright model is estimated).
        </p>
        {mode === "learn" && (
          <Learn title="Learn the concept">
            When the Fed hikes, 2Y usually jumps. 10Y jumps less unless inflation expectations or term premium also reprice. That gap is why 2s10s
            flattened (then inverted) in 2022–23 in the real world — and in this sandbox.
          </Learn>
        )}
      </GlassCard>

      <div className="panel rounded-2xl p-5">
        <div className="kicker">Guess the curve</div>
        <h3 className="font-serif text-xl">{guess.data?.question}</h3>
        <p className="text-xs text-mist-600 mt-1">
          Unlabelled {guess.data?.market} curve on {guess.data?.before_date}
        </p>
        <div className="h-56 mt-3">
          <ResponsiveContainer>
            <LineChart
              data={(reveal ? guess.data?.after : guess.data?.before)?.map((p) => ({ tenor: p.tenor_years, y: p.yield_pct, maturity: p.maturity }))}
            >
              <CartesianGrid vertical={false} />
              <XAxis dataKey="tenor" tick={tick} />
              <YAxis tick={tick} />
              <Line type="monotone" dataKey="y" stroke="#C084FC" strokeWidth={2} dot />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <button onClick={() => setReveal(true)} className="mt-3 text-xs px-3 py-1 rounded-full border border-cyan/40 text-cyan">
          Reveal what happened next ({guess.data?.after_date})
        </button>
      </div>
    </div>
  );
}
