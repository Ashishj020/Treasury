import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { Mkt } from "./format";

type Mode = "analyst" | "learn";

type Ctx = {
  market: Mkt;
  setMarket: (m: Mkt) => void;
  range: string;
  setRange: (r: string) => void;
  frequency: string;
  setFrequency: (f: string) => void;
  mode: Mode;
  setMode: (m: Mode) => void;
  commandOpen: boolean;
  setCommandOpen: (v: boolean) => void;
};

const C = createContext<Ctx | null>(null);

export function UIProvider({ children }: { children: ReactNode }) {
  const [market, setMarket] = useState<Mkt>("US");
  const [range, setRange] = useState("5Y");
  const [frequency, setFrequency] = useState("daily");
  const [mode, setMode] = useState<Mode>("learn");
  const [commandOpen, setCommandOpen] = useState(false);
  const value = useMemo(
    () => ({ market, setMarket, range, setRange, frequency, setFrequency, mode, setMode, commandOpen, setCommandOpen }),
    [market, range, frequency, mode, commandOpen],
  );
  return <C.Provider value={value}>{children}</C.Provider>;
}

export function useUI() {
  const v = useContext(C);
  if (!v) throw new Error("useUI outside provider");
  return v;
}
