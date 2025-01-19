import requests
import os

url = "https://gift-recsys.onrender.com"  


try:
    # Make a simple GET request to the Flask app
    response = requests.get(url)

    # Check if the response status code is 200 (OK)
    if response.status_code == 200:
        print("Success! The Flask app responded correctly.")
        print("Response text:", response.text)
    else:
        print(f"Failed! Received status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print("Error while trying to reach the Flask app:", e)
