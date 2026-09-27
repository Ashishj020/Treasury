import { useMemo, useState } from "react";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { MARKET_META, type Mkt, fmtNum, fmtPct } from "../lib/format";
import { ErrorState, GlassCard, Kicker, Learn, Skeleton } from "../components/ui/Card";
import { TooltipInfo } from "../components/ui/TooltipInfo";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Tip, tick } from "../components/charts/Chart";
import { useUI } from "../lib/store";

export default function Returns() {
  const { mode } = useUI();
  const { data, error, loading } = useFetch(() => api.returns("10Y", "MAX"), []);
  const cum = useMemo(() => mergeRet(data?.series, "cumulative"), [data]);
  const dd = useMemo(() => mergeRet(data?.series, "drawdown"), [data]);

  if (loading) return <Skeleton className="h-[70vh]" />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div>
        <Kicker>06 — Bond returns</Kicker>
        <h1 className="font-serif text-3xl md:text-4xl mt-1">Constant-maturity 10Y total return</h1>
        <p className="text-sm text-mist-400 mt-1">{data.disclaimer}</p>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {Object.entries(data.stats).map(([m, s]) => (
          <div key={m} className="panel rounded-2xl p-4">
            <div className="kicker" style={{ color: MARKET_META[m as Mkt].color }}>
              {m}
            </div>
            <div className="num text-2xl mt-1">{fmtPct(s.ann_return * 100)}</div>
            <div className="text-[11px] text-mist-400 mt-2">
              Vol {fmtPct(s.ann_vol * 100, 1)} · Max DD {fmtPct(s.max_drawdown * 100, 1)}
              <br />
              Sharpe {s.sharpe == null ? "—" : fmtNum(s.sharpe)} · 12M {s.last_12m == null ? "—" : fmtPct(s.last_12m * 100)}
            </div>
            <p className="text-[10px] text-mist-600 mt-2">{data.benchmarks[m]}</p>
          </div>
        ))}
      </div>
      <div className="panel rounded-2xl p-4">
        <Kicker>Cumulative wealth (start = 1)</Kicker>
        <div className="h-72 mt-2">
          <Lines data={cum} keys={["US", "IN", "UK", "EZ"]} />
        </div>
      </div>
      <div className="panel rounded-2xl p-4">
        <TooltipInfo term="Drawdown">Drawdowns</TooltipInfo>
        <div className="h-56 mt-2">
          <Lines data={dd} keys={["US", "IN", "UK", "EZ"]} />
        </div>
      </div>
      {mode === "learn" && (
        <Learn title="What is in the return">
          Each day we reprice a par-coupon bond with remaining maturity of 10Y, then roll back to 10Y. Coupon return uses the previous yield as the
          running coupon. This is a laboratory index, not Bloomberg/ICE/CRSP.
        </Learn>
      )}
      <BondLab />
    </div>
  );
}

function Lines({ data, keys }: { data: Record<string, unknown>[]; keys: Mkt[] }) {
  return (
    <ResponsiveContainer>
      <LineChart data={data}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="date" tick={tick} minTickGap={48} />
        <YAxis tick={tick} />
        <Tooltip content={<Tip />} />
        <Legend />
        {keys.map((k) => (
          <Line key={k} type="monotone" dataKey={k} stroke={MARKET_META[k].color} dot={false} strokeWidth={1.5} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

function mergeRet(series: Record<string, { date: string; cumulative: number; drawdown: number }[]> | undefined, key: "cumulative" | "drawdown") {
  const map = new Map<string, Record<string, string | number>>();
  Object.entries(series || {}).forEach(([m, pts]) => {
    pts.forEach((p) => {
      const row = map.get(p.date) || { date: p.date };
      row[m] = p[key];
      map.set(p.date, row);
    });
  });
  return [...map.values()].sort((a, b) => String(a.date).localeCompare(String(b.date)));
}

function BondLab() {
  const [face, setFace] = useState(100);
  const [coupon, setCoupon] = useState(4);
  const [mat, setMat] = useState(10);
  const [y, setY] = useState(4.2);
  const [shock, setShock] = useState(100);
  const body = { face, coupon_rate: coupon / 100, maturity_years: mat, yield_rate: y / 100, frequency: 2, yield_shock_bp: shock };
  const { data } = useFetch(() => api.bondLab(body), [face, coupon, mat, y, shock]);

  return (
    <GlassCard>
      <Kicker>Bond price–yield lab · duration & convexity</Kicker>
      <h3 className="font-serif text-2xl mt-1">Drag the yield. Watch the price.</h3>
      <div className="grid md:grid-cols-2 gap-6 mt-4">
        <div className="space-y-3 text-sm">
          <L label="Face" v={face} set={setFace} min={50} max={1000} />
          <L label="Coupon %" v={coupon} set={setCoupon} min={0} max={12} step={0.1} />
          <L label="Maturity" v={mat} set={setMat} min={1} max={30} />
          <L label="Yield %" v={y} set={setY} min={0.1} max={12} step={0.05} />
          <L label="Shock bp" v={shock} set={setShock} min={-300} max={300} step={5} />
          {data && (
            <div className="grid grid-cols-2 gap-2 pt-2">
              <Mini k="Price" v={fmtNum(data.price)} />
              <Mini k="Current yield" v={fmtPct(data.current_yield * 100)} />
              <Mini k="Macaulay" v={fmtNum(data.macaulay)} />
              <Mini k="Modified" v={fmtNum(data.modified)} />
              <Mini k="Convexity" v={fmtNum(data.convexity)} />
              <Mini k="Dur. error" v={fmtNum(data.duration_error)} />
            </div>
          )}
        </div>
        <div className="h-64">
          <ResponsiveContainer>
            <LineChart data={data?.curve || []}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="yield" tick={tick} />
              <YAxis tick={tick} />
              <Tooltip content={<Tip />} />
              <Line type="monotone" dataKey="price" stroke="#22D3EE" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <p className="text-sm text-mist-400 mt-3">{data?.note}</p>
      {data && (
        <p className="text-xs text-mist-600 mt-2">
          After a {shock} bp parallel: actual price {fmtNum(data.actual_price)} · duration approx {fmtNum(data.duration_approx)} · duration+convexity{" "}
          {fmtNum(data.convexity_approx)}. Convexity reduces the approximation error.
        </p>
      )}
    </GlassCard>
  );
}

function L({ label, v, set, min, max, step = 1 }: { label: string; v: number; set: (n: number) => void; min: number; max: number; step?: number }) {
  return (
    <label className="block">
      <div className="flex justify-between text-mist-400">
        {label}
        <span className="num text-mist-50">{v}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={v} onChange={(e) => set(+e.target.value)} className="w-full" />
    </label>
  );
}
function Mini({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-lg border border-white/10 p-2">
      <div className="kicker">{k}</div>
      <div className="num">{v}</div>
    </div>
  );
}
