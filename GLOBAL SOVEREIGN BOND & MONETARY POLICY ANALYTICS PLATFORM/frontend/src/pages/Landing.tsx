import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { MARKET_META, MARKETS } from "../lib/format";

const mini = [
  [1.2, 1.4, 1.1, 1.6, 2.1, 2.8, 3.4, 4.2, 3.9, 3.6],
  [7.2, 7.0, 6.4, 6.1, 5.8, 7.1, 7.3, 6.9, 6.6, 6.4],
  [1.5, 1.2, 0.6, 0.4, 0.9, 2.4, 4.1, 4.4, 4.0, 3.8],
  [0.4, 0.1, -0.2, -0.4, 0.2, 1.6, 2.6, 2.4, 2.2, 2.1],
];

export default function Landing() {
  const nav = useNavigate();
  return (
    <div className="bg-lab grain min-h-screen relative overflow-hidden">
      <div className="relative z-10 max-w-6xl mx-auto px-6 py-10 md:py-16">
        <div className="flex items-center justify-between text-[11px] text-mist-400">
          <span className="font-serif text-mist-200">POLICY → YIELDS</span>
          <span className="num tracking-[0.2em]">DEMO DATA · US · IN · UK · EZ</span>
        </div>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }} className="mt-20 md:mt-28">
          <div className="kicker">Global sovereign bond market lab</div>
          <h1 className="font-serif text-5xl md:text-7xl mt-4 leading-[0.95] max-w-4xl">
            Explore how monetary policy moves through global fixed-income markets.
          </h1>
          <p className="mt-6 max-w-xl text-mist-400 text-lg">
            A student-built research terminal: policy rates, yield curves, event studies, and cross-market transmission — with every formula shown.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button
              onClick={() => nav("/lab/overview")}
              className="px-5 py-3 rounded-full bg-cyan text-ink-0 text-sm font-medium hover:bg-white transition"
            >
              Enter Market Lab
            </button>
            <button onClick={() => nav("/lab/methodology")} className="px-5 py-3 rounded-full border border-white/15 text-sm text-mist-200">
              Read the methodology
            </button>
          </div>
        </motion.div>

        <div className="mt-20 grid md:grid-cols-4 gap-3">
          {MARKETS.map((m, i) => (
            <button
              key={m}
              onClick={() => nav("/lab/curves")}
              className="panel rounded-2xl p-4 text-left hover:border-cyan/30 transition"
            >
              <div className="kicker" style={{ color: MARKET_META[m].color }}>
                {MARKET_META[m].short}
              </div>
              <div className="font-serif text-lg mt-1">{MARKET_META[m].name}</div>
              <svg viewBox="0 0 100 36" className="mt-3 w-full h-12">
                <polyline
                  fill="none"
                  stroke={MARKET_META[m].color}
                  strokeWidth="1.6"
                  points={mini[i]
                    .map((v, j) => `${(j / 9) * 100},${32 - ((v - Math.min(...mini[i])) / (Math.max(...mini[i]) - Math.min(...mini[i]))) * 26}`)
                    .join(" ")}
                />
              </svg>
              <div className="text-[11px] text-mist-600 mt-1">Simulated par curve · click to open Curve Lab</div>
            </button>
          ))}
        </div>

        <div className="mt-16 grid md:grid-cols-3 gap-6 text-sm text-mist-400">
          <div>
            <div className="kicker text-cyan">RESEARCH QUESTION</div>
            <p className="mt-2">How do policy-rate changes move sovereign yields, curves, volatility, term premia, and cross-market co-movement?</p>
          </div>
          <div>
            <div className="kicker text-orchid">NOT A FORECAST</div>
            <p className="mt-2">DEMO series are historically inspired, not official prints. Insights are sample observations with limitations stated.</p>
          </div>
          <div>
            <div className="kicker text-emerald">STACK</div>
            <p className="mt-2">React · FastAPI · Nelson-Siegel curves · OLS · event studies · duration/convexity closed form.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
