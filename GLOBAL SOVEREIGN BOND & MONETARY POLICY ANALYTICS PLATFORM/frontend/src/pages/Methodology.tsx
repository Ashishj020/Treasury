import { api } from "../lib/api";
import { useFetch } from "../lib/useFetch";
import { Kicker, Learn, Skeleton } from "../components/ui/Card";

export default function Methodology() {
  const { data, loading } = useFetch(() => api.methodology(), []);
  if (loading) return <Skeleton className="h-96" />;
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <Kicker>11 — Methodology</Kicker>
        <h1 className="font-serif text-3xl md:text-4xl mt-1">How the numbers are made</h1>
        <p className="text-sm text-mist-400 mt-2">
          This page is the contract with the reader. If a chart looks clever, the formula that produced it should still be boring.
        </p>
      </div>
      {data &&
        Object.entries(data).map(([k, v]) => (
          <section key={k} className="panel rounded-2xl p-5">
            <div className="kicker">{k}</div>
            <p className="text-sm text-mist-200 mt-2 leading-relaxed">{v}</p>
          </section>
        ))}
      <section className="panel rounded-2xl p-5 space-y-3 text-sm text-mist-300">
        <div className="kicker">Formulas in words</div>
        <p>
          <b className="text-mist-50">Bond price.</b> Discount every coupon and the face value at the periodic yield. If the coupon equals the yield,
          the machine prices at par — that is why we start the return engine at par each day.
        </p>
        <p>
          <b className="text-mist-50">Modified duration.</b> D_mod = D_Mac / (1 + y/m). Economically: the percent price change for a one percentage
          point change in yield, ignoring convexity. m is payment frequency.
        </p>
        <p>
          <b className="text-mist-50">Convexity.</b> The curvature term. For a large parallel sell-off, duration alone overstates the price decline;
          convexity is why long bonds “hurt less than linear” on the way down and help more on the way up.
        </p>
        <p>
          <b className="text-mist-50">Event study.</b> Each path is measured as the yield minus the event-day yield, in bp. Averaging those paths is a
          description of this DEMO sample.
        </p>
        <p>
          <b className="text-mist-50">Cleaning.</b> Business-day calendar; last observation carried for policy steps; monthly last for macro. No
          interpolation across missing official prints because there are no official prints here.
        </p>
        <Learn title="Limitations worth repeating">
          Simulated data. Nelson-Siegel is interpolatory. OLS ignores HAC standard errors. Scenarios are linear elasticities. Term premium is
          conceptual. Eurozone = Bund benchmark, not a GDP-weighted euro sovereign.
        </Learn>
      </section>
    </div>
  );
}
