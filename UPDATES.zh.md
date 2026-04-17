# bess_calc 项目更新日志

这是一份一次性的项目回顾快照，覆盖从项目初始到 2026-04-16 的主要变更。
此后的变更请查看 `git log`，不再维护此文件。

🌏 [English version / 英文版](./UPDATES.md)

仓库：https://github.com/simen-zhu/bess_calc
部署：https://besscalc-production.up.railway.app

---

## 2025 年 12 月（最近）

**商用 vs 住宅账单自动分类** — `081cf38`
后端加了 `classify_customer(bill)` 函数，按三条规则分类：
- `max_demand_kw >= 20` → commercial
- 否则月用电量 `peak_kwh + offpeak_kwh < 3000` → residential
- 其他 → unclear

住宅账单直接拦下不跑 ROI 计算。`/analyze` 端点 response 新增两个字段：`customer_type` 和 `supported`，residential 时附带 `reason` 说明不支持原因。

配套的前端改动（蓝色 info card 拦住 residential、黄色警告条标记 unclear、修 `data.bess.net_cost` undefined 白屏）在 Bolt 云端做，不在这个仓库里。

---

## 2025 年 12 月（更早一点）

**切换 LLM：Anthropic Claude → Moonshot Kimi** — `f4b6e84`、`0a07934`、`66b2ae1`
PDF 账单解析从 Anthropic API 换成 Moonshot Kimi API（`moonshot-v1-32k`）。动机：成本 + 国内网络稳定性。

顺带做的事：
- 引入 `python-dotenv`，支持本地 `.env` 加载 `MOONSHOT_API_KEY`
- 修 API key `.strip()` 处理，删掉一行重复代码
- print 文案从"正在用Claude解析账单"改成"正在用Kimi解析账单"

**Moonshot 过载自动重试**（未单独成 commit，含在切换里）
指数退避 2s / 5s / 10s，最多重试 3 次，应对 Moonshot 偶发 429/5xx。

---

## 2025 年 11 月及更早

**部署到 Railway** — `be46128`、`1da3844`
加了 `Procfile` 和 `requirements.txt`，部署到 Railway。修了 FastAPI 的 CORS middleware 加载顺序——必须在 app 实例化之后立刻挂载，否则前端跨域请求被拦。

**PDF 解析 pipeline 成型** — `e8fa56c`
`pipeline.py` 成型：pdfplumber 抽文本 → LLM 解析成结构化 dict（utility、rate_schedule、max_demand_kw、peak_kwh、offpeak_kwh 等）→ `bill_to_inputs()` 转成 BESS/Solar 计算器输入。

**项目起点** — `b2f3397`
初始 commit。核心文件：`bess_calc.py`（ROI 计算逻辑，含 `calc_bess` / `calc_solar` / `calc_combined` 三个函数）。基于 PG&E B19S + Ava Community Energy 的真实 C&I 账单，SGIP + ITC 补贴 toggle，10 年 NPV 和静态回收期输出。

---

*2026-04-16 之后的变更请 `git log` 查看。*
