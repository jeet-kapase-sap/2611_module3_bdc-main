# Module 3 — 💬 Questions Catalogue

## 📦 SAP Business Data Cloud — Data Products

| Service | Data Product | Type | Description |
|---|---|---|---|
| **SVC1** | `AM_PO_HISTORY` | Analytic Model | Purchase order history — spend, quantities, delivery performance, pricing |
| **SVC2** | `V_SUPPLIER` | Dimension View | Supplier master — name, country, city, region, blocked status |
| **SVC3** | `AM_SUPPLIER_RISK_SCORE` | Analytic Model | Composite risk scores — spend concentration (35%), single source (30%), country risk (35%) |

---

## ⚙️ How It Works

```
User Question → LLM extracts parameters → Calls 1-3 BDC operations → LLM aggregates & composes answer
```

- **Single-service questions**: LLM calls one operation, aggregates the results, responds.
- **Multi-service questions**: LLM chains calls — e.g., gets risk data first, extracts supplier IDs, then fetches supplier names in a second round.
- **Pre-computed fields**: The LLM uses `CountPurchaseOrder` (not row counting) and `Late_Delivery_Pct` (not manual calculation) — these are built into the data products.

---

## 🟢 Basic — Single Service, Single Call

### Q1 | AM_PO_HISTORY
> **How many purchase orders did we place with Supplier 17300001 in 2020 and what was the total value?**

| Round | Operation | What Happens |
|---|---|---|
| 1 | `get_po_history` | `supplier='17300001'`, `year='2020'` → LLM sums `CountPurchaseOrder` and `NetAmount` |

**Learns**: Basic filtering, using pre-computed measures.

---

### Q2 | V_SUPPLIER
> **How many suppliers do we have in each country? Show as a table of country code and supplier count.**

| Round | Operation | What Happens |
|---|---|---|
| 1 | `get_supplier_info` | Fetch all suppliers → orchestrator pre-aggregates by Country → LLM presents table |

**Learns**: Full-scan query, pre-aggregation in the orchestrator.

---

### Q3 | AM_PO_HISTORY
> **What are our top 5 materials by total spend in 2019 and how many POs were created for each?**

| Round | Operation | What Happens |
|---|---|---|
| 1 | `get_po_history` | `year='2019'`, `select='Material,NetAmount,CountPurchaseOrder'` → orchestrator pre-aggregates spend and PO count by Material → LLM ranks top 5 |

**Learns**: Requesting specific fields via `select`, top-N ranking from pre-aggregated data.

---

## 🟡 Intermediate — Threshold Filters or Two Services

### Q4 | AM_PO_HISTORY
> **Which suppliers have delivered late more than 1% of the time in the year 2017?**

| Round | Operation | What Happens |
|---|---|---|
| 1 | `get_po_history` | `year='2017'`, `late_delivery_gt=1.0` → returns only suppliers exceeding 1% late delivery threshold |

**Learns**: Threshold filtering on a derived metric (`Late_Delivery_Pct`).

---

### Q5 | AM_PO_HISTORY → V_SUPPLIER
> **What is the average price we pay for material TG11 across all suppliers and who offers the best price?**

| Round | Operation | What Happens |
|---|---|---|
| 1 | `get_po_history` | `material='TG11'`, `select='Supplier,Unit_Price,NetPriceAmount'` → LLM computes avg price per supplier, identifies best |
| 2 | `get_supplier_info` | `supplier='<best_supplier_id>'` → enriches with `SupplierName`, `Country` |

**Learns**: Multi-round chaining — first call finds the answer, second call enriches it with context.

---

### Q6 | AM_SUPPLIER_RISK_SCORE → V_SUPPLIER
> **Are any of our suppliers located in sanctioned countries? Show their names and risk scores.**

| Round | Operation | What Happens |
|---|---|---|
| 1 | `get_supplier_risk` | `sanctions_only=true` → returns suppliers with `Trade_Sanctions_Flag='Y'` |
| 2 | `get_supplier_info` | Fetches `SupplierName`, `CityName` for each sanctioned supplier |

**Learns**: Boolean flag filtering, multi-round enrichment.

---

### Q7 | AM_SUPPLIER_RISK_SCORE
> **Which suppliers are rated HIGH risk in US and IN in 2019?**

