# Workshop Day: Connection Credentials

<!-- TODO: Replace placeholder values with actual credentials before the workshop day. Remove this file from the repository after the event. -->

> [!IMPORTANT]
> **This file will be updated with connection details during the workshop. It is not available until then.**

## SAP BTP Destination Configuration

| Property | Value |
|---|---|
| Name | `BDC-AI-Data-Foundation` |
| Type | `HTTP` |
| URL | `https://bdc-ac-dsp.eu10.hcs.cloud.sap` |
| Proxy Type | `Internet` |
| Authentication | `OAuth2ClientCredentials` |
| Token Service URL | `https://bdc-ac-dsp.authentication.eu10.hana.ondemand.com/oauth/token` |
| Client ID | `sb-ead6cc68-47ca-4a4a-b391-616a3274a71b!b556820\|client!b3650` |
| Client Secret | `f8883986-468a-4b8c-8eaa-7057a7769ba6$5G8_P0_sp_KJNGTcMaGSbI3TJAdHdMliW8LQ4Y8D4bo=` |

## `.env` File

Copy and paste the following into your `.env` file:

```env
# ── AI Core / GenAI Hub ──────────────────────────────────────────────────────
# Source: BTP Cockpit → Instances → AI Core → Service Key
# These credentials authenticate with SAP AI Core to access the LLM deployment.
AICORE_AUTH_URL=https://mx-adoption-lab.authentication.eu10.hana.ondemand.com
AICORE_CLIENT_ID=sb-e7e2f3f2-e6f7-46f2-9822-990a4a48203e!b549051|aicore!b540
AICORE_CLIENT_SECRET='68a107b2-6f30-4b5d-8a55-957db05898a3$VhU3F6B0j1fKeB7Y637IQEC87u_UCFRLXA_ZQMAd8g8='

# ── LLM Deployment ───────────────────────────────────────────────────────────
# Source: AI Launchpad → Deployments → GPT-5 → Deployment URL
# This is the inference endpoint for the GPT-5 model hosted on SAP AI Core.
GPT5_DEPLOYMENT_URL=https://api.ai.prod.eu-central-1.aws.ml.hana.ondemand.com/v2/inference/deployments/dd903286e41187d5

# ── BTP Destination ──────────────────────────────────────────────────────────
# Source: BTP Cockpit → Connectivity → Destinations
# Points to your SAP Datasphere instance. The Cloud Foundry app uses this
# destination to route OData requests to Datasphere's consumption APIs.
DESTINATION=BDC-AI-Data-Foundation

# ── Cloud Foundry Proxy App ──────────────────────────────────────────────────
# Source: BTP Cockpit → Cloud Foundry → Applications → bdc-connection → Routes
# The middleware app that handles authentication and proxies OData calls
# from the notebook to SAP Datasphere via the BTP Destination Service.
BDC_PROXY_URL=
