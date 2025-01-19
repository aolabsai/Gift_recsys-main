import requests
import os

# Define the base URL (local or deployed depending on the environment)
# Use the 'PORT' environment variable (which Render sets) or default to 5000 for local development
host = "http://10.217.11.42"  # Localhost for development
port = os.getenv("PORT", 5000)  # Get the port from the environment (default to 5000)
url = f"{host}:{port}/"  # Full URL

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
