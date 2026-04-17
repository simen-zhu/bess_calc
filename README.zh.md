# bess_calc

> 一份电费单 PDF，几秒钟输出一个说得过去的储能 + 光伏投资测算。

🌏 [English version / 英文版](./README.md)  ·  📋 [更新日志](./UPDATES.zh.md)

**在线 Demo：** https://besscalc-production.up.railway.app
**前端：** https://react-solar-battery-b4ez.bolt.host

---

## 要解决什么问题

在商业储能 BD 的第一次客户对话里，客户问的第一个问题几乎总是：*"我能省多少钱？"* 答好这个问题要做的事不少——读懂复杂的电费单、拆解费率结构、估算削峰幅度、测算峰谷套利、叠加补贴（SGIP、ITC），最后给出回收期和 NPV。BD 通常用 Excel 一单一单算，平均 30+ 分钟一个 lead。

这个工具把这个"Stage 1 预测算"（BD 岗位负责的环节，后面详细工程由其他专家接手）压缩到一次 PDF 上传。

## 能做什么

1. **上传电费单 PDF**（当前支持商业/工业账单；住宅账单会被识别并友好提示不支持——住宅经济模型根本不同，超出本工具范围）
2. **用视觉 LLM 解析账单**——提取电力公司、费率代码、最大需量（kW）、峰谷 kWh、需量电费、能量电费
3. **跑三种 ROI 场景**——纯储能、纯光伏、光伏+储能组合
4. **返回**净安装成本（扣除 SGIP + 联邦 ITC 之后）、年节省、静态回收期、10 年 NPV

已在加州一个 C&I 真实电费单（PG&E B19S + Ava Community Energy 费率组合）上跑通端到端流程。

## 架构

```
PDF 上传（React / Bolt 前端）
        │
        ▼
FastAPI /analyze 端点（Python，Railway 部署）
        │
        ├── pdfplumber ──▶ 原始文本
        │
        ├── Moonshot Kimi (moonshot-v1-32k) ──▶ 结构化账单字典
        │                                       {utility, rate_schedule,
        │                                        max_demand_kw, peak_kwh, ...}
        │
        ├── classify_customer() ──▶ commercial / residential / unclear
        │       （住宅拦截；unclear 给警告继续）
        │
        └── bess_calc.py
              ├── calc_bess()     —— 纯储能（需量削峰 + 套利）
              ├── calc_solar()    —— 光伏发电抵扣
              └── calc_combined() —— 叠加 SGIP + ITC 的组合测算
```

**技术栈：** Python 3、FastAPI、pdfplumber、Moonshot Kimi API、React + TypeScript、Bolt、Railway。

## 关键技术选择

**用 pdfplumber 而不是 OCR。** 电费单是原生 PDF，文字层是结构化的。OCR 只会加延迟和幻觉风险，没任何好处。

**用视觉 LLM 解析，不用正则。** 每家电力公司账单版式都不一样——PG&E、Ava、SCE、SDG&E、PSE 都不同。给每家写 50 行正则的路子没法规模化。一个 LLM prompt 可以泛化到所有版式。

**Moonshot Kimi 替代 Anthropic Claude。** 2025 年 12 月切换——同等解析质量下 Moonshot 价格低很多，国内网络延迟也更稳定。保留了 OpenAI SDK 接口，换 API 只动一行代码。

**商业 vs 住宅硬分流。** 住宅账单没有需量电费，而 60%+ 的商业储能价值来自削峰。住宅账单跑商业逻辑会得到"看起来对但其实错"的结果。分类器（`max_demand_kw ≥ 20 → commercial`，否则看月用电量）明确拦截住宅账单，比静默给错答案更负责。

**ROI 逻辑放后端保护。** 所有计算（SGIP 上限、ITC 基数叠加、费率常量）放服务器端 `bess_calc.py`，不在前端。前端代码无法被反向工程出模型。

## 仓库文件

| 文件 | 说明 |
|---|---|
| `app.py` | FastAPI 应用、`/analyze` 端点、CORS 配置 |
| `pipeline.py` | PDF 解析、LLM 调用、客户分类、账单转输入 |
| `bess_calc.py` | ROI 计算核心：`calc_bess` / `calc_solar` / `calc_combined` |
| `Procfile`、`requirements.txt` | Railway 部署配置 |
| `UPDATES.md` / `UPDATES.zh.md` | 一次性项目历史回顾 |

前端在单独的 Bolt 云端项目里，不在这个仓库。

## 本地运行

```bash
git clone https://github.com/simen-zhu/bess_calc
cd bess_calc
pip install -r requirements.txt
echo "MOONSHOT_API_KEY=your-key-here" > .env
python3 pipeline.py  # 跑 sample 账单
# 或
uvicorn app:app --reload  # 启动 API 服务
```

需要一个 Moonshot API key——在 https://platform.moonshot.cn 申请。

## 当前状态 & 路线图

**已上线**：后端 Railway 部署、前端 Bolt 部署、端到端流程在真实加州 C&I 账单上跑通。

**即将开发**：手动参数覆盖——让用户在拿到默认 ROI 后调整电池容量、安装成本、SGIP/ITC 开关、削峰幅度假设。服务对象是 BD 同事和有技术素养的 C&I 客户，让他们能基于自己的假设做敏感性分析。

**进行中**：核心 ROI 模型的 Streamlit 版本，用于更快迭代和内部使用。

**远期**：多电力公司验证（SCE、SDG&E、PSE），以及 Green Button 15 分钟间隔数据接入做精确削峰估算。

## 关于

一个作品集项目，展示对清洁能源 BD 工作流的端到端思考——技术不是目的，而是针对特定业务瓶颈的应用。行业知识（PG&E B19S 费率机制、SGIP 补贴叠加规则、需量电费经济学）是真正的分析价值所在；代码只是交付载体。

目标方向：清洁能源储能与投资领域的 BD / Analyst 岗位。更多背景见 [LinkedIn](https://linkedin.com/in/simen-zhu)。
