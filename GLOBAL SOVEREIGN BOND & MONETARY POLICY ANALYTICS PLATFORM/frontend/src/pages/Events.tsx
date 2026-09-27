import { useState } from "react";
import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { useUI } from "../lib/store";
import { ErrorState, Kicker, Learn, Skeleton, EmptyState } from "../components/ui/Card";
import { fmtBp, fmtNum } from "../lib/format";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Tip,
  tick,
} from "../components/charts/Chart";

export default function Events() {
  const { mode } = useUI();
  const [cb, setCb] = useState("FED");
  const [type, setType] = useState("HIKE");
  const [window, setWindow] = useState(10);
  const { data, error, loading } = useFetch(() => api.eventStudy(cb, type, window), [cb, type, window]);

  return (
    <div className="space-y-6">
      <div>
        <Kicker>05 — Event study engine</Kicker>
        <h1 className="font-serif text-3xl md:text-4xl mt-1">Average 10Y path around policy shocks</h1>
      </div>
      <div className="flex flex-wrap gap-2">
        {["FED", "RBI", "BOE", "ECB"].map((x) => (
          <button key={x} onClick={() => setCb(x)} className={`px-3 py-1 rounded-full border text-xs ${cb === x ? "border-cyan text-cyan" : "border-white/10"}`}>
            {x}
          </button>
        ))}
        {["HIKE", "CUT", "HOLD", "QE", "QT"].map((x) => (
          <button key={x} onClick={() => setType(x)} className={`px-3 py-1 rounded-full border text-xs ${type === x ? "border-orchid text-orchid" : "border-white/10"}`}>
            {x}
          </button>
        ))}
        {[1, 5, 10, 30].map((w) => (
          <button key={w} onClick={() => setWindow(w)} className={`px-3 py-1 rounded-full border text-xs num ${window === w ? "border-emerald text-emerald" : "border-white/10"}`}>
            [{-w}, +{w}]
          </button>
        ))}
      </div>

      {loading && <Skeleton className="h-80" />}
      {error && <ErrorState message={error} />}
      {data && !data.ok && <EmptyState title={data.error || "No events"} hint="Try another event type, or expand the window." />}
      {data?.ok && data.points && (
        <>
          <div className="grid sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <Stat k="Events" v={String(data.n)} />
            <Stat k="Avg terminal" v={fmtBp(data.avg_terminal_bp)} />
            <Stat k="Median terminal" v={fmtBp(data.median_terminal_bp)} />
            <Stat k="Max increase" v={fmtBp(data.max_increase_bp)} />
            <Stat k="Max decrease" v={fmtBp(data.max_decrease_bp)} />
            <Stat k="Vol pre → post" v={`${fmtNum(data.vol_pre_bp, 1)} → ${fmtNum(data.vol_post_bp, 1)}`} />
          </div>
          <div className="panel rounded-2xl p-4">
            <div className="h-[360px]">
              <ResponsiveContainer>
                <ComposedChart data={data.points}>
                  <CartesianGrid vertical={false} />
                  <XAxis dataKey="day" tick={tick} />
                  <YAxis tick={tick} unit=" bp" />
                  <Tooltip content={<Tip />} />
                  <Area dataKey="p75_bp" stroke="none" fill="#22D3EE22" />
                  <Area dataKey="p25_bp" stroke="none" fill="#07090D" />
                  <Line dataKey="mean_bp" name="Mean bp" stroke="#22D3EE" strokeWidth={2} dot={false} />
                  <Line dataKey="median_bp" name="Median" stroke="#C084FC" strokeDasharray="4 4" dot={false} />
                  <ReferenceLine x={-1} stroke="#8B95A5" strokeDasharray="2 2" />
                  <ReferenceLine x={0} stroke="#F472B6" />
                  <ReferenceLine x={1} stroke="#8B95A5" strokeDasharray="2 2" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-mist-600 mt-2">Highlighted: T−1, T, T+1. Band is p25–p75 of event paths.</p>
          </div>
          {mode === "learn" && (
            <Learn title="Event-study methodology">
              {data.methodology} Paths that do not have a full window on both sides are dropped. DEMO waypoints are sparse — n will be small. Do not
              read a 3-event average as a structural impulse response.
            </Learn>
          )}
        </>
      )}
    </div>
  );
}

function Stat({ k, v }: { k: string; v: string }) {
  return (
    <div className="panel rounded-xl p-3">
      <div className="kicker">{k}</div>
      <div className="num text-lg mt-1">{v}</div>
    </div>
  );
}
