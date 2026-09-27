import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { ErrorState, Kicker, Skeleton } from "../components/ui/Card";

export default function Sources() {
  const src = useFetch(() => api.sources(), []);
  const st = useFetch(() => api.status(), []);
  if (src.loading || st.loading) return <Skeleton className="h-96" />;
  if (src.error) return <ErrorState message={src.error} />;
  return (
    <div className="space-y-6">
      <div>
        <Kicker>12 — Data sources</Kicker>
        <h1 className="font-serif text-3xl md:text-4xl mt-1">Where the series claim to come from</h1>
        <p className="text-sm text-amber-200/80 mt-2">{st.data?.disclaimer}</p>
      </div>
      <div className="panel rounded-2xl p-4">
        <div className="kicker">Data status</div>
        <div className="mt-3 space-y-2">
          {st.data?.items.map((i) => (
            <div key={i.market} className="flex flex-wrap justify-between text-sm border-b border-white/5 py-2">
              <span>
                {i.market} · {i.source}
              </span>
              <span className="num text-emerald">
                ● {i.status} · {i.observations.toLocaleString()} obs · {i.last_updated}
              </span>
            </div>
          ))}
        </div>
        <p className="text-xs text-mist-600 mt-3">{st.data?.label}. Last updated {st.data?.last_updated}.</p>
      </div>
      {src.data?.map((s) => (
        <article key={s.code} className="panel rounded-2xl p-5 space-y-1">
          <div className="kicker">{s.code}</div>
          <h3 className="font-serif text-xl">{s.name}</h3>
          <p className="text-sm text-mist-300">{s.institution}</p>
          <dl className="grid md:grid-cols-2 gap-2 text-sm mt-3">
            <Row k="Variable" v={s.variable} />
            <Row k="Frequency" v={s.frequency} />
            <Row k="Date range" v={s.date_range} />
            <Row k="Transformation" v={s.transformation} />
          </dl>
          <p className="text-sm text-mist-400 mt-2">{s.methodology}</p>
          <a className="text-xs text-cyan" href={s.url} target="_blank" rel="noreferrer">
            Real-world home of the inspiration →
          </a>
        </article>
      ))}
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <div className="kicker">{k}</div>
      <div className="text-mist-200">{v}</div>
    </div>
  );
}
