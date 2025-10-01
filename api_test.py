import requests
import time
import hmac
import hashlib

# --- Your API Credentials ---
# For this test, your keys are placed directly in the script.
api_key = "jucNYGEH33v5alHOyI"
api_secret = "TrzNeE9de4oYHgrzWkSuCGfP0cIPDqSnKZTM"

# --- Configuration ---
# Set to False to use the mainnet, or True for the testnet.
use_testnet = False
base_url = "https://api-demo.bybit.com" if use_testnet else "https://api.bybit.com"

def generate_signature(timestamp, api_key, recv_window, query_string, api_secret):
    """Generates the HMAC-SHA256 signature for the request."""
    payload = timestamp + api_key + recv_window + query_string
    return hmac.new(
        api_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

# --- API Request Details ---
# Endpoint to test. /v5/market/tickers is a good choice for checking market data access.
endpoint = "/v5/market/tickers"
params = {"category": "spot"}

# --- Prepare and Send Request ---
timestamp = str(int(time.time() * 1000))
recv_window = "10000"  # 10 seconds
query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])

# Generate the signature.
signature = generate_signature(timestamp, api_key, recv_window, query_string, api_secret)

# Prepare headers.
headers = {
    "X-BAPI-API-KEY": api_key,
    "X-BAPI-TIMESTAMP": timestamp,
    "X-BAPI-RECV-WINDOW": recv_window,
    "X-BAPI-SIGN": signature,
}

# Construct the full URL.
url = base_url + endpoint

print("--- Sending Request ---")
print(f"URL: {url}")
print(f"Params: {params}")
print("-----------------------")

try:
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
    data = response.json()
    print("\n--- Response ---")
    print(data)
    print("--------------------")
    if data.get("retCode") == 0:
        print("\n✅ Success! Connection to Bybit API is working.")
    else:
        print(f"\n❌ Bybit API Error: {data.get('retMsg')} (Return Code: {data.get('retCode')})")
except requests.exceptions.RequestException as e:
    print(f"\n❌ Connection Error: {e}")
