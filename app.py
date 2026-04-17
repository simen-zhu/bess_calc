from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from pipeline import parse_bill, bill_to_inputs, classify_customer
from bess_calc import calc_bess, calc_solar, calc_combined

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    bill = parse_bill(tmp_path)
    os.unlink(tmp_path)

    customer_type = classify_customer(bill)

    if customer_type == "residential":
        return {
            "customer_type": "residential",
            "supported": False,
            "reason": "住宅账单暂不支持，本工具仅适用于商业/工业用户账单（含需量电费）。",
        }

    inputs = bill_to_inputs(bill)

    bess = calc_bess(
        dr_kw=inputs["dr_kw"],
        arb_kwh=inputs["arb_kwh"],
        demand_rate=inputs["demand_rate"],
        peak_demand_rate=inputs["peak_demand_rate"],
    )
    solar = calc_solar(peak_rate=inputs["peak_rate"])
    combined = calc_combined(bess, solar)

    return {
        "customer_type": customer_type,
        "supported": True,
        "bess": {"net_cost": bess["net_cost"], "annual_savings": bess["annual_savings_y1"], "payback_years": bess["payback_years"], "npv_10yr": bess["npv_10yr"]},
        "solar": {"net_cost": solar["net_cost"], "annual_savings": solar["annual_savings_y1"], "payback_years": solar["payback_years"], "npv_10yr": solar["npv_10yr"]},
        "combined": {"net_cost": combined["net_cost"], "annual_savings": combined["annual_savings_y1"], "payback_years": combined["payback_years"], "npv_10yr": combined["npv_10yr"]},
        "utility_data": {"utility_name": bill.get("utility"), "monthly_bill": bill.get("total_amount"), "rate_per_kwh": bill.get("peak_rate"), "monthly_kwh": round((bill.get("peak_kwh", 0) + bill.get("offpeak_kwh", 0)) / bill.get("billing_days", 30) * 30)},
    }

@app.get("/health")
def health():
    return {"status": "ok"}