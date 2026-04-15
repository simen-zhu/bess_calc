# bess_calc.py

def calc_bess(
    cap_kwh=400,
    pwr_kw=150,
    cost_per_kwh=280,
    dr_kw=55,
    arb_kwh=320,
    eff=0.92,
    esc=0.035,
    sgip=True,
    itc=True,
    demand_rate=39.22,
    peak_demand_rate=6.40,
):
    gross = cap_kwh * cost_per_kwh
    sgip_amt = min(cap_kwh * 200, gross * 0.9) if sgip else 0
    itc_base = (gross - sgip_amt) if sgip else gross
    itc_amt = itc_base * 0.30 if itc else 0
    net_cost = gross - sgip_amt - itc_amt

    dc_monthly = dr_kw * demand_rate + dr_kw * peak_demand_rate
    arb_monthly = arb_kwh * eff * 0.1155 * 30
    total_monthly = dc_monthly + arb_monthly
    om_annual = gross * 0.015

    npv = -net_cost
    cumulative = -net_cost
    payback_year = None

    for y in range(1, 11):
        escalation = (1 + esc) ** (y - 1)
        annual_net = total_monthly * 12 * escalation - om_annual
        npv += annual_net / (1.05 ** y)
        cumulative += annual_net
        if payback_year is None and cumulative >= 0:
            payback_year = y

    return {
        "gross_cost": round(gross),
        "net_cost": round(net_cost),
        "sgip_rebate": round(sgip_amt),
        "itc_credit": round(itc_amt),
        "monthly_savings": round(total_monthly),
        "annual_savings_y1": round(total_monthly * 12 - om_annual),
        "payback_years": payback_year,
        "npv_10yr": round(npv),
    }


def calc_solar(
    system_kw=100,
    cost_per_w=2.80,
    annual_kwh=145000,
    peak_rate=0.3436,
    itc=True,
    esc=0.035,
):
    gross = system_kw * cost_per_w * 1000
    itc_amt = gross * 0.30 if itc else 0
    net_cost = gross - itc_amt
    om_annual = gross * 0.01

    annual_savings = annual_kwh * peak_rate

    npv = -net_cost
    cumulative = -net_cost
    payback_year = None

    for y in range(1, 11):
        escalation = (1 + esc) ** (y - 1)
        annual_net = annual_savings * escalation - om_annual
        npv += annual_net / (1.05 ** y)
        cumulative += annual_net
        if payback_year is None and cumulative >= 0:
            payback_year = y

    return {
        "gross_cost": round(gross),
        "net_cost": round(net_cost),
        "itc_credit": round(itc_amt),
        "annual_savings_y1": round(annual_savings - om_annual),
        "payback_years": payback_year,
        "npv_10yr": round(npv),
    }


def calc_combined(bess_result, solar_result):
    net_cost = bess_result["net_cost"] + solar_result["net_cost"]
    annual_savings = bess_result["annual_savings_y1"] + solar_result["annual_savings_y1"]
    gross_cost = bess_result["gross_cost"] + solar_result["gross_cost"]
    om_annual = gross_cost * 0.01

    npv = -net_cost
    cumulative = -net_cost
    payback_year = None

    for y in range(1, 11):
        escalation = (1.035) ** (y - 1)
        annual_net = annual_savings * escalation - om_annual
        npv += annual_net / (1.05 ** y)
        cumulative += annual_net
        if payback_year is None and cumulative >= 0:
            payback_year = y

    return {
        "net_cost": round(net_cost),
        "annual_savings_y1": round(annual_savings),
        "payback_years": payback_year,
        "npv_10yr": round(npv),
    }