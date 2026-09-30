# Module 3 — Governed Multi-Source Answers from SAP Business Data Cloud

## Overview

This solution demonstrates how to answer natural language procurement and risk analytics questions using **governed data products from SAP Business Data Cloud**. Unlike Module 2 which queries a single live S/4HANA system, Module 3 blends multiple SAP and non-SAP sources into pre-modeled, consumption-ready data products in SAP Datasphere.

**Use case:** BestRun Technologies — Supplier Risk Intelligence  
Meet Eric Larsen: A Chief Procurement Officer (CPO) at BestRun Technologies, asks natural language questions about purchase order history, supplier details, and composite supplier risk scores — all answered from governed BDC data products that combine S/4HANA PO data, supplier master data, and an external country risk index.

---

## 🏗️ Architecture

```
Notebook ---- HTTPS ----> bdc_connectivity.py (CF App on SAP BTP Cloud Foundry)
                                ├── /odata  ──► BTP Destination Service ──► SAP Datasphere ──► SAP Business Data Cloud Data Products
                                └── /fetch_data  (standalone smoke test endpoint)

AI Core (GPT-5) ──► called directly from notebook using client_credentials OAuth
```

### Data Lineage

```
SAP BDC Data Products (SAP)              External Data (Non-SAP)
├─ PurchaseOrder                         ├─ EXT_COUNTRY_RISK_INDEX
├─ PurchaseOrderItem                     │   (Country Risk Scores, CSV)
├─ PurchaseOrderScheduleLine             │
├─ Supplier                              │
│                                        │
▼                                        ▼
┌────────────────────────────────────────────────────────────────┐
│                  SAP Datasphere Modeling                        │
│                                                                │
│  PO + POItem + POScheduleLine ──► HL_PO_HISTORY (Flattened)    │
│  Supplier ────────────────────► V_SUPPLIER (Dimension)         │
│                                                                │
│  HL_PO_HISTORY ──┐                                             │
│  V_SUPPLIER ─────┤──► V_SUPPLIER_RISK_SCORE (SQL View)         │
│  EXT_COUNTRY_ ───┘    ├─ Spend Concentration (35%)             │
│  RISK_INDEX            ├─ Single Source Dependency (30%)        │
│                        ├─ Country Risk (35%)                   │
│                        └─ Composite Risk Score (0-100)         │
│                                                                │
│  HL_PO_HISTORY ──────────────► AM_PO_HISTORY (Analytic Model)  │
│  V_SUPPLIER_RISK_SCORE ──────► AM_SUPPLIER_RISK_SCORE (AM)     │
└────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
├── bdc_connectivity.py             # CF app — BDC connection via BTP Destination Service
├── manifest.yaml                   # CF deployment manifest
├── requirements.txt                # Python dependencies
├── runtime.txt                     # Python version (3.11.16)
├── module3_implementation.ipynb    # Main workshop notebook
└── README_MODULE3.md               # This file
```

---

## 🧩 Components

### 1. `bdc_connectivity.py` — CF BDC Connectivity App

A lightweight Flask app deployed to SAP BTP Cloud Foundry that proxies OData requests from the notebook to SAP Datasphere via BTP Destination Service.

- **`/odata`** — Main proxy endpoint. Accepts `dest`, `path` (or `service`), and any `$`-prefixed OData parameters. Routes through BTP Destination Service → SAP Datasphere.
- **`/fetch_data`** — Standalone smoke test — returns 1 row from AM_PO_HISTORY to verify the full chain.

**Key design:**
- Reads destination credentials from `VCAP_SERVICES` (injected by CF service binding)
- Fetches OAuth bearer token from BTP Destination Service for each request
- Supports two calling modes: by registered service name (`?service=AM_PO_HISTORY`) or by full OData path (`?path=/api/v1/...`)
- No Cloud Connector needed — Datasphere is cloud-to-cloud

### 2. `module3_implementation.ipynb` — Workshop Notebook

Jupyter notebook with three governed read-only operations against SAP Business Data Cloud:

| Operation | What It Answers | Data Product | Type |
|---|---|---|---|
| `get_po_history` | Spend, PO counts, delivery performance, pricing | AM_PO_HISTORY | Analytic Model |
| `get_supplier_info` | Supplier names, countries, blocked status | V_SUPPLIER | Dimension View |
| `get_supplier_risk` | Composite risk scores, risk drivers, sanctions | AM_SUPPLIER_RISK_SCORE | Analytic Model |

---

## ☁️ BTP Services Required

| Service | Purpose | Binding |
|---|---|---|
| Destination Service | Lookup Datasphere destination config (URL, OAuth credentials) | `module3_bdc` |

AI Core credentials are provided via `.env` file (not CF-bound).

**Note:** Unlike Module 2, no Cloud Connector or Connectivity Service is needed — SAP Datasphere is a cloud service accessible directly via BTP Destination Service.

