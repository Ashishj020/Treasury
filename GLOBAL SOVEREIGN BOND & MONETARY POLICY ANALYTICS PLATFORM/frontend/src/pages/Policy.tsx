import { useMemo, useState } from "react";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { MARKET_META, type Mkt, fmtBp, fmtPct } from "../lib/format";
import { ErrorState, GlassCard, Kicker, Learn, Skeleton } from "../components/ui/Card";
import { useUI } from "../lib/store";

export default function PolicyPage() {
  const { mode } = useUI();
  const { data, error, loading } = useFetch(() => api.events(), []);
  const [sel, setSel] = useState<number | null>(null);
  const chosen = data?.policy.find((p) => p.id === sel);

  const cols = useMemo(() => {
    const grouped: Record<string, NonNullable<typeof data>["policy"]> = { FED: [], RBI: [], BOE: [], ECB: [] };
    data?.policy.forEach((e) => {
      (grouped[e.cb] ||= []).push(e);
    });
    return grouped;
  }, [data]);

  if (loading) return <Skeleton className="h-[70vh]" />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-6">
      <div>
        <Kicker>02 — Monetary policy</Kicker>
        <h1 className="font-serif text-3xl md:text-4xl mt-1">Decision timeline</h1>
        <p className="text-sm text-mist-400 mt-1">SIMULATED DATA. Cards are stylised meeting notes, not official minutes.</p>
      </div>

      <div className="grid md:grid-cols-4 gap-3">
        {(["FED", "RBI", "BOE", "ECB"] as const).map((cb) => (
          <div key={cb}>
            <div className="kicker mb-2">{cb}</div>
            <div className="space-y-2">
              {(cols[cb] || []).map((e) => (
                <button
                  key={e.id}
                  onClick={() => setSel(e.id)}
                  className={`w-full text-left panel rounded-xl p-3 hover:border-cyan/30 ${sel === e.id ? "border-cyan/40" : ""}`}
                >
                  <div className="num text-[11px] text-mist-400">{e.date}</div>
                  <div className="text-sm mt-1">{e.decision}</div>
                  <div className={`num text-xs ${e.change_bp < 0 ? "text-emerald" : e.change_bp > 0 ? "text-[#FB7185]" : "text-mist-400"}`}>
                    {fmtBp(e.change_bp)} · {fmtPct(e.policy_rate)}
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {chosen && (
        <GlassCard>
          <div className="kicker">Market reaction</div>
          <h3 className="font-serif text-2xl mt-1">
            {chosen.cb} · {chosen.date}
          </h3>
          <p className="text-sm text-mist-400 mt-2">{chosen.rationale}</p>
          <table className="mt-4 w-full text-sm">
            <thead className="text-[11px] text-mist-600">
              <tr>
                <th />
                <th className="text-left">2Y</th>
                <th className="text-left">10Y</th>
                <th className="text-left">30Y</th>
              </tr>
            </thead>
            <tbody>
              {(["before", "event", "after"] as const).map((k) => (
                <tr key={k} className="border-t border-white/5">
                  <td className="py-2 capitalize text-mist-400">{k}</td>
                  {(["2Y", "10Y", "30Y"] as const).map((m) => (
                    <td key={m} className="num">
                      {chosen[k][m] == null ? "—" : fmtPct(chosen[k][m] as number)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {mode === "learn" && (
            <Learn title="How to read a reaction">
              “Before” is ~5 sessions earlier, “after” ~5 later. A hike that lifts 2Y more than 30Y is a classic bear-flattening. This is not an
              identified impulse response.
            </Learn>
          )}
        </GlassCard>
      )}

      <RegimeBlock />
    </div>
  );
}

function RegimeBlock() {
  const [m, setM] = useState<Mkt>("US");
  const { data } = useFetch(() => api.regimes(m), [m]);
  return (
    <div className="panel rounded-2xl p-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="kicker">Policy cycle analyzer</div>
          <h3 className="font-serif text-xl">Average market behaviour by regime</h3>
        </div>
        <select value={m} onChange={(e) => setM(e.target.value as Mkt)} className="bg-ink-2 border border-white/10 rounded-lg text-xs px-2 py-1">
          {Object.keys(MARKET_META).map((k) => (
            <option key={k}>{k}</option>
          ))}
        </select>
      </div>
      <p className="text-xs text-mist-600 mt-2">{data?.rule}</p>
      <div className="grid md:grid-cols-3 gap-3 mt-4">
        {data?.regimes.map((r) => (
          <div key={r.regime} className="rounded-xl border border-white/10 p-3">
            <div className="kicker">{r.regime}</div>
            <div className="num text-xs mt-2 text-mist-400">n = {r.n} sessions</div>
            <div className="mt-2 text-sm">Avg 2Y {fmtPct(r.avg_2y)}</div>
            <div className="text-sm">Avg 10Y {fmtPct(r.avg_10y)}</div>
            <div className="text-sm">Vol {fmtPct(r.avg_vol * 100, 1)}</div>
            <div className="text-sm">Ann. TR {fmtPct(r.avg_return_ann * 100, 1)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
