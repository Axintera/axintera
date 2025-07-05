# test_client.py
import requests
import json

# The RFD we want to fulfill. It uses the "reduce_avg" service that our solver provides.
rfd = {
    "service": "reduce_avg",
    "records": [
        {"x": 10, "y": 20, "z": 5},
        {"x": 2,  "y": 10, "z": 15}
    ]
}

# We send the request to the MAIN network server (the mock MCP server)
# It will be responsible for finding our solver and forwarding the request.
mcp_server_url = "http://localhost:8000/fulfill"

print(f"Sending RFD to MCP Server at {mcp_server_url}")
print("--- RFD ---")
print(json.dumps(rfd, indent=2))
print("-----------")

try:
    response = requests.post(mcp_server_url, json=rfd, timeout=10)
    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

    print("\n--- ✅ SUCCESS: Got Response ---")
    print(json.dumps(response.json(), indent=2))
    print("------------------------------")

except requests.exceptions.RequestException as e:
    print(f"\n--- ❌ ERROR ---")
    print(f"Request failed: {e}")
    if e.response:
        print(f"Response Status: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")
    print("------------------")