import requests#
import dotenv
import os

aolabs_api_key = os.getenv("AOLABS_API_KEY")

gist = "https://gist.githubusercontent.com/Rafipilot/8fc2d8549f9fc7433c0ce01abe7b26d6/raw/689fda194eab6b786363fd92a047305193ab20cf/gistfile1.txt"

url = "https://api.aolabs.ai/v0dev/kennel"

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "X-API-KEY": "key here"
}

payload = {
    "kennel_name": "recommender4",
    "arch_URL": gist,
    "description": "Gift Recommender System",
    "permissions": ""
}

response = requests.post(url, headers=headers, json=payload)
print(response.text)