# LIQUIDITY → CONTROL

**Global Corporate Liquidity & Cash Management Optimization**

Simulated treasury lab for **Orion Global Industries**, a fictional multinational with operating companies in India, the United States, the United Kingdom and Singapore.

All figures are **SIMULATED CORPORATE TREASURY DATA**. They are not real company results.

The book covers January 2024 – December 2026, more than ₹500 Cr of simulated annual cash flow, and a calculated idle-cash reduction near **12%** under hybrid cash pooling plus short-term deployment. That 12% is a model output, not an assumed constant.

## Run locally

```bash
# backend
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8765

# frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The Vite proxy forwards `/api` to FastAPI on port 8765.

## Tests

```bash
cd backend
python -m pytest -q
```

## What the lab answers

- Where is the cash?
- How much is idle?
- Where do we need to borrow?
- Would pooling help Singapore without stranding India surplus?
- What happens if USD/INR moves 10%?
- Which structure scores best if you care more about liquidity than return?

Not financial, legal or tax advice. Simplified project-model formulas — see **Methodology** in the app.
