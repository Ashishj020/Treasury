import { motion } from "framer-motion";
import { Link } from "react-router-dom";

const NODES = [
  { id: "UK", x: 48, y: 28, r: 18, label: "United Kingdom", cash: "Buffer Builder", color: "#6366F1" },
  { id: "IN", x: 68, y: 48, r: 26, label: "India", cash: "Cash Rich", color: "#22D3EE" },
  { id: "US", x: 22, y: 42, r: 20, label: "United States", cash: "Always Moving", color: "#34D399" },
  { id: "SG", x: 78, y: 62, r: 14, label: "Singapore", cash: "Efficient but Tight", color: "#F472B6" },
];

export function Landing() {
  return (
    <div className="mesh relative min-h-screen overflow-hidden">
      <div className="grid-bg min-h-screen">
        <div className="noise" />
        <header className="relative z-10 flex items-center justify-between px-6 py-6 lg:px-12">
          <div>
            <div className="font-display text-xs tracking-[0.32em] text-cyan">LIQUIDITY → CONTROL</div>
            <div className="mt-1 text-[10px] uppercase tracking-[0.2em] text-faint">Orion Global Industries · London</div>
          </div>
          <div className="text-[10px] uppercase tracking-[0.18em] text-mute">Simulated corporate treasury data</div>
        </header>

        <main className="relative z-10 mx-auto grid max-w-6xl gap-12 px-6 pb-24 pt-8 lg:grid-cols-[1.1fr_0.9fr] lg:px-12 lg:pt-16">
          <div>
            <p className="text-[11px] uppercase tracking-[0.28em] text-faint">
              Global corporate liquidity & cash management lab
            </p>
            <h1 className="font-display mt-5 max-w-xl text-5xl leading-[1.05] tracking-tight text-ink md:text-6xl">
              Four countries.
              <br />
              Four currencies.
              <br />
              <span className="text-cyan">One treasury question.</span>
            </h1>
            <p className="mt-6 max-w-md text-lg text-mute">Where should the company’s cash go?</p>
            <p className="mt-4 max-w-lg text-sm leading-relaxed text-faint">
              Built a multi-currency liquidity model across India, the US, the UK and Singapore, analyzing ₹500Cr+ simulated
              cash flows and identifying a calculated idle-cash reduction near 12% through cash-pooling and short-term
              investment strategies.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/overview"
                className="rounded-full bg-cyan px-6 py-3 text-sm font-semibold text-bg transition hover:shadow-glow"
              >
                Enter treasury lab
              </Link>
              <Link to="/methodology" className="rounded-full border border-white/15 px-6 py-3 text-sm text-mute">
                Read the method
              </Link>
            </div>
            <div className="mt-10 grid grid-cols-2 gap-4 text-[12px] text-mute md:grid-cols-4">
              {NODES.map((n) => (
                <div key={n.id} className="border-t border-white/10 pt-3">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-faint">{n.id}</div>
                  <div className="mt-1 text-ink">{n.label}</div>
                  <div className="text-[11px]">{n.cash}</div>
                </div>
              ))}
            </div>
          </div>

          <motion.svg
            viewBox="0 0 100 80"
            className="h-[420px] w-full"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            aria-label="Four-country cash map"
          >
            <defs>
              <filter id="soft">
                <feGaussianBlur stdDeviation="1.2" />
              </filter>
            </defs>
            {NODES.map((a, i) =>
              NODES.slice(i + 1).map((b) => (
                <motion.line
                  key={a.id + b.id}
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  stroke="rgba(34,211,238,0.18)"
                  strokeWidth="0.3"
                  strokeDasharray="1 1.4"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 2, delay: 0.4 }}
                />
              ))
            )}
            {NODES.map((n, i) => (
              <g key={n.id}>
                <motion.circle
                  cx={n.x}
                  cy={n.y}
                  r={n.r}
                  fill={n.color}
                  fillOpacity={0.12}
                  stroke={n.color}
                  strokeWidth="0.4"
                  animate={{ r: [n.r, n.r + 1.4, n.r] }}
                  transition={{ duration: 3.6 + i, repeat: Infinity }}
                />
                <circle cx={n.x} cy={n.y} r={2.2} fill={n.color} />
                <text x={n.x} y={n.y - n.r - 2} textAnchor="middle" fontSize="3.2" fill="#F5F7FA">
                  {n.id}
                </text>
              </g>
            ))}
          </motion.svg>
        </main>
      </div>
    </div>
  );
}
