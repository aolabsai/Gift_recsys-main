import requests

url = "https://api.aolabs.ai/v0dev/kennel/agent"

LABEL = "0000000000"

payload = {
    "kennel_id": "gift-recsys-1",  # use kennel_name entered above
    "agent_id": "test123",   # enter unique user IDs here, to call a unique agent for each ID
    "INPUT": "0000000000000000",  

    "LABEL": LABEL,
    "control": {
        "US": True,
        "states": 1,
    }
}

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "X-API-KEY": "KzZbXbaahd1ElPO5Rtyv3a1ejHlw3Kn848c9SA1J"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)
