import { useEffect, useState } from "react";
import { api, type ScenarioResp } from "../lib/api";
import { MARKET_META, type Mkt, fmtBp, fmtPct } from "../lib/format";
import { GlassCard, Kicker, Learn } from "../components/ui/Card";
import { useUI } from "../lib/store";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis, Tip, tick } from "../components/charts/Chart";

const STAGES = [
  { id: "cb", t: "CENTRAL BANK", d: "A committee sets the operational rate (and sometimes the balance-sheet path)." },
  { id: "pr", t: "POLICY RATE", d: "Overnight reserves are repriced. This is the instrument, not the 10Y." },
  { id: "mm", t: "MONEY MARKET", d: "Bills, OIS and repo hug the new target. The front end of the curve is now in play." },
  { id: "st", t: "SHORT-TERM YIELDS", d: "2Y yields are mostly expected policy over the next eight quarters, plus a small premium." },
  { id: "ex", t: "EXPECTATIONS", d: "Investors rewrite the path: how many more hikes? When do cuts start? Forward guidance lives here." },
  { id: "lt", t: "LONG-TERM YIELDS", d: "10Y/30Y mix that path with inflation, growth and term premium. They do not have to follow 1-for-1." },
  { id: "px", t: "BOND PRICES", d: "Price ≈ inverse of yield. Duration converts a bp move into a mark-to-market P&L." },
  { id: "rt", t: "PORTFOLIO RETURNS", d: "Coupon carry plus price change. Hiking cycles can produce negative total returns even with positive yields." },
];

export default function Scenario() {
  const { mode } = useUI();
  const [fed, setFed] = useState(-100);
  const [rbi, setRbi] = useState(0);
  const [boe, setBoe] = useState(0);
  const [ecb, setEcb] = useState(0);
  const [inf, setInf] = useState(0);
  const [gr, setGr] = useState(0);
  const [risk, setRisk] = useState(0);
  const [out, setOut] = useState<ScenarioResp | null>(null);
  const [stage, setStage] = useState(STAGES[0]);
  const [shock, setShock] = useState<"hike25" | "hike50" | "cut25" | "cut50">("cut100" as never);

  useEffect(() => {
    api.scenario({ fed_bp: fed, rbi_bp: rbi, boe_bp: boe, ecb_bp: ecb, inflation_shock_pp: inf, growth_shock_pp: gr, risk_off: risk }).then(setOut);
  }, [fed, rbi, boe, ecb, inf, gr, risk]);

  const bars =
    out &&
    Object.entries(out.markets).map(([m, v]) => ({
      mkt: m,
      "2Y": v.d2_bp,
      "10Y": v.d10_bp,
      "30Y": v.d30_bp,
    }));

  return (
    <div className="space-y-6">
      <div>
        <Kicker>09 — Scenario lab</Kicker>
        <h1 className="font-serif text-3xl md:text-4xl mt-1">What if the Fed cuts 100 bp?</h1>
        <p className="text-sm text-amber-200/80 mt-1">ILLUSTRATIVE SCENARIO — NOT A FORECAST</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {[
          ["hike25", "Hike 25", 25],
          ["hike50", "Hike 50", 50],
          ["cut25", "Cut 25", -25],
          ["cut50", "Cut 50", -50],
          ["cut100", "Cut 100", -100],
        ].map(([id, lab, bp]) => (
          <button
            key={id}
            onClick={() => {
              setFed(bp as number);
              setShock(id as never);
            }}
            className={`px-3 py-1 rounded-full border text-xs ${fed === bp ? "border-cyan text-cyan" : "border-white/10"}`}
          >
            {lab}
          </button>
        ))}
        <span className="text-[11px] text-mist-600 self-center">Policy shock meter</span>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="panel rounded-2xl p-4 space-y-3">
          <Slider label="Fed (bp)" v={fed} set={setFed} min={-200} max={200} />
          <Slider label="RBI (bp)" v={rbi} set={setRbi} min={-200} max={200} />
          <Slider label="BoE (bp)" v={boe} set={setBoe} min={-200} max={200} />
          <Slider label="ECB (bp)" v={ecb} set={setEcb} min={-200} max={200} />
          <Slider label="Inflation shock (pp)" v={inf} set={setInf} min={-3} max={3} step={0.1} />
          <Slider label="Growth shock (pp)" v={gr} set={setGr} min={-3} max={3} step={0.1} />
          <Slider label="Risk-off (0–1)" v={risk} set={setRisk} min={0} max={1} step={0.05} />
        </div>
        <div className="panel rounded-2xl p-4">
          <div className="h-72">
            <ResponsiveContainer>
              <BarChart data={bars || []}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="mkt" tick={tick} />
                <YAxis tick={tick} />
                <Tooltip content={<Tip />} />
                <Legend />
                <Bar dataKey="2Y" fill="#22D3EE" />
                <Bar dataKey="10Y" fill="#C084FC" />
                <Bar dataKey="30Y" fill="#F472B6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {out && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {(Object.keys(out.markets) as Mkt[]).map((m) => {
            const v = out.markets[m];
            return (
              <div key={m} className="panel rounded-2xl p-4">
                <div className="kicker" style={{ color: MARKET_META[m].color }}>
                  {m}
                </div>
                <div className="text-sm mt-2">2Y {fmtBp(v.d2_bp)}</div>
                <div className="text-sm">10Y {fmtBp(v.d10_bp)}</div>
                <div className="text-sm">30Y {fmtBp(v.d30_bp)}</div>
                <div className="text-sm">Slope {fmtBp(v.slope_bp)}</div>
                <div className="text-sm">10Y TR ≈ {fmtPct(v.approx_10y_return_pct)}</div>
              </div>
            );
          })}
        </div>
      )}

      {out && (
        <ul className="text-xs text-mist-500 list-disc pl-5">
          {Object.entries(out.assumptions).map(([k, v]) => (
            <li key={k}>
              {k}: {v}
            </li>
          ))}
        </ul>
      )}

      <GlassCard>
        <Kicker>Policy transmission simulator</Kicker>
        <h3 className="font-serif text-xl mt-1">Click every stage of the chain</h3>
        <div className="flex flex-col gap-2 mt-4">
          {STAGES.map((s) => (
            <button
              key={s.id}
              onClick={() => setStage(s)}
              className={`text-left rounded-xl border px-3 py-2 ${stage.id === s.id ? "border-cyan/50 bg-cyan/5" : "border-white/10"}`}
            >
              <div className="kicker">{s.t}</div>
              {stage.id === s.id && <p className="text-sm text-mist-300 mt-1">{s.d}</p>}
            </button>
          ))}
        </div>
        {mode === "learn" && (
          <Learn title="How monetary policy reaches bond markets">
            1. Central bank changes the policy rate. 2. Money-market rates respond. 3. Investors revise expected future shorts. 4. Inflation and growth
            expectations adjust. 5. Longer yields move. 6. Bond prices move inversely. 7. Portfolio returns change. 8. Capital flows may transmit the
            shock across markets. None of those arrows is mechanical in every episode.
          </Learn>
        )}
      </GlassCard>
    </div>
  );
}

function Slider({
  label,
  v,
  set,
  min,
  max,
  step = 5,
}: {
  label: string;
  v: number;
  set: (n: number) => void;
  min: number;
  max: number;
  step?: number;
}) {
  return (
    <label className="block text-sm">
      <div className="flex justify-between text-mist-400">
        {label}
        <span className="num text-mist-50">{v}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={v} onChange={(e) => set(+e.target.value)} className="w-full" />
    </label>
  );
}
