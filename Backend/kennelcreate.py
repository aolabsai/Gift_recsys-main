import requests

gist = "https://gist.githubusercontent.com/Rafipilot/8fc2d8549f9fc7433c0ce01abe7b26d6/raw/52a6857097887b5b38c5433591ef4d934b0ca7b6/gistfile1.txt"

url = "https://api.aolabs.ai/v0dev/kennel"

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "X-API-KEY": "api_key_here"
}

payload = {
    "kennel_name": "recommender3",
    "arch_URL": gist,
    "description": "Basic Recommender System",
    "permissions": ""
}

response = requests.post(url, headers=headers, json=payload)
print(response.text)