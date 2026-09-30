# Module 2 — Governed Live-Data Answers from SAP S/4HANA

## Overview

This solution demonstrates how to answer natural language procurement questions using **live data from SAP S/4HANA** through SAP BTP services. 

**Use case:** BestRun Technologies — Helios Supplier QBR Pre-Preparation  
Maria Schneider, Senior Procurement Manager, queries live SAP S/4HANA data to prepare for a supplier Quarterly Business Review.

---

## Architecture

```
Notebook ---- HTTPS ----> s4_connectivity.py (CF App on SAP BTP Cloud Foundry)
                                ├── /odata  ──► BTP Destination Service ──► Cloud Connector ──► S/4HANA 
                                └── /fetch_data  (standalone test endpoint)

AI Core (GPT-5) ──► called directly from notebook using client_credentials OAuth
```

---

## Repository Structure

```
├── s4_connectivity.py              # CF app — S/4HANA connection via BTP Connectivity
├── manifest.yaml                   # CF deployment manifest
├── requirements.txt                # Python dependencies
├── runtime.txt                     # Python version (3.11.15)
├── module2_implementation.ipynb    # Main workshop notebook
└── README_MODULE2.md               # This file
```

---

## Components

### 1. `s4_connectivity.py` — CF S/4HANA Connectivity App

A Flask app deployed to SAP BTP Cloud Foundry that handles all S/4HANA connectivity:

- **`/odata`** — Dynamic OData endpoint. Accepts `dest`, `path`, `client`, and any `$`-prefixed OData parameters. Routes through BTP Destination Service → Cloud Connector → S/4HANA.
- **`/fetch_data`** — Standalone test endpoint using `DESTINATION` and `SAP_CLIENT` env vars.

**Key design:**
- Uses `http.client.HTTPConnection` directly (not `requests`) to avoid `urllib3` stripping `Proxy-Authorization` headers on HTTP targets
- Reads `CloudConnectorLocationId` from destination config and sends `SAP-Connectivity-SCC-Location_ID` header
- Handles HTTP 30x redirects while preserving `sap-client` query parameter

### 2. `module2_implementation.ipynb` — Workshop Notebook

Jupyter notebook running in SAP Build Code with two governed read-only operations:

| Operation | What it answers | SAP Data |
|---|---|---|
| `get_po_exposure` | Open/overdue PO schedule lines | EKKO + EKET via `API_PURCHASEORDER_2` |
| `get_inventory` | Material stock by type and location | MARD via `API_MATERIAL_STOCK_SRV` |

---

## BTP Services Required

| Service | Purpose | Binding |
|---|---|---|
| Destination Service | Lookup S/4HANA destination config (URL, credentials, Location ID) | `module2_VCAP` |
| Connectivity Service | Proxy host/port + OAuth token for Cloud Connector tunnel | `module2_connectivity_service` |

AI Core credentials are provided via `.env` file (not CF-bound).

---

## SAP S/4HANA OData APIs Used

| API | Entity | SAP Tables | Used for |
|---|---|---|---|
| `API_PURCHASEORDER_2` (OData v4) | `PurchaseOrder` | EKKO | Supplier → PO number lookup |
| `API_PURCHASEORDER_2` (OData v4) | `PurchaseOrderScheduleLine` | EKET | Open/overdue schedule lines |
| `API_MATERIAL_STOCK_SRV` (OData v2) | `A_MatlStkInAcctMod` | MARD | Stock by type and storage location |

### Key field mappings

| OData Field | SAP Table.Field | Meaning |
|---|---|---|
| `Supplier` | EKKO.LIFNR | Supplier ID (on PO header, not schedule line) |
| `ScheduleLineDeliveryDate` | EKET.EINDT | Operational due date — drives overdue classification |
| `SchedLineStscDeliveryDate` | EKET.SLFDT | Statistics-relevant date — for KPI (not used, requires GR date) |
| `ScheduleLineOrderQuantity` | EKET.MENGE | Scheduled quantity |
| `OpenPurchaseOrderQuantity` | EKET.MENGE - EKET.WEMNG | Remaining open quantity |
| `MatlStkInAcctMod` | MARD.LABST | Unrestricted stock — hard available |
| `QualInspectionStock` | MARD.INSME | Quality inspection stock — conditional |
| `BlockedQuantity` | MARD.SPEME | Blocked stock — unavailable |

---

## Business Rules (defined in code, not in LLM prompt)

- **Open line** = `OpenPurchaseOrderQuantity > 0`
- **Overdue** = `ScheduleLineDeliveryDate < today` AND `OpenPurchaseOrderQuantity > 0`
- **Upcoming** = `ScheduleLineDeliveryDate >= today` AND `OpenPurchaseOrderQuantity > 0`
- **Unrestricted stock** = always usable
- **Quality inspection stock** = conditional — requires positive usage decision before use
- **Blocked stock** = unavailable

---

## Setup

### 1. BTP Destination (`RI4_400`)

| Property | Value |
|---|---|
| URL | `http://<host>:<port>` |
| Proxy Type | `OnPremise` |
| Authentication | `BasicAuthentication` |
| User | `<sap_user>` |
| Password | `<sap_password>` |
| CloudConnectorLocationId | `<location_id>` (if SCC uses non-default location) |

### 2. Cloud Connector

- Protocol: `HTTPS` (if backend uses HTTPS port)
- Internal host/port must match the destination URL
- Server certificate imported into SCC Trusted CAs
- Resources: `/` with all sub-paths


### 4. `.env` file (for notebook in Build Code)

```
AICORE_AUTH_URL=https://<subaccount>.authentication.<region>.hana.ondemand.com
AICORE_CLIENT_ID=<client_id>
AICORE_CLIENT_SECRET='<client_secret>'
GPT5_DEPLOYMENT_URL=https://api.ai.prod.eu-central-1.aws.ml.hana.ondemand.com/v2/inference/deployments/<deployment_id>
DESTINATION=RI4_400
SAP_CLIENT=400
```

### 5. Deploy CF App

```sh
cf login
cf push
```

### 6. Verify connectivity

```
GET https://<app-url>/fetch_data
```

Should return schedule line data from S/4HANA.

---

## Running the Notebook

1. Upload `module2_implementation.ipynb` and `.env` to SAP Build Code project
2. Run **Step 1** (install packages) → restart kernel
3. Run **Steps 2–6** (imports, config, LLM, S/4HANA helper, smoke tests)
4. Run **Steps 7–10** (operations, tools, prompt, orchestrator)
5. Run **Step 11** (questions)

---

## Known Limitations

1. **Supplier performance KPI** — not implemented. Requires actual goods receipt date (`EKBE.BUDAT`) which is not exposed on `PurchaseOrderScheduleLine`. The `PurchaseOrderHistory` entity would be needed for accurate OTD calculation.

2. **Supplier field on schedule line** — `Supplier` (EKKO.LIFNR) is on the PO header entity, not on `PurchaseOrderScheduleLine`. Supplier filtering requires a two-step lookup: header → PO numbers → schedule lines.

3. **Batch size** — PO number filters are batched in groups of 5 to avoid URL length limits. Suppliers with many POs may result in multiple OData calls.

4. **Stock data** — requires `API_MATERIAL_STOCK_SRV` to be activated on the S/4HANA system (`/n/IWFND/V4_ADMIN` or `/n/IWFND/MAINT_SERVICE`).

---

## Dependencies

```
flask==2.3
requests
cfenv
```
