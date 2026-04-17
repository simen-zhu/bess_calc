# pipeline.py
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
from bess_calc import calc_bess, calc_solar, calc_combined

PROMPT = """从这张电费单提取以下数据，只返回JSON不要其他文字：
{
  "utility": "电力公司名称",
  "rate_schedule": "费率代码",
  "max_demand_kw": 最大需量数字,
  "peak_kwh": 峰时用电量数字,
  "offpeak_kwh": 谷时用电量数字,
  "billing_days": 账单天数数字,
  "peak_rate": 综合峰时电价数字,
  "offpeak_rate": 综合谷时电价数字,
  "demand_rate": 需量电价每kW数字,
  "peak_demand_rate": 峰时需量电价每kW数字,
  "total_amount": 账单总金额数字
}"""


def parse_bill(pdf_path: str) -> dict:
    api_key = (os.environ.get("MOONSHOT_API_KEY") or "").strip()
    client = OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1")

    # 上传 PDF 并提取文本内容
    file_object = client.files.create(file=Path(pdf_path), purpose="file-extract")
    file_content = client.files.content(file_id=file_object.id).text

    # 调用 Kimi 解析账单
    completion = client.chat.completions.create(
        model="moonshot-v1-32k",
        messages=[
            {"role": "system", "content": file_content},
            {"role": "user", "content": PROMPT},
        ],
    )

    raw = completion.choices[0].message.content
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"Kimi 返回的内容不是合法 JSON：{e}\n原始返回：{raw}")


def bill_to_inputs(bill: dict) -> dict:
    dr_kw = bill["max_demand_kw"] * 0.17
    arb_kwh = min(
        (bill["peak_kwh"] + bill["offpeak_kwh"]) / bill["billing_days"] * 0.5,
        400
    )
    return {
        "dr_kw": round(dr_kw, 1),
        "arb_kwh": round(arb_kwh, 1),
        "peak_rate": bill["peak_rate"],
        "demand_rate": bill["demand_rate"],
        "peak_demand_rate": bill.get("peak_demand_rate", 0),
    }


def run_analysis(pdf_path: str):
    print("正在用Claude解析账单...\n")
    bill = parse_bill(pdf_path)
    inputs = bill_to_inputs(bill)

    print(f"电力公司: {bill['utility']} | 费率: {bill['rate_schedule']}")
    print(f"最大需量: {bill['max_demand_kw']} kW | 月账单: ${bill['total_amount']:,.2f}")
    print(f"需量电价: ${inputs['demand_rate']}/kW | 峰时电价: ${inputs['peak_rate']}/kWh")
    print(f"削峰量: {inputs['dr_kw']} kW | 套利容量: {inputs['arb_kwh']} kWh\n")

    bess = calc_bess(
        dr_kw=inputs["dr_kw"],
        arb_kwh=inputs["arb_kwh"],
        demand_rate=inputs["demand_rate"],
        peak_demand_rate=inputs["peak_demand_rate"],
    )
    solar = calc_solar(peak_rate=inputs["peak_rate"])
    combined = calc_combined(bess, solar)

    print(f"{'':20} {'BESS':>12} {'光伏':>12} {'组合':>12}")
    print("-" * 60)
    print(f"{'净成本':20} ${bess['net_cost']:>11,} ${solar['net_cost']:>11,} ${combined['net_cost']:>11,}")
    print(f"{'年节省':20} ${bess['annual_savings_y1']:>11,} ${solar['annual_savings_y1']:>11,} ${combined['annual_savings_y1']:>11,}")
    print(f"{'回收期':20} {str(bess['payback_years'])+'年':>12} {str(solar['payback_years'])+'年':>12} {str(combined['payback_years'])+'年':>12}")
    print(f"{'10年NPV':20} ${bess['npv_10yr']:>11,} ${solar['npv_10yr']:>11,} ${combined['npv_10yr']:>11,}")


if __name__ == "__main__":
    run_analysis(str(Path(__file__).parent / "PGE_bill_cali.pdf"))
