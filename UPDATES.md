# bess_calc Project Updates

A one-time snapshot of major changes from project inception through 2026-04-16.
For changes after this date, see `git log`. This file is not maintained going forward.

🌏 [中文版 / Chinese version](./UPDATES.zh.md)

Repository: https://github.com/simen-zhu/bess_calc
Deployment: https://besscalc-production.up.railway.app

---

## December 2025 (most recent)

**Commercial vs. residential bill classification** — `081cf38`
Added `classify_customer(bill)` to the backend with three rules:
- `max_demand_kw >= 20` → commercial
- Otherwise, monthly `peak_kwh + offpeak_kwh < 3000` → residential
- All other cases → unclear

Residential bills are blocked from the ROI calculation. The `/analyze` endpoint now returns two new fields: `customer_type` and `supported`. Residential responses include a `reason` explaining why they're not supported.

Matching frontend changes (blue info card for residential, yellow warning banner for unclear, and a fix for the `data.bess.net_cost` undefined white-screen bug) live in the Bolt cloud project, not in this repo.

---

## December 2025 (earlier)

**LLM switch: Anthropic Claude → Moonshot Kimi** — `f4b6e84`, `0a07934`, `66b2ae1`
PDF bill parsing moved from the Anthropic API to the Moonshot Kimi API (`moonshot-v1-32k`). Motivation: cost and network reliability in China.

Related changes:
- Added `python-dotenv` for local `.env` loading of `MOONSHOT_API_KEY`
- Fixed API key `.strip()` handling and removed a duplicate line
- Changed the print message from "Parsing with Claude..." to "Parsing with Kimi..."

**Moonshot overload auto-retry** (folded into the LLM switch, not a separate commit)
Exponential backoff at 2s / 5s / 10s, up to 3 retries, to handle occasional 429/5xx from Moonshot.

---

## November 2025 and earlier

**Railway deployment** — `be46128`, `1da3844`
Added `Procfile` and `requirements.txt` for Railway. Fixed FastAPI CORS middleware ordering — the middleware must be attached right after app instantiation, otherwise cross-origin requests from the frontend get blocked.

**PDF parsing pipeline** — `e8fa56c`
`pipeline.py` shipped: pdfplumber extracts text → LLM parses into a structured dict (utility, rate_schedule, max_demand_kw, peak_kwh, offpeak_kwh, etc.) → `bill_to_inputs()` converts the dict into BESS/Solar calculator inputs.

**Initial commit** — `b2f3397`
Project kickoff. Core file: `bess_calc.py` with `calc_bess` / `calc_solar` / `calc_combined` functions. Built on a real C&I bill under PG&E B19S + Ava Community Energy, with SGIP + ITC toggles, 10-year NPV, and simple payback period outputs.

---

*For changes after 2026-04-16, see `git log`.*
