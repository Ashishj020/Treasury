export type Term = {
  term: string;
  definition: string;
  why: string;
  formula?: string;
  example: string;
  interpretation?: string;
};

export const GLOSSARY: Term[] = [
  { term: "Monetary policy", definition: "How a central bank sets the price and quantity of reserves to steer inflation and activity.", why: "It is the first link in the chain this lab studies: policy → short rates → curve → returns.", example: "The FOMC setting the federal funds target range." },
  { term: "Expansionary monetary policy", definition: "Easing: lower policy rates and/or asset purchases that add reserves.", why: "Tends to pull short-end yields down and, if credible, can also lower expected future short rates.", example: "March 2020 emergency cuts plus QE." },
  { term: "Contractionary monetary policy", definition: "Tightening: higher policy rates and/or runoff of the balance sheet.", why: "Usually lifts front-end yields and can flatten or invert the curve.", example: "The 2022–23 global hiking cycle." },
  { term: "Policy rate", definition: "The operational interest rate the central bank targets in the overnight market.", why: "It anchors money-market rates, which then price the short end of the sovereign curve.", example: "Fed funds upper bound, RBI repo, BoE Bank Rate, ECB deposit facility.", formula: "Often quoted as a target or a corridor, not a market yield." },
  { term: "Central bank", definition: "The public institution that issues the currency and operates monetary policy.", why: "Its reaction function is what bond investors spend their lives inferring.", example: "Fed, RBI, BoE, ECB in this lab." },
  { term: "Sovereign bond", definition: "A debt security issued by a national government (or, for EZ, the German Bund benchmark here).", why: "It is the risk-free (or near risk-free local-currency) building block of every local yield curve.", example: "A 10-year U.S. Treasury note." },
  { term: "Bond yield", definition: "The discount rate that equates the bond’s remaining cash flows to its price.", why: "Yield is the language of rates markets; price is what portfolios actually mark.", example: "A 10Y trading at 4.21% yield.", formula: "P = Σ CF_t / (1+y/m)^{mt}" },
  { term: "Bond price", definition: "Present value of promised coupons and principal.", why: "Duration and convexity describe how this price moves when y moves.", example: "A par bond prices at 100 when coupon = yield." },
  { term: "Coupon", definition: "The contractual interest paid by the bond, usually semi-annually.", why: "Coupon return is the carry piece of total return.", example: "A 4% coupon on 100 face pays 2 every six months." },
  { term: "Maturity", definition: "The date principal is repaid. Tenor is time left to that date.", why: "Different maturities load differently on policy vs term premium.", example: "2Y is policy-sensitive; 30Y is duration- and premium-sensitive." },
  { term: "Duration", definition: "Macaulay duration: present-value-weighted average maturity of cash flows, in years.", why: "It is the first-order sensitivity of the bond to a parallel yield shift.", formula: "D_Mac = Σ t·PV(CF_t) / P", example: "A 10Y par coupon bond has Mac duration a bit below 10." },
  { term: "Modified duration", definition: "Percentage price change for a 1 percentage-point yield change, to first order.", why: "Portfolio managers quote risk in modified duration.", formula: "D_mod = D_Mac / (1 + y/m)", example: "D_mod = 8 means +100 bp in yield ≈ −8% in price (linear)." },
  { term: "Convexity", definition: "Second derivative of price with respect to yield, scaled by 1/P.", why: "It measures how duration itself changes; long bonds have more convexity.", formula: "C = (1/P) d²P/dy²", example: "For a large sell-off, actual price falls less than duration predicts." },
  { term: "Yield curve", definition: "Yields plotted against maturity at a point in time.", why: "Its shape is a compressed statement about path-of-policy, inflation and term premium.", example: "3M through 30Y in the Curve Lab." },
  { term: "Yield-curve steepening", definition: "Longer yields rise relative to shorter yields (2s10s widens).", why: "Often associated with easing, fiscal supply, or rising growth/inflation expectations.", example: "Bull steepener: short end falls more than the long end." },
  { term: "Yield-curve flattening", definition: "The gap between long and short yields compresses.", why: "Classic late-cycle hiking pattern: front end catches up with (or overshoots) the long end.", example: "Bear flattener: 2Y up more than 10Y." },
  { term: "Inversion", definition: "Shorter yields above longer yields. In this lab: 10Y−2Y < −15 bp.", why: "Historically a recession warning in the U.S.; it is a slope observation, not a forecast.", example: "UST 2s10s in 2022–23." },
  { term: "Term premium", definition: "Extra yield investors require to hold duration rather than rolling shorts.", why: "It is the piece of the 10Y that is not just expected future short rates. It is not directly observed.", formula: "10Y ≈ expected avg short rates + term premium  (conceptual)", example: "QE is often argued to compress term premium." },
  { term: "Inflation expectations", definition: "The path of prices markets (or surveys) think will arrive.", why: "They enter both expected short rates (via the reaction function) and term premia.", example: "5Y5Y forward inflation swaps." },
  { term: "Real interest rate", definition: "Nominal rate minus expected inflation (Fisher).", why: "Sovereign nominal yields mix real rates and inflation compensation.", formula: "i ≈ r + π^e", example: "TIPS yields are a U.S. real-rate proxy — not in this DEMO set." },
  { term: "Quantitative easing", definition: "Large-scale asset purchases that expand the central-bank balance sheet.", why: "The intended channel is duration extraction / term-premium compression, plus signalling.", example: "PSPP at the ECB; UST+MBS QE at the Fed." },
  { term: "Quantitative tightening", definition: "Allowing the balance sheet to shrink (runoff) or selling assets.", why: "The opposite duration-supply shock — empirically much less cleanly identified than QE.", example: "Fed runoff from June 2022." },
  { term: "Forward guidance", definition: "Communication about the likely future path of the policy rate.", why: "It can move 2Y–5Y yields without a change in the current target.", example: "'Higher for longer' in 2023." },
  { term: "Benchmark yield", definition: "The on-the-run or par-curve yield used as the market’s reference.", why: "Spreads, duration hedges and textbook charts all hang off a benchmark.", example: "This lab uses simulated par curves, not a specific CUSIP." },
  { term: "Credit spread", definition: "Yield of a riskier bond minus the sovereign benchmark of similar duration.", why: "Sovereigns in this lab are the benchmark; credit is mentioned so the concept is not confused with slope.", example: "A corporate 10Y at 5.2% vs UST 10Y 4.2% is +100 bp." },
  { term: "Volatility", definition: "Dispersion of changes — here, annualised standard deviation.", why: "Hiking cycles usually lift yield vol; QE often crushed it.", formula: "σ_ann = σ_daily × √252", example: "90-day realised vol of 10Y yield changes." },
  { term: "Correlation", definition: "Standardised covariance, between −1 and 1.", why: "High US–India 10Y correlation is an observed co-movement, not a structural proof of spillover.", formula: "ρ = Cov(x,y) / (σx σy)", example: "90-day rolling ρ of daily yield changes." },
  { term: "Covariance", definition: "Expected product of demeaned moves.", why: "Beta and correlation are built from it.", formula: "Cov(x,y) = E[(x−μx)(y−μy)]" , example: "Used in the rolling-beta chart." },
  { term: "Beta", definition: "OLS slope of one series on another.", why: "A India-on-US 10Y beta of 0.4 means a 10 bp UST move historically lined up with ~4 bp in G-Secs, in sample.", formula: "β = Cov(y,x) / Var(x)", example: "Rolling 90-day beta of ΔIN10Y on ΔUS10Y." },
  { term: "Basis point", definition: "One hundredth of a percentage point.", why: "Rates traders think in bp, not in 'percent'.", formula: "1 bp = 0.01 percentage point = 0.0001 in decimal", example: "6.20% → 6.45% is +25 bp." },
  { term: "Total return", definition: "Price return plus coupon (carry) over the holding period.", why: "Yields can rise and a coupon bond can still earn positive total return if carry offsets mark-to-market.", formula: "TR = (P1 − P0 + coupon) / P0", example: "Constant-maturity 10Y TR in the Returns page." },
  { term: "Excess return", definition: "Total return minus a financing / cash rate.", why: "Duration risk should be judged after the risk-free carry.", example: "Here we subtract a simple local policy-rate proxy when shown." },
  { term: "Rolling return", definition: "Return computed on a moving window (12M, 3Y).", why: "Stops a single start-date from dominating the story.", example: "Trailing 12-month 10Y TR." },
  { term: "Rolling volatility", definition: "Standard deviation on a moving window, usually annualised.", why: "Regime-dependent: 2020 and 2022 look nothing like 2017.", example: "60-day realised vol." },
  { term: "Drawdown", definition: "Peak-to-trough decline of a cumulative wealth index.", why: "Hiking cycles produced historically large drawdowns in long bonds in 2022.", formula: "DD_t = W_t / max_{s≤t} W_s − 1", example: "Max drawdown on the Returns page." },
  { term: "Recession", definition: "A broad, persistent contraction in activity. NBER-style, not two negative GDP prints by themselves.", why: "Curve inversion is a statistical warning, not a dating committee.", example: "This DEMO set plants a COVID collapse, not a 2022 NBER recession." },
  { term: "Inflation", definition: "The rate of change of a consumer-price index, usually y/y.", why: "It is the mandate variable that most clearly moved 2021–23 policy.", example: "Simulated CPI y/y on Macro Drivers." },
  { term: "GDP growth", definition: "Real output growth.", why: "Stronger growth usually lifts real rates and steepens, all else equal.", example: "Monthly interpolated DEMO GDP y/y." },
  { term: "Unemployment", definition: "Share of the labour force without work, looking for work.", why: "A dual-mandate input for the Fed; a slack variable everywhere.", example: "COVID spike in the U.S. DEMO series." },
  { term: "Policy transmission", definition: "The chain from the policy instrument to yields, credit, FX, and spending.", why: "This entire application is a map of the rates piece of that chain.", example: "See the transmission diagram on Scenario Lab." },
  { term: "Cross-market transmission", definition: "How a shock in one sovereign curve shows up in another.", why: "USD discount-rate, dollar funding, and risk sentiment are the usual suspects. Correlation ≠ causation.", example: "Fed hikes and India 10Y in the lag explorer." },
];

export function findTerm(q: string) {
  const s = q.toLowerCase();
  return GLOSSARY.find((t) => t.term.toLowerCase() === s) || GLOSSARY.find((t) => t.term.toLowerCase().includes(s));
}
