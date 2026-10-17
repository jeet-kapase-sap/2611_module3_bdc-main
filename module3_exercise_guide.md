# Module 3: Governed Business Context-Rich Answers from Multi-Source Data Products with SAP Business Data Cloud
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


## Prerequisite for Bring Your Own Tenant (BYOT)

> **Note:** This step is not required for SAP Sandbox Tenants, as they come preconfigured.

Before starting this exercise, ensure you have access to:

- **SAP Business Data Cloud & SAP Datasphere** — Admin and Modeler Roles.
- **SAP BTP** subaccount with the necessary roles.
- **SAP Build Code** (SAP Business Application Studio).
- A running **SAP AI Core** deployment with GPT-5 (or any model of your choice), including your deployment URL and service key (`clientid`, `clientsecret`, `url`, `AI_API_URL`).


- Activate SAP BDC Data Products `PurchaseOrder`, `PurchaseOrderItem`, `PurchaseOrderScheduleLine`, and `Supplier`.  
  Data Package: **SAP Sourcing and Procurement Data Products (SAP S/4HANA Cloud Private Edition)**. Refer to [SAP Business Data Cloud — Activating Data Products](https://help.sap.com/docs/business-data-cloud/administering-sap-business-data-cloud/activating-data-products) for detailed steps. 
  ![SAP BDC Data Products](images/bdcdataproducts.png)

- **Important — Before You Begin:** This exercise uses two SAP Datasphere spaces:
  - **SAP Managed:** `RI4400`
  - **Customer Managed:** `AI_DATA_CONTEXT_FOUNDATION`

  The pre-built tables, models, and external dataset are provided as `.json` and `.csv` files, located in the `others` folder of the repository. Before importing, update the Space IDs in the `.json` files to match your landscape. A direct as-is import will fail without this adjustment.

- Requesting SAP BDC Data Products `PurchaseOrder`, `PurchaseOrderItem`, `PurchaseOrderScheduleLine`, and `Supplier` Access into a SAP Datasphere space. Refer to [SAP Datasphere — Requesting Access to Data Products](https://help.sap.com/docs/SAP_DATASPHERE/c8a54ee704e94e15926551293243fd1d/ea7cb802cbea47b39a441888873c3a49.html) for detailed steps.  
  > **Note:** You can use an existing space, e.g. `AI_DATA_CONTEXT_FOUNDATION`  
  ![SAP Datasphere, Request SAP BDC Data Products 1](images/datasphererequestdp_1.png)  
  ![SAP Datasphere, Request SAP BDC Data Products 2](images/datasphererequestdp_2.png)  
  ![SAP Datasphere, Request SAP BDC Data Products 3](images/datasphererequestdp_3.png)

- In SAP Datasphere, Space `AI_DATA_CONTEXT_FOUNDATION`, import the following `.json` files:  
  ![SAP Datasphere, Import JSON Object](images/datasphereimportjson.png)
  1. `EXT_COUNTRY_RISK_INDEX.json`
  2. `IL_PO_ITEM.json`
  3. `V_SUPPLIER.json`
  4. `HL_PO_HISTORY.json`
  5. `V_SUPPLIER_RISK_SCORE.json`
  6. `AM_PO_HISTORY.json`
  7. `AM_SUPPLIER_RISK_SCORE.json`

- In SAP Datasphere Space `AI_DATA_CONTEXT_FOUNDATION`, navigate to the Local Table `EXT_COUNTRY_RISK_INDEX` and upload the CSV file `EXT_COUNTRY_RISK_INDEX.csv` (Country Risk Index dataset) located in the `others` folder of the repository.  
  > **Note:** If the dataset does not align with your business context, substitute it with a comparable reference dataset of your choice.  
  ![SAP Datasphere, Upload the data](images/datasphereuploadthedata.png)

- In SAP Datasphere, expose the following OData services for consumption. Ensure the analytical and relational endpoints are activated for Space `AI_DATA_CONTEXT_FOUNDATION`:

  | Object | Type | OData Endpoint |
  |--------|------|----------------|
  | `AM_PO_HISTORY` | Analytical | `/api/v1/datasphere/consumption/analytical/AI_DATA_FOUNDATION/AM_PO_HISTORY/AM_PO_HISTORY` |
  | `V_SUPPLIER` | Relational | `/api/v1/datasphere/consumption/relational/AI_DATA_FOUNDATION/V_SUPPLIER/V_SUPPLIER/SET` |
  | `AM_SUPPLIER_RISK_SCORE` | Analytical | `/api/v1/datasphere/consumption/analytical/AI_DATA_FOUNDATION/AM_SUPPLIER_RISK_SCORE/AM_SUPPLIER_RISK_SCORE` |

  > **Note:** To expose an OData service in SAP Datasphere, navigate to the respective Analytic Model or View, open the properties, and enable **Expose for Consumption**. Refer to [SAP Datasphere — Consuming Data via OData](https://help.sap.com/docs/SAP_DATASPHERE/43509d67b8b84e66a30851e832f66911/7a453609c8694b029493e7d87e0de60a.html) for detailed steps.
    ![SAP Datasphere, Expose for Consumption](images/generateodata1.png)

    ![SAP Datasphere, Generate Odata Request](images/generateodata2.png)


- An SAP BTP subaccount with the following services provisioned:
  - **Integration Between SAP Datasphere and SAP BTP Destination Service** Refer to [How to Consume SAP Datasphere Analytical Models Using OData Services: Part 1 and Part 2 sections only](https://community.sap.com/t5/technology-blog-posts-by-sap/how-to-consume-sap-datasphere-analytical-models-to-sap-fiori-using-odata/ba-p/14445184) for detailed steps.

  1. `Expose the Analytical Model for Consumption`
  2. `Establish Trust Between Datasphere and BTP`

      ![SAP BTP, Export XML IDP Trust Configuration](images/btpdestinationtrust.png)

      ![SAP Datasphere, Trusted Identity Providers](images/dataspheretrustedidp.png)


  3. `Configure OAuth in SAP Datasphere - Choose Oauth Client Purpose: API Access or Technical User that fits in your scenario`

      ![SAP Datasphere, OAuth Client_1](images/datasphereoauthclient1.png)

      ![SAP Datasphere, OAuth Client_2](images/datasphereoauthclient2.png)
  
  - **Destination Service** instance with a configured SAP Datasphere destination — Type: `HTTP`, Name: `BDC-AI-Data-Foundation`
    ![SAP BTP, Destination Service_1](images/btpdestinationservice1.png)

    ![SAP BTP, Destination Service_2](images/btpdestinationservice2.png)

  - **Connectivity Service** instance bound to the CF app — Service: `Destination Service`, Plan: `lite`, Runtime Environment: `Cloud Foundry`, Name: `module3_bdc`
    ![SAP BTP, Connectivity Service](images/btpconntectivityservice.png)

- The SAP BTP Cloud Foundry CLI (`cf`) installed and logged in.

- A GitHub account to clone the repository.

- Basic familiarity with Python and Jupyter notebooks.

## Architecture
![Module 3 Architecture](images/architecture.png)



## Section 1: Clone & Create the Application

### Open SAP Build Lobby
Before cloning the repository, you need a running SAP Business Application Studio / SAP Build Code dev space with Python support.
  1. In SAP Business Application Studio, create a new dev space
  2. Name your dev space (e.g., userxxFullStack)
  3. Select Full Stack Cloud Application as the application type
  4. Under Additional SAP Extensions, enable Python Tools
  5. Click Create Dev Space
<img width="1913" height="956" alt="image" src="https://github.tools.sap/user-attachments/assets/9c69e4c9-d414-4f78-8bdd-6c8b8b6f0ae9" />

Wait for the dev space to show RUNNING status, then click on the dev space name to open it.
<img width="1761" height="114" alt="image" src="https://github.tools.sap/user-attachments/assets/a35f89cd-fe9a-4711-919c-03aa5d512b54" />

### Step 1: Clone the Repository
Once your dev space is open in the editor, click Clone from Git.

<img width="2560" height="1226" alt="image" src="https://github.tools.sap/user-attachments/assets/21eae266-adac-4f9a-bd04-5b0af40c4973" />

### Step 2: Enter the Repository URL
In the dialog, enter the following GitHub repository URL:
``` 
https://github.tools.sap/IA-C/2611_module3_bdc-main.git
```
<img width="1292" height="663" alt="image" src="https://github.tools.sap/user-attachments/assets/eccd8752-1e08-4afc-8c86-bac3f3b8dccb" />


### Step 3: Open the Cloned Project
When prompted "Would you like to open the repository, or add it to the current workspace?", click Open.

<img width="1282" height="770" alt="image" src="https://github.tools.sap/user-attachments/assets/2038d3c5-4f9b-4282-bc93-923e9a8715c6" />

The project will open in SAP Business Application Studio

### Step 4: Create the Environment Configuration File
Now you'll create a .env file to store your AI Core credentials securely.
  1. In the Explorer panel, click on create a new file icon
  2. Name the file name as .env including the dot at the beginning)
<img width="1123" height="445" alt="image" src="https://github.tools.sap/user-attachments/assets/6d32de86-bf77-4c62-a360-86cf93fd35fe" />

The .env file is now created. In the next section, you'll fill it with your AI Core credentials.


> [!NOTE]
> The .env file stores sensitive credentials locally and is automatically excluded from version control by the .gitignore file. Never commit this file to Git.


## Section 6: Configure Jupyter and Python Extensions

  1. Open Jupyter Notebook module2_implementation.ipynb
<img width="304" height="439" alt="image" src="https://github.tools.sap/user-attachments/assets/cc5d8825-6123-4b18-a099-a3ed0ff90004" />

  2. Read through the notebook until you get to the first code cell in the Setup and configuration section.

  3. Run the first code cell to install the required python modules.

     > [!NOTE]
     > To execute a code cell, click the play icon beside the cell. It is also possible to execute it by clicking into the code cell and pressing Shift+Enter.

<img width="444" height="87" alt="image" src="https://github.tools.sap/user-attachments/assets/f574c63b-a048-45d6-bc21-efe02bbc8247" />

  4. On the next screen, choose the recommended Python 3.13.
<img width="600" height="175" alt="image" src="https://github.tools.sap/user-attachments/assets/674be8e4-646c-4c95-9ac6-0c98948fe6b1" />

  5. The required libraries will now start installing. Once the libraries have been successfully installed, the kernel must be restarted. Choose Restart in the menu on the top.
<img width="730" height="399" alt="image" src="https://github.tools.sap/user-attachments/assets/fa05093e-b023-44d4-b34b-bb380ffc5b5a" />

  6. On the following pop-up window, Choose Restart. It will take a few seconds for the kernel to restart. After it restarts, the environment is ready for use!
<img width="523" height="164" alt="image" src="https://github.tools.sap/user-attachments/assets/951f583a-d16c-4f08-a70c-847c38ac34a4" />

  7. Follow the step-by-step instructions provided in the Jupyter Notebook to complete the remaining parts of the exercise.