---

## 📦 SAP Business Data Cloud — Data Products

### OData Services Exposed from SAP Datasphere

| Data Product | OData Path | Type | Description |
|---|---|---|---|
| `AM_PO_HISTORY` | `/api/v1/datasphere/consumption/analytical/AI_DATA_FOUNDATION/AM_PO_HISTORY/AM_PO_HISTORY` | Analytical | PO history — spend, quantities, delivery, pricing |
| `V_SUPPLIER` | `/api/v1/datasphere/consumption/relational/AI_DATA_FOUNDATION/V_SUPPLIER/V_SUPPLIER/SET` | Relational | Supplier master — name, country, city, blocked status |
| `AM_SUPPLIER_RISK_SCORE` | `/api/v1/datasphere/consumption/analytical/AI_DATA_FOUNDATION/AM_SUPPLIER_RISK_SCORE/AM_SUPPLIER_RISK_SCORE` | Analytical | Composite risk scores with sub-dimensions |

### AM_PO_HISTORY — Key Fields

| Field | Type | Description |
|---|---|---|
| `PurchaseOrder` | String(10) | PO document number |
| `PurchaseOrderItem` | String(5) | PO line item |
| `PurchaseOrderDate` | Date | PO creation date |
| `Supplier` | String(10) | Supplier ID |
| `Material` | String(40) | Material number |
| `MaterialGroup` | String(9) | Material group code |
| `Plant` | String(4) | Plant code |
| `NetAmount` | Decimal(34,4) | Line item spend |
| `Unit_Price` | Decimal(5) | Unit price |
| `OrderQuantity` | Decimal(13,3) | Ordered quantity |
| `CountPurchaseOrder` | Int32 | Pre-computed PO count per row |
| `CountScheduleLines` | Int32 | Pre-computed schedule line count |
| `IsLateDelivery` | Int32 | Late delivery flag (0/1) |
| `Late_Delivery_Pct` | Double | Late delivery percentage |
| `LocalCurrency` | String(5) | Currency code |

### V_SUPPLIER — Key Fields

| Field | Type | Description |
|---|---|---|
| `Supplier` | String(10) | Supplier ID (primary key) |
| `SupplierName` | String(80) | Supplier display name |
| `Country` | String(3) | Country code |
| `Region` | String(3) | Region code |
| `CityName` | String(35) | City |
| `PostingIsBlocked` | Boolean | Posting blocked flag |
| `PurchasingIsBlocked` | Boolean | Purchasing blocked flag |

### AM_SUPPLIER_RISK_SCORE — Key Fields

| Field | Type | Description |
|---|---|---|
| `Supplier` | String(10) | Supplier ID |
| `Year` | String(4) | Calendar year |
| `Country` | String(3) | Supplier country |
| `CompositeRiskScore` | Int32 | Weighted risk score (0-100) |
| `RiskCategory` | String(6) | HIGH / MEDIUM / LOW |
| `SpendConcentrationScore` | Int32 | Spend concentration dimension (0-100, weight 35%) |
| `SpendConcentrationPct` | Decimal(18,2) | Supplier spend / total group spend × 100 |
| `SingleSourceScore` | Int32 | Single source dimension (0-100, weight 30%) |
| `SingleSourcedMaterialCount` | Int32 | Materials with only this supplier |
| `SupplierGroupSpend` | Decimal(38,4) | Supplier's spend in worst material group |
| `TotalGroupSpend` | Decimal(38,4) | Total spend in that material group |
| `WorstMaterialGroup` | String(9) | Material group with highest concentration |
| `WorstMaterialGroupName` | String(20) | Material group description |
| `Trade_Sanctions_Flag` | String(1) | Y = sanctioned (overrides score to 99) |
| `Political_Stability` | Int32 | Country political stability score |
| `Logistics_Reliability` | Int32 | Country logistics reliability score |

---

## 🧮 Risk Scoring Logic

The `AM_SUPPLIER_RISK_SCORE` data product implements a composite risk model:

```
CompositeRiskScore = SpendConcentrationScore × 0.35
                   + SingleSourceScore × 0.30
                   + CountryRiskScore × 0.35
```

| Dimension | Weight | Thresholds |
|---|---|---|
| Spend Concentration | 35% | >60% → 90, >30% → 50, ≤30% → 20 |
| Single Source | 30% | ≥6 materials → 95, ≥3 → 60, ≥1 → 30, 0 → 0 |
| Country Risk | 35% | Uses `Overall_Risk_Score` from external dataset |

**Override:** `Trade_Sanctions_Flag = 'Y'` → `CompositeRiskScore = 99` (HIGH)

**Categories:** >60 = HIGH, >30 = MEDIUM, ≤30 = LOW

---

## 📋 Setup

### 1. BTP Destination (`BDC-AI-Data-Foundation`)

