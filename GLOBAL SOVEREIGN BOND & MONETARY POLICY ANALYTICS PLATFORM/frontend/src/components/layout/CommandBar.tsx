import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUI } from "../../lib/store";
import { GLOSSARY } from "../../lib/glossary";

const PAGES = [
  { q: "US 10Y", to: "/lab/overview" },
  { q: "India 2Y", to: "/lab/curves" },
  { q: "Fed hikes 2022", to: "/lab/events" },
  { q: "UK yield curve", to: "/lab/curves" },
  { q: "Eurozone inversion", to: "/lab/curves" },
  { q: "event study", to: "/lab/events" },
  { q: "regression", to: "/lab/macro" },
  { q: "scenario", to: "/lab/scenario" },
  { q: "duration", to: "/lab/returns" },
  { q: "correlation", to: "/lab/cross" },
  { q: "methodology", to: "/lab/methodology" },
  { q: "data sources", to: "/lab/sources" },
  { q: "monetary policy", to: "/lab/policy" },
  { q: "bond returns", to: "/lab/returns" },
  { q: "volatility", to: "/lab/risk" },
];

export function CommandBar() {
  const { commandOpen, setCommandOpen } = useUI();
  const [q, setQ] = useState("");
  const nav = useNavigate();

  const results = useMemo(() => {
    const s = q.toLowerCase();
    const pages = PAGES.filter((p) => p.q.toLowerCase().includes(s) || !s);
    const terms = GLOSSARY.filter((t) => t.term.toLowerCase().includes(s)).slice(0, 6);
    return { pages: pages.slice(0, 8), terms };
  }, [q]);

  useEffect(() => {
    if (!commandOpen) setQ("");
  }, [commandOpen]);

  if (!commandOpen) return null;
  return (
    <div className="fixed inset-0 z-[60] bg-black/55 backdrop-blur-sm flex items-start justify-center pt-[12vh]" onClick={() => setCommandOpen(false)}>
      <div className="w-[min(640px,92vw)] glass rounded-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <input
          autoFocus
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search markets, maturities, policy events…"
          className="w-full bg-transparent px-4 py-4 outline-none text-sm border-b border-white/10"
        />
        <div className="max-h-80 overflow-y-auto p-2">
          <div className="kicker px-2 py-1">Navigate</div>
          {results.pages.map((p) => (
            <button
              key={p.q}
              className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/[0.05] text-sm"
              onClick={() => {
                nav(p.to);
                setCommandOpen(false);
              }}
            >
              {p.q}
            </button>
          ))}
          {results.terms.length > 0 && (
            <>
              <div className="kicker px-2 py-1 mt-2">Glossary</div>
              {results.terms.map((t) => (
                <div key={t.term} className="px-3 py-2">
                  <div className="text-sm text-cyan">{t.term}</div>
                  <div className="text-xs text-mist-400">{t.definition}</div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
