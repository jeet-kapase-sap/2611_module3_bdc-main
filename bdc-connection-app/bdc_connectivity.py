# ==============================================================================
#  Module 3 — BDC Connectivity Proxy App
#  File: bdc_connectivity.py
#
#  A lightweight Flask app deployed on Cloud Foundry (BTP) that proxies
#  OData requests from the notebook to SAP Datasphere via BTP Destination Service.
#
#  Flow: Notebook → this app (/odata) → BTP Destination Service → SAP Datasphere
#
#  Why a proxy?
#  - The notebook cannot call Datasphere directly — it lacks the OAuth2
#    token exchange that BTP Destination Service handles.
#  - This app reads destination credentials from VCAP_SERVICES (injected
#    by CF when bound to the Destination Service instance), fetches a
#    bearer token, and forwards the OData request to Datasphere.
#
#  Deploy: cf push (uses manifest.yaml)
#  Test:   https://<app-route>/fetch_data (returns 1 row from AM_PO_HISTORY)
# ==============================================================================

from flask import Flask, jsonify, request
import os
import requests
import json
from urllib.parse import quote, urlencode

app = Flask(__name__)
cf_port = os.getenv("PORT")

# ── Registered Datasphere OData service paths ─────────────────────────────────
# These map short service names to their full Datasphere consumption API paths.
# Used by the /odata?service=<name> shorthand so the notebook doesn't need
# to pass full paths every time.
SERVICES = {
    "AM_PO_HISTORY": "/api/v1/datasphere/consumption/analytical/AI_DATA_FOUNDATION/AM_PO_HISTORY/AM_PO_HISTORY",
    "V_SUPPLIER": "/api/v1/datasphere/consumption/relational/AI_DATA_FOUNDATION/V_SUPPLIER/V_SUPPLIER/SET",
    "AM_SUPPLIER_RISK_SCORE": "/api/v1/datasphere/consumption/analytical/AI_DATA_FOUNDATION/AM_SUPPLIER_RISK_SCORE/AM_SUPPLIER_RISK_SCORE",
}


# ── Authentication ─────────────────────────────────────────────────────────────

def get_oauth_token(credentials):
    """
    Exchange client credentials for an OAuth2 access token.
    Used to authenticate with the BTP Destination Service API.
    Credentials come from VCAP_SERVICES (injected by CF service binding).
    """
    resp = requests.post(
        credentials['url'] + "/oauth/token",
        data={
            'grant_type': 'client_credentials',
            'client_id': credentials['clientid'],
            'client_secret': credentials['clientsecret'],
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    resp.raise_for_status()
    return resp.json()['access_token']


def get_destination_config(dest_name):
    """
    Fetch destination configuration + auth token from BTP Destination Service.

    Steps:
    1. Read Destination Service credentials from VCAP_SERVICES
    2. Get an OAuth token for the Destination Service itself
    3. Call the Destination Service API to get the target destination config
       (URL, auth tokens for Datasphere)

    Returns dict with:
    - destinationConfiguration: URL, auth type, etc.
    - authTokens: pre-fetched bearer token for the target system (Datasphere)
    """
    vcap = json.loads(os.getenv("VCAP_SERVICES"))
    dest_creds = vcap['destination'][0]['credentials']
    dest_svc_token = get_oauth_token(dest_creds)
    resp = requests.get(
        f"{dest_creds['uri']}/destination-configuration/v1/destinations/{dest_name}",
        headers={"Authorization": f"Bearer {dest_svc_token}"}
    )
    resp.raise_for_status()
    return resp.json()


# ── Datasphere OData call ─────────────────────────────────────────────────────

def call_datasphere(dest_name, path):
    """
    Execute an OData GET request against SAP Datasphere.

    Steps:
    1. Resolve the BTP Destination → get Datasphere base URL + bearer token
    2. Append the OData path (with query params) to the base URL
    3. Call Datasphere with the bearer token
    4. Return the JSON response

    The bearer token is fetched fresh each call via the Destination Service.
    For production, you'd cache this — but for a workshop proxy, simplicity wins.
    """
    dest_info = get_destination_config(dest_name)
    dest_config = dest_info['destinationConfiguration']

    # Extract the pre-fetched auth token for Datasphere
    auth_tokens = dest_info.get('authTokens', [])
    if not auth_tokens:
        raise Exception("Destination Service returned no auth tokens - check destination config")

    token_entry = auth_tokens[0]
    if token_entry.get('error'):
        raise Exception(f"Token error: {token_entry.get('error')}")

    bearer = token_entry['value']
    base_url = dest_config['URL'].rstrip('/')
    target_url = base_url + path

    resp = requests.get(
        target_url,
        headers={
            "Authorization": f"Bearer {bearer}",
            "Accept": "application/json",
        }
    )

    if resp.status_code >= 400:
        raise Exception(f"Datasphere error {resp.status_code}: {resp.text[:500]}")

    return resp.json()


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    """Health check + endpoint documentation."""
    return jsonify(
        status="ok",
        endpoints={
            "/fetch_data": "Smoke test - top 1 from AM_PO_HISTORY",
            "/odata?service=AM_PO_HISTORY&$top=1": "Query a registered service by name",
            "/odata?path=/api/v1/...&$top=1": "Query with a custom OData path",
        }
    )


@app.route('/fetch_data')
def fetch_data():
    """
    Quick smoke test — fetches 1 row from AM_PO_HISTORY.
    Hit this URL in a browser after cf push to verify the full chain works:
    Notebook → CF App → Destination Service → Datasphere
    """
    dest = os.getenv("DESTINATION")
    if not dest:
        return jsonify(error="DESTINATION env var not set"), 400
    try:
        path = SERVICES["AM_PO_HISTORY"] + "?$top=1"
        data = call_datasphere(dest, path)
        return jsonify(data)
    except Exception as e:
        return jsonify(error=str(e)), 502


@app.route('/odata')
def odata():
    """
    Main OData proxy endpoint — called by bdc_get() in the notebook.

    Two modes:
    1. By service name:  /odata?service=AM_PO_HISTORY&$top=10
       → Resolves to the registered path in SERVICES dict

    2. By full path:     /odata?path=/api/v1/datasphere/...&$top=10
       → Uses the path as-is (for custom or ad-hoc queries)

    All query params starting with $ are forwarded as OData parameters
    ($filter, $select, $orderby, $top, etc.)
    """
    dest = request.args.get('dest') or os.getenv("DESTINATION")
    service = request.args.get('service')
    path = request.args.get('path')

    # Resolve the OData base path
    if service:
        if service not in SERVICES:
            return jsonify(error=f"Unknown service '{service}'", available=list(SERVICES.keys())), 400
        base_path = SERVICES[service]
    elif path:
        base_path = path
    else:
        return jsonify(error="Provide ?service=<name> or ?path=<odata_path>", available=list(SERVICES.keys())), 400

    # Collect OData query parameters ($filter, $top, $select, etc.)
    odata_params = {k: v for k, v in request.args.items() if k.startswith('$')}

    # Append OData params to the path
    if odata_params:
        qs = urlencode(odata_params)
        full_path = base_path + ('&' if '?' in base_path else '?') + qs
    else:
        full_path = base_path

    try:
        data = call_datasphere(dest, full_path)
        return jsonify(data)
    except Exception as e:
        return jsonify(error=str(e)), 502


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if cf_port is None:
        # Local development
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        # Cloud Foundry — port assigned by the platform
        app.run(host='0.0.0.0', port=int(cf_port), debug=False)
