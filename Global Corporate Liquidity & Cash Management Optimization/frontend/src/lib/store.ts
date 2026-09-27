import { create } from "zustand";
import type { CountryCode, Reporting, Scenario, Strategy } from "./format";

type State = {
  reporting: Reporting;
  scenario: Scenario;
  strategy: Strategy;
  country: CountryCode;
  learning: boolean;
  dismissed: string[];
  setReporting: (v: Reporting) => void;
  setScenario: (v: Scenario) => void;
  setStrategy: (v: Strategy) => void;
  setCountry: (v: CountryCode) => void;
  setLearning: (v: boolean) => void;
  dismiss: (id: string) => void;
};

export const useTreasury = create<State>((set) => ({
  reporting: "INR",
  scenario: "base",
  strategy: "none",
  country: "ALL",
  learning: false,
  dismissed: [],
  setReporting: (reporting) => set({ reporting }),
  setScenario: (scenario) => set({ scenario }),
  setStrategy: (strategy) => set({ strategy }),
  setCountry: (country) => set({ country }),
  setLearning: (learning) => set({ learning }),
  dismiss: (id) => set((s) => ({ dismissed: [...s.dismissed, id] })),
}));

export function filters() {
  const s = useTreasury.getState();
  return { reporting: s.reporting, scenario: s.scenario, strategy: s.strategy, country: s.country };
}
