# bess_calc

> Turn a utility bill PDF into a defensible BESS + solar investment case — in seconds.

🌏 [中文版 / Chinese version](./README.zh.md)  ·  📋 [Update log](./UPDATES.md)

**Live demo:** https://besscalc-production.up.railway.app
**Frontend:** https://react-solar-battery-b4ez.bolt.host

---

## The problem

In commercial & industrial battery storage sales, the first conversation with a prospect almost always starts the same way: *"How much would I save?"* Answering that well takes reading a dense utility bill, decomposing the rate structure, estimating demand-charge reduction, modeling peak-valley arbitrage, stacking incentives (SGIP, ITC), and producing payback + NPV. BD reps do this in spreadsheets, one bill at a time, often taking 30+ minutes per lead.

This tool compresses that preliminary ROI estimate (the "Stage 1" pre-feasibility step that BD owns, before detailed engineering takes over) into a single PDF upload.

## What it does

1. **Upload a utility bill PDF** (currently supports commercial/industrial bills; residential is detected and politely rejected — the economics are fundamentally different and out of scope)
2. **Parses the bill with a vision LLM** — pulls out utility name, rate schedule, max demand (kW), peak/off-peak kWh, demand charges, energy charges
3. **Runs three ROI scenarios** — storage-only, solar-only, and combined solar+storage
4. **Returns** net install cost (after SGIP + federal ITC), annual savings, simple payback, and 10-year NPV

Validated end-to-end on a real California C&I utility bill under the PG&E B19S + Ava Community Energy rate structure.

## Architecture

```
PDF upload (React / Bolt frontend)
        │
        ▼
FastAPI /analyze endpoint (Python, Railway)
        │
        ├── pdfplumber ──▶ raw text
        │
        ├── Moonshot Kimi (moonshot-v1-32k) ──▶ structured bill dict
        │                                       {utility, rate_schedule,
        │                                        max_demand_kw, peak_kwh, ...}
        │
        ├── classify_customer() ──▶ commercial / residential / unclear
        │       (residential is blocked; unclear gets a warning)
        │
        └── bess_calc.py
              ├── calc_bess()     — standalone storage (demand charge reduction + arbitrage)
              ├── calc_solar()    — solar PV sizing and generation offset
              └── calc_combined() — stacked economics with SGIP + ITC
```

**Stack:** Python 3, FastAPI, pdfplumber, Moonshot Kimi API, React + TypeScript, Bolt, Railway.

## Why these technical choices

**pdfplumber over OCR.** Utility bills are native PDFs with structured text layers. OCR adds latency and hallucination risk for no benefit.

**Vision LLM for parsing, not regex.** Every utility has a different bill layout. PG&E, Ava, SCE, SDG&E, PSE — all different. A 50-line regex-per-utility approach doesn't scale. An LLM parser generalizes across layouts with a single prompt.

**Moonshot Kimi over Anthropic Claude.** Switched in Dec 2025 — Moonshot's pricing is dramatically lower for the same parsing quality on Chinese and English bills, and API latency from China is more stable. Kept the OpenAI SDK interface so the swap was a single file change.

**Hard split between commercial and residential.** Residential bills lack demand charges, which is where 60%+ of commercial BESS value comes from. Running C&I logic on a residential bill produces wrong answers that look right. The classifier (`max_demand_kw ≥ 20 → commercial`, else check monthly kWh) blocks residential bills explicitly rather than silently mis-pricing them.

**Backend-protected calculation logic.** The ROI math (SGIP caps, ITC basis stacking, rate tariff constants) lives server-side in `bess_calc.py`, not in the frontend. The frontend can't be reverse-engineered into the model.

## Repo layout

| File | What it is |
|---|---|
| `app.py` | FastAPI application, `/analyze` endpoint, CORS |
| `pipeline.py` | PDF parsing, LLM call, customer classification, bill-to-inputs transformation |
| `bess_calc.py` | ROI calculation core: `calc_bess`, `calc_solar`, `calc_combined` |
| `Procfile`, `requirements.txt` | Railway deployment config |
| `UPDATES.md` / `UPDATES.zh.md` | One-time project history snapshot |

Frontend lives in a separate Bolt cloud project (not in this repo).

## Run locally

```bash
git clone https://github.com/simen-zhu/bess_calc
cd bess_calc
pip install -r requirements.txt
echo "MOONSHOT_API_KEY=your-key-here" > .env
python3 pipeline.py  # runs against a sample bill
# or
uvicorn app:app --reload  # run the API server
```

You'll need a Moonshot API key — get one at https://platform.moonshot.cn.

## Status and roadmap

**Currently live**: backend deployed on Railway, frontend on Bolt, end-to-end flow working on real California C&I bills.

**Next up**: manual parameter overrides — letting the user adjust battery size, install cost, SGIP/ITC toggles, and demand reduction assumption after the default ROI is returned. Targeted at BD reps and technically literate C&I customers who want to sensitize the default output to their own assumptions.

**In progress**: a Streamlit version of the core ROI model for faster iteration and internal use.

**Longer-term**: multi-utility validation (SCE, SDG&E, PSE), and Green Button 15-minute interval data integration for precise demand reduction estimates.

## About

A portfolio project built to demonstrate end-to-end thinking about clean energy BD workflows — not tech for its own sake, but tech applied to a specific operational bottleneck. The domain knowledge (PG&E B19S rate mechanics, SGIP incentive stacking, demand charge economics) is where the analytical value lives; the code is the delivery vehicle.

Targeting BD / analyst roles in clean energy storage and investment. More context on [LinkedIn](https://linkedin.com/in/simen-zhu).