| Round | Operation | What Happens |
|---|---|---|
| 1 | `get_supplier_risk` | `risk_category='HIGH'`, `countries='US,IN'`, `year='2019'` → multi-condition OData filter with OR logic on countries |

**Learns**: Multi-condition filtering, comma-separated country list translated to OData OR clause.

---

## 🔴 Complex — Multi-Service, Analytical Reasoning

### Q8 | AM_SUPPLIER_RISK_SCORE → V_SUPPLIER
> **What is the driving score for the HIGH risk suppliers from India in 2019? Break down all risk dimensions.**

| Round | Operation | What Happens |
|---|---|---|
| 1 | `get_supplier_risk` | `risk_category='HIGH'`, `country='IN'`, `year='2019'` → returns full score breakdown: `SpendConcentrationScore`, `SingleSourceScore`, `CompositeRiskScore`, `WorstMaterialGroup`, `Trade_Sanctions_Flag` |
| 2 | `get_supplier_info` | Fetches `SupplierName` for display |

**Learns**: LLM interprets which sub-score (Spend Concentration, Single Source, or Country Risk) is the dominant risk driver by comparing individual scores. Analytical reasoning, not just data retrieval.

---

### Q9 | AM_SUPPLIER_RISK_SCORE → AM_PO_HISTORY → V_SUPPLIER
> **Who are our top 3 highest-risk suppliers in 2020? For each, show their supplier name, composite risk score, worst material group name, spend concentration percentage, and total PO spend.**

| Round | Operation | What Happens |
|---|---|---|
| 1 | `get_supplier_risk` | `year='2020'`, `order_by='CompositeRiskScore desc'`, `top=3` → identifies top 3 riskiest suppliers with risk breakdown |
| 2 | `get_po_history` | `supplier='<each_supplier>'`, `year='2020'` → total PO spend per supplier |
| 3 | `get_supplier_info` | Fetches `SupplierName`, `Country` for each supplier |

**Learns**: Three-service orchestration — LLM chains risk → spend → master data and merges into a single answer. Full data product showcase.

---

### Q10 | AM_SUPPLIER_RISK_SCORE + AM_PO_HISTORY + V_SUPPLIER
> **Compare the year-over-year risk trend for Supplier 17300001: show composite risk score, spend concentration, single-source count, total PO spend, and late delivery rate for 2018, 2019, and 2020.**

| Round | Operation | What Happens |
|---|---|---|
| 1 | `get_supplier_risk` | `supplier='17300001'`, `years='2018,2019,2020'` → risk scores across 3 years |
| 2 | `get_po_history` | `supplier='17300001'` for each year → `NetAmount`, `Late_Delivery_Pct` |
| 3 | `get_supplier_info` | `supplier='17300001'` → `SupplierName`, `Country` for context |

**Learns**: Trend analysis — LLM merges risk and operational data across years into a comparison table, identifies whether risk is trending up or down and explains why.

---

## 📌 Summary

| # | Question | Level | Services | Rounds | Key Learning |
|---|---|---|---|---|---|
| Q1 | PO count and value for a supplier | 🟢 Basic | SVC1 | 1 | Pre-computed measures |
| Q2 | Supplier count by country | 🟢 Basic | SVC2 | 1 | Pre-aggregation in orchestrator |
| Q3 | Top 5 materials by spend + PO count | 🟢 Basic | SVC1 | 1 | Select fields, top-N ranking |
| Q4 | Late delivery suppliers > 1% | 🟡 Intermediate | SVC1 | 1 | Threshold filtering |
| Q5 | Average price + best supplier | 🟡 Intermediate | SVC1 → SVC2 | 2 | Multi-round enrichment |
| Q6 | Suppliers in sanctioned countries | 🟡 Intermediate | SVC3 → SVC2 | 2 | Boolean flag + enrichment |
| Q7 | HIGH risk in US and India | 🟡 Intermediate | SVC3 | 1 | Multi-condition filter |
| Q8 | Risk score driver breakdown | 🔴 Complex | SVC3 → SVC2 | 2 | Analytical reasoning |
| Q9 | Top 3 riskiest + spend + names | 🔴 Complex | SVC3 → SVC1 → SVC2 | 3 | Three-service orchestration |
| Q10 | Year-over-year risk trend | 🔴 Complex | SVC3 + SVC1 + SVC2 | 3 | Trend analysis + multi-source merge |
