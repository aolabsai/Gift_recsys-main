import requests

# Replace with your Flask app's endpoint
base_url = "http://127.0.0.1:5000"  # Change to 10.217.143.178:5000 if testing on network

# Try a basic GET request to the root endpoint
def test_flask_server():
    try:
        response = requests.get(base_url)
        
        if response.status_code == 200:
            print(f"Success! Flask app is running at {base_url}")
            print(f"Response from the server: {response.text}")
        else:
            print(f"Failed to reach Flask app. Status code: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error while trying to reach Flask app: {e}")

# Run the test
test_flask_server()
