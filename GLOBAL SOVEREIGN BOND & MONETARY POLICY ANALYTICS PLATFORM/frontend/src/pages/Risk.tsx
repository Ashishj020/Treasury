import { useState } from "react";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { useUI } from "../lib/store";
import { fmtNum, fmtPct } from "../lib/format";
import { ErrorState, Kicker, Learn, Skeleton } from "../components/ui/Card";
import { TooltipInfo } from "../components/ui/TooltipInfo";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Tip, tick } from "../components/charts/Chart";

export default function Risk() {
  const { market, mode } = useUI();
  const [w, setW] = useState(60);
  const { data, error, loading } = useFetch(() => api.risk(market, w), [market, w]);
  if (loading) return <Skeleton className="h-[70vh]" />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div>
        <Kicker>07 — Risk & volatility</Kicker>
        <h1 className="font-serif text-3xl md:text-4xl mt-1">{market} realised risk</h1>
      </div>
      <div className="flex gap-2">
        {[30, 60, 90, 252].map((x) => (
          <button key={x} onClick={() => setW(x)} className={`px-3 py-1 rounded-full border text-xs num ${w === x ? "border-cyan text-cyan" : "border-white/10"}`}>
            {x}D
          </button>
        ))}
      </div>
      <div className="grid sm:grid-cols-3 gap-3">
        <Box k="Max drawdown" v={fmtPct(data.max_drawdown * 100, 1)} term="Drawdown" />
        <Box k="5% historical VaR (daily)" v={data.var_5pct_daily == null ? "—" : fmtPct(data.var_5pct_daily * 100, 2)} term="Volatility" />
        <Box k="Sharpe" v={data.sharpe == null ? "—" : fmtNum(data.sharpe)} />
      </div>
      <p className="text-xs text-mist-600">{data.note}</p>
      <div className="panel rounded-2xl p-4">
        <Kicker>Rolling return volatility</Kicker>
        <div className="h-64 mt-2">
          <ResponsiveContainer>
            <LineChart data={data.return_vol}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="date" tick={tick} minTickGap={48} />
              <YAxis tick={tick} />
              <Tooltip content={<Tip />} />
              <Line type="monotone" dataKey="value" name="ann. vol" stroke="#F472B6" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="panel rounded-2xl p-4">
        <Kicker>Drawdown of 10Y TR index</Kicker>
        <div className="h-56 mt-2">
          <ResponsiveContainer>
            <LineChart data={data.drawdown}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="date" tick={tick} minTickGap={48} />
              <YAxis tick={tick} />
              <Tooltip content={<Tip />} />
              <Line type="monotone" dataKey="value" stroke="#A78BFA" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      {mode === "learn" && (
        <Learn title="Do not overstate VaR">
          Historical VaR is the 5% quantile of this sample’s daily returns. It is silent about tomorrow, about liquidity, and about a 2022-style
          hiking surprise that sits in the tail of a short window.
        </Learn>
      )}
    </div>
  );
}

function Box({ k, v, term }: { k: string; v: string; term?: string }) {
  return (
    <div className="panel rounded-2xl p-4">
      <div className="flex justify-between">
        <div className="kicker">{k}</div>
        {term && <TooltipInfo term={term} />}
      </div>
      <div className="num text-2xl mt-2">{v}</div>
    </div>
  );
}
