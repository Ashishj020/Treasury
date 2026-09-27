import { useState } from "react";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { useUI } from "../lib/store";
import { fmtNum } from "../lib/format";
import { ErrorState, GlassCard, Kicker, Learn, Skeleton } from "../components/ui/Card";
import { CartesianGrid, Line, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, Tip, tick, LineChart } from "../components/charts/Chart";

const VARS = ["10Y", "2Y", "policy", "inflation", "gdp", "unemployment"];

export default function Macro() {
  const { market, mode } = useUI();
  const [x, setX] = useState("inflation");
  const [y, setY] = useState("10Y");
  const [dep, setDep] = useState("IN:10Y");
  const [inds, setInds] = useState("US:10Y,IN:policy,IN:inflation");
  const macro = useFetch(() => api.macro(market), [market]);
  const sc = useFetch(() => api.scatter(`${market}:${x}`, `${market}:${y}`), [market, x, y]);
  const [reg, setReg] = useState<Awaited<ReturnType<typeof api.regression>> | null>(null);
  const [busy, setBusy] = useState(false);

  async function run() {
    setBusy(true);
    try {
      setReg(await api.regression({ dependent: dep, independents: inds.split(",").map((s) => s.trim()), differences: true }));
    } finally {
      setBusy(false);
    }
  }

  if (macro.loading) return <Skeleton className="h-[70vh]" />;
  if (macro.error) return <ErrorState message={macro.error} />;

  const inf = macro.data?.series.inflation || [];

  return (
    <div className="space-y-6">
      <div>
        <Kicker>08 — Macro drivers</Kicker>
        <h1 className="font-serif text-3xl md:text-4xl mt-1">{market} macro vs the curve</h1>
      </div>
      <div className="panel rounded-2xl p-4">
        <Kicker>Inflation (y/y) overlay</Kicker>
        <div className="h-52 mt-2">
          <ResponsiveContainer>
            <LineChart data={inf}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="date" tick={tick} minTickGap={40} />
              <YAxis tick={tick} />
              <Tooltip content={<Tip />} />
              <Line type="monotone" dataKey="value" name="CPI y/y" stroke="#F472B6" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel rounded-2xl p-4">
        <div className="flex flex-wrap gap-2 items-center">
          <Kicker>Scatter</Kicker>
          <select value={x} onChange={(e) => setX(e.target.value)} className="bg-ink-2 border border-white/10 rounded-lg text-xs px-2 py-1">
            {VARS.map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
          <span className="text-mist-600">vs</span>
          <select value={y} onChange={(e) => setY(e.target.value)} className="bg-ink-2 border border-white/10 rounded-lg text-xs px-2 py-1">
            {VARS.map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </div>
        {sc.data && (
          <>
            <p className="text-xs num text-mist-400 mt-2">
              ρ = {fmtNum(sc.data.correlation, 3)} · R² = {fmtNum(sc.data.r_squared, 3)} · n = {sc.data.n} monthly points
            </p>
            <div className="h-64 mt-2">
              <ResponsiveContainer>
                <ScatterChart>
                  <CartesianGrid />
                  <XAxis dataKey="x" tick={tick} name={x} />
                  <YAxis dataKey="y" tick={tick} name={y} />
                  <Tooltip content={<Tip />} />
                  <Scatter data={sc.data.points} fill="#22D3EE" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>

      <GlassCard>
        <Kicker>Regression lab</Kicker>
        <h3 className="font-serif text-xl mt-1">Monthly OLS on first differences</h3>
        <div className="flex flex-wrap gap-2 mt-3">
          <input value={dep} onChange={(e) => setDep(e.target.value)} className="bg-ink-2 border border-white/10 rounded-lg text-xs px-2 py-1 num" />
          <input value={inds} onChange={(e) => setInds(e.target.value)} className="flex-1 min-w-[220px] bg-ink-2 border border-white/10 rounded-lg text-xs px-2 py-1 num" />
          <button onClick={run} className="px-3 py-1 rounded-full bg-cyan text-ink-0 text-xs">
            {busy ? "Fitting…" : "Estimate"}
          </button>
        </div>
        {reg && (
          <>
            <p className="text-xs text-mist-400 mt-3">
              n={reg.n} · R²={fmtNum(reg.r_squared, 3)} · Adj R²={fmtNum(reg.adj_r_squared, 3)}
            </p>
            <table className="w-full text-sm mt-2">
              <thead className="text-[11px] text-mist-600">
                <tr>
                  {["Variable", "Coef", "SE", "t", "p"].map((h) => (
                    <th key={h} className="text-left font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {reg.terms.map((t) => (
                  <tr key={t.variable} className="border-t border-white/5 num">
                    <td className="py-1">{t.variable}</td>
                    <td>{fmtNum(t.coefficient, 3)}</td>
                    <td>{fmtNum(t.std_error, 3)}</td>
                    <td>{fmtNum(t.t_stat, 2)}</td>
                    <td>{fmtNum(t.p_value, 3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <ul className="mt-3 text-xs text-mist-500 list-disc pl-4 space-y-1">
              {reg.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
            {mode === "learn" && (
              <Learn title="How to read this table">
                A p-value below 0.05 is often called “significant”, but these standard errors ignore autocorrelation. We do not star coefficients. The
                intercept is α; other rows are β. R² is in-sample fit, not forecasting skill.
              </Learn>
            )}
          </>
        )}
      </GlassCard>
    </div>
  );
}