| Property | Value |
|---|---|
| URL | `https://<datasphere-tenant>.datasphere.cloud.sap` |
| Proxy Type | `Internet` |
| Authentication | `OAuth2SAMLBearerAssertion` or `OAuth2ClientCredentials` |
| Audience | Datasphere tenant URL |
| Token Service URL | `https://<datasphere-tenant>.authentication.<region>.hana.ondemand.com/oauth/token` |

### 2. `.env` File

Create `.env` in the project root:

| Variable | Description |
|---|---|
| `AICORE_AUTH_URL` | AI Core OAuth URL |
| `AICORE_CLIENT_ID` | AI Core client ID |
| `AICORE_CLIENT_SECRET` | AI Core client secret |
| `GPT5_DEPLOYMENT_URL` | GPT-5 deployment inference URL |
| `DESTINATION` | BTP Destination name (e.g. `BDC-AI-Data-Foundation`) |
| `BDC_PROXY_URL` | Cloud Foundry app route URL |

### 3. Deploy CF App

```sh
cf login
cf push
```

### 4. Verify Connectivity

```
GET https://<app-route>/fetch_data
```

Should return 1 row of PO history data from SAP Datasphere.

---

## 🚀 Running the Notebook

### On SAP Business Application Studio (BAS)

**One-time setup** (run in terminal):
```bash
python3 -m venv ~/venv
~/venv/bin/pip install python-dotenv pandas matplotlib requests ipykernel
~/venv/bin/python -m ipykernel install --user --name=venv --display-name="Python (venv)"
```

Then select **Python (venv)** kernel in the notebook.

### On VS Code (local)

No venv needed — run Step 1 in the notebook:
```python
%pip install python-dotenv pandas matplotlib requests
```

### Notebook Steps

| Step | What It Does |
|---|---|
| **1** | Install dependencies |
| **2** | Imports and environment setup |
| **3** | Configuration — loads `.env`, defines OData paths |
| **4** | AI Core LLM Client — OAuth token management, chat completions |
| **5** | BDC OData Helper — `bdc_get()` routes requests through CF proxy |
| **6** | Smoke Tests — validates all 3 OData services are reachable |
| **7** | Governed Business Operations — 3 operations, one per data product |
| **8** | LLM Tool Schemas — registers operations with explicit field descriptions |
| **9** | System Prompt — BDC context, aggregation rules, risk interpretation |
| **10** | Ask Engine — multi-round orchestrator with smart payload management |
| **11** | Ask SAP Business Data Cloud — 10 questions, basic to complex |

---

## 💬 Sample Questions (Basic → Complex)

| # | Question | Level | Services | Rounds |
|---|---|---|---|---|
| Q1 | How many POs did we place with Supplier X in 2020 and total value? | 🟢 Basic | SVC1 | 1 |
| Q2 | How many suppliers per country? | 🟢 Basic | SVC2 | 1 |
| Q3 | Top 5 materials by spend in 2019 + PO count? | 🟢 Basic | SVC1 | 1 |
| Q4 | Suppliers with late delivery > 1% in 2017? | 🟡 Intermediate | SVC1 | 1 |
| Q5 | Average price for material TG11 + best supplier? | 🟡 Intermediate | SVC1 → SVC2 | 2 |
| Q6 | Suppliers in sanctioned countries? | 🟡 Intermediate | SVC3 → SVC2 | 2 |
| Q7 | HIGH risk suppliers in US and IN in 2019? | 🟡 Intermediate | SVC3 | 1 |
| Q8 | Risk score drivers for HIGH risk supplier from India? | 🔴 Complex | SVC3 → SVC2 | 2 |
| Q9 | Top 3 riskiest suppliers + spend + names? | 🔴 Complex | SVC3 → SVC1 → SVC2 | 3 |
| Q10 | Year-over-year risk trend for a supplier? | 🔴 Complex | SVC3 + SVC1 + SVC2 | 3 |

---

## ⚠️ Known Limitations

1. **Pre-aggregation approximation** — Large result sets (>100 rows) are pre-aggregated by the orchestrator before being sent to the LLM. This reduces token cost and latency but means the LLM works from summaries, not raw data. For precise drill-downs, reduce the query scope with filters.

2. **No write operations** — All three operations are read-only. The LLM cannot create, update, or delete any data in SAP Business Data Cloud.

3. **Row cap** — Operations enforce hard caps: `get_po_history` (5,000), `get_supplier_info` (1,000), `get_supplier_risk` (1,000). Queries exceeding these limits return truncated results.

4. **Token per request** — The CF proxy fetches a fresh OAuth bearer token from BTP Destination Service for each request. For production, implement token caching.

5. **LLM aggregation** — Spend totals, PO counts, and averages are computed by the LLM or orchestrator from row-level data, not by OData `$apply` aggregation. Results are accurate for the returned rows but may not reflect the full dataset if the row cap was hit.

---

## 📦 Dependencies

```
flask
requests
```
