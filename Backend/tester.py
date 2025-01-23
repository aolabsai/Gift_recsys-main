from dotenv import load_dotenv
import os
import http.client
import requests

load_dotenv()

rapid_key = os.getenv("RAPID_KEY")

conn = http.client.HTTPSConnection("real-time-amazon-data.p.rapidapi.com")
headers = {
    'x-rapidapi-key': rapid_key,
    'x-rapidapi-host': "real-time-amazon-data.p.rapidapi.com"
}