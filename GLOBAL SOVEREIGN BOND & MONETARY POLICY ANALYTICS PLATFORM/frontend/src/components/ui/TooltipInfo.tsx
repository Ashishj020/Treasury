import { useState, type ReactNode } from "react";
import { HelpCircle } from "lucide-react";
import { findTerm } from "../../lib/glossary";

export function TooltipInfo({ term, children }: { term: string; children?: ReactNode }) {
  const [open, setOpen] = useState(false);
  const t = findTerm(term);
  return (
    <span className="relative inline-flex items-center gap-1">
      {children}
      <button
        type="button"
        aria-label={`Explain ${term}`}
        onClick={() => setOpen((v) => !v)}
        onBlur={() => setOpen(false)}
        className="text-mist-600 hover:text-cyan transition"
      >
        <HelpCircle size={12} />
      </button>
      {open && t && (
        <span className="absolute z-40 left-0 top-5 w-72 glass rounded-xl p-3 text-left shadow-glass">
          <span className="kicker">{t.term}</span>
          <p className="text-sm mt-1 text-mist-50">{t.definition}</p>
          <p className="text-xs mt-2 text-mist-400">
            <span className="text-cyan">WHY IT MATTERS. </span>
            {t.why}
          </p>
          {t.formula && <p className="text-[11px] mt-2 num text-orchid">{t.formula}</p>}
          <p className="text-xs mt-2 text-mist-400">
            <span className="text-emerald">EXAMPLE. </span>
            {t.example}
          </p>
        </span>
      )}
    </span>
  );
}
