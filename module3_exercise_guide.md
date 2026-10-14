# Module 2: Governed Business Context-Rich Answers from Multi-Source Data Products with SAP Business Data Cloud
## Introduction

In this exercise, you'll understand how SAP Business Data Cloud data products serve as the governed data layer for AI-powered analytics, SAP-delivered data products (PurchaseOrder, Supplier) and custom products (Supplier Risk Score) are pre-modeled and ready to consume using SAP Generative AI Hub and SAP BTP connectivity services. The assistant answers natural language questions over governed, multi-source data, from basic single-service queries to complex three-service analytical questions spanning PO history, supplier master, and risk scores with no hallucination.

You'll learn how to:
### Demo Section
- SAP Business Data Cloud, Data Products.
- SAP Datasphere, Analytic Models & Views Governed Layer with SAP and Non-SAP data sources.
- SAP Datasphere, V4 Odata Consumption Services.
- Configure SAP BTP Destination service to estabilish secure connection with SAP Datasphere.

### Hands-on Section
- Connect SAP AI Core (GPT-5) to extract business parameters from natural language questions Connect an AI agent to SAP Business Data Cloud through a Cloud Foundry proxy app using BTP Destination Service and OData services exposed from SAP Datasphere.
- Design governed business operations that map natural language questions to the right OData service: AM_PO_HISTORY for spend/delivery, V_SUPPLIER for master data, AM_SUPPLIER_RISK_SCORE for risk analytics.
- Author LLM tool schemas that reflect data product semantics:expose the right fields, guide the LLM to use pre-computed measures (e.g., CountPurchaseOrder) instead of counting raw rows, and set appropriate parameter constraints.
- Build a system prompt that teaches the LLM domain context:risk scoring logic (weighted dimensions), aggregation rules, and multi-service orchestration pattern.
- Orchestrate multi-round, multi-service LLM tool calls: the LLM autonomously chains calls across three services (e.g., get risk scores → resolve supplier names → combine into a single answer) without human intervention.
- Ask natural language questions over governed, multi-source data, from basic single-service queries to complex three-service analytical questions spanning PO history, supplier master, and risk scores.

### 🏗️ Architecture: Module 3 SAP BDC Data Products Connectivity with Business context and semantics

```
┌─────────────────┐         HTTPS           ┌─────────────────────────────────────┐
│                 │ ──────────────────────► │  bdc_connectivity.py                │
│    Notebook     │                         │  (Cloud Foundry App on SAP BTP)     │
│                 │ ◄────────────────────── │                                     │
│                 │        JSON Response    └──────────┬──────────────────────────┘
└─────────────────┘                                    │
                                                       │  /odata
                                                       ▼
                                          ┌─────────────────────────────┐
                                          │  BTP Destination Service    │
                                          │  (Credentials + Routing)    │
                                          └──────────┬──────────────────┘
                                                     │
                                                     ▼
                                          ┌─────────────────────────────┐
                                          │    SAP Datasphere           │
                                          │    (OData V2/V4 Service)    │
                                          └──────────┬──────────────────┘
                                                     │
                                                     ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                SAP Datasphere — Analytic Models & Views                        │
│                                                                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────────────────┐   │
│  │ AM_PO_HISTORY    │  │ V_SUPPLIER       │  │ AM_SUPPLIER_RISK_SCORE      │   │
│  │ (PO Fact)        │  │ (Supplier Dim)   │  │ (Risk Fact)                 │   │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────┬──────────────────┘   │
│           │                     │                       │                      │
│           │                     │                       │                      │ 
│           │                     │                       │                      │
│           ▼                     ▼                       ▼                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                SAP BDC Data Products (SAP Sources)                      │   │
│  │                                                                         │   │
│  │  ┌───────────────────┐ ┌───────────────────┐ ┌──────────────────────┐   │   │
│  │  │ PurchaseOrder     │ │PurchaseOrderItem  │ │PurchaseOrder         │   │   │
│  │  │                   │ │                   │ │ScheduleLine          │   │   │
│  │  └───────────────────┘ └───────────────────┘ └──────────────────────┘   │   │
│  │                                                                         │   │
│  │  ┌───────────────────┐                                                  │   │
│  │  │ Supplier          │                                                  │   │
│  │  └───────────────────┘                                                  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                External Data (Non-SAP Sources)                          │   │
│  │                                                                         │   │
│  │  ┌──────────────────────────────┐                                       │   │
│  │  │ EXT_COUNTRY_RISK_INDEX       │                                       │   │
│  │  │ (Country Risk Scores, CSV)   │                                       │   │
│  │  └──────────────────────────────┘                                       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────┘
```


## Prerequisite for Bring Your Own Tenant (BYOT) (Note: This step is not required for SAP Sandbox Tenants, as they come preconfigured.)

Before starting this exercise, ensure you have:

  - Access to SAP Business Data Cloud, SAP Datasphere - Admin and Modeler Roles.
  - Installed SAP Data Products PurchaseOrder, PurchaseOrderItem, PurchaseOrderScheduleLine and Supplier into a SAP Datasphere space.
  - Your SAP AI Core service key (clientid, clientsecret, url, AI_API_URL)
  - An SAP BTP subaccount with the following services provisioned:
    - Destination Service instance with a configured SAP Datasphere destination. Type: HTTP and Name it as BDC-AI-Data-Foundation
    - Connectivity Service instance bound to the CF app. Service: Destination Service, Plan lite, Runtime Environment: Cloud Foundry and Name it as module3_bdc
  - The SAP BTP Cloud Foundry CLI (cf) installed and logged in
  - A GitHub account to clone the repository
  - Basic familiarity with Python and Jupyter notebooks

## Architecture
![Module 3 Architecture](images/architecture.png)
