from flask import Flask, request, jsonify, redirect, session
import jwt
import datetime
import google.auth.transport.requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

import random
from openai import OpenAI
import json
import re
import numpy as np
import http.client
from urllib.parse import quote

from dotenv import load_dotenv
import embedding_bucketing.embedding_model_test as em

from flask_cors import CORS
import google.auth

from firebase_admin import credentials, auth
import firebase_admin
from firebase_admin import firestore
import numpy as np
import os
import requests
import time

endpoint = "https://gift-recsys.onrender.com"  # change to https://gift-recsys.onrender.com for prod and http://127.0.0.1:5000 for local 
frontend_url = "https://gift-recsys-main.onrender.com/"   #change to http://localhost:5174/ for local and  https://giftrec.aolabs.ai/ for prod

app = Flask(__name__)
app.secret_key = "super_secret_key"
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5174",
    "https://gift-recsys-main.onrender.com",
    "https://giftrec.aolabs.ai"
])

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

load_dotenv()

ao_endpoint_url = "https://api.aolabs.ai/v0dev/kennel/agent"

openai_key = os.getenv("OPENAI_KEY")
rapid_key = os.getenv("RAPID_KEY")

firebase_sdk = json.loads(os.getenv("FIREBASE_SDK")) 
firebase_apikey = os.getenv("firebase_apikey")

JWT_SECRET_KEY = 'your_secret_key'
JWT_ALGORITHM = 'HS256'
#Set up google oauth
google_client = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")


aolabs_key = os.getenv("AOLABS_API_KEY")
kennel_id = "recommender4"

cred = credentials.Certificate(firebase_sdk)
firebase_admin.initialize_app(cred)



db = firestore.client()


flow = Flow.from_client_config(
    {
        "web": {
            "client_id": google_client,
            "client_secret": google_client_secret,
            "redirect_uris": [f"{endpoint}/callback"], 
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
)
with open("google-countries.json") as f:
    country_data = json.load(f)

client = OpenAI(api_key=openai_key)
em.config(openai_key)

possible_genres = ["Clothes", "Electronics", "Books", "Children Toys", "Jewelry", "Home", "Beauty", "Sports", "Food", "Music", "Movies", "Games", "Art", "Travel", "Pets", "Health", "Fitness", "Tech", "DIY", "Gardening", "Cooking", "Crafts", "Cars", "Outdoors", "Office", "School", "Baby", "Party", "Wedding", "Grooming", "Drama Book", "Dolls", "Purse", "Wallet", "Chocolates", "Makeup"]

targets = ["Unisex", "Adult Male", "Adult Female","Female Teenager","Male Tennager", "Children/ Kids"]

amazon_categories = ["Clothing, Shoes & Jewelry", "Electronics", "Books", "Toys & Games", "Jewelry", "Home & Kitchen", "Beauty & Personal Care", "Sports & Outdoors", "Grocery & Gourmet Food", "Music", "Movies & TV", "Video Games", "Arts, Crafts & Sewing", "Luggage & Travel Gear", "Pet Supplies", "Health & Household", "Exercise & Fitness", "Tech", "DIY & Tools", "Gardening", "Cooking", "Crafts", "Automotive", "Outdoors", "Office Products", "School Supplies", "Baby", "Party Supplies", "Wedding Supplies", "Grooming", "Drama Books", "Dolls", "Purse", "Wallet", "Chocolates"]
##TODO add more types

#init embedding bucketing
cache_targets, bucket_targets = em.init("embedding_targets_cache", targets)
cache_categories, bucket_categories = em.init("embedding_categories_cache", amazon_categories)
cache, bucket = em.init("embedding_cache", possible_genres)

agent = None



def listTostring(s):
    return ''.join(map(str,s)) 

def stringTolist(s):
    return [int(i) for i in s]

def generate_token(user_email):
    payload = {
        'email': user_email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expires in 1 hour
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def trainAgentCall(Input, Label, email, name_of_agent):
    Input = listTostring(Input)
    Label = listTostring(Label)
    email = email.lower()
    uid = email+name_of_agent
    print("training agent with uid", uid)
    payload = {
    "kennel_id": kennel_id, 
    "agent_id": uid,   
    "INPUT": Input,  

    "LABEL": Label,
    "control": {
        "US": True,
        "states": 1,
    }
}

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-KEY": f"{aolabs_key}"
    }

    response = requests.post(ao_endpoint_url, json=payload, headers=headers)
    print("Agent response: ", response.json())


def agentDelete(email, name_of_agent):
    uid= email+name_of_agent

    payload = {
        "kennel_id": kennel_id,
        "agent_id": uid,
        "request": "delete_agent"
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-KEY": f"{aolabs_key}"
    }
    response = requests.post(ao_endpoint_url, json=payload, headers=headers)
    print("Agent delete response: ", response.text)

def agentResponse(Input, email, name_of_agent):
    email = email.lower()

    uid = email+name_of_agent
    Input = listTostring(Input)
    print("calling agent with uid: ", uid)
    payload = {
    "kennel_id": kennel_id, 
    "agent_id": uid,  
    "INPUT": Input,  

    "control": {
        "US": True,
        "states": 1,
    }
}

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-KEY": f"{aolabs_key}"
    }

    response = requests.post(ao_endpoint_url, json=payload, headers=headers)
    print("Agent response: ", response.json())
    return stringTolist(response.json()["story"])

@app.route("/login_with_google")
def login_with_google():
    """
    Initiates the Google OAuth2 login flow and returns the authorization URL.
    """
    flow.redirect_uri = f"{endpoint}/callback"  # Adjust redirect URI
    auth_url, state = flow.authorization_url()
    
    # Store the state in the session for later validation
    session["oauth_state"] = state
    print("session", session)
    return jsonify({"url": auth_url})

@app.route("/callback")
def callback():
    """
    Handles the callback from Google OAuth, verifies the token, and redirects the user with JWT.
    """
    stored_state = session.get("email")  # Corrected variable name
    received_state = request.args.get("state")
    print("session", session)


    # Fetch the token from the authorization response
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    # Verify the ID token from Google
    idinfo = id_token.verify_oauth2_token(
        credentials.id_token, Request(), google_client
    )
    
    email = idinfo["email"]

    # Generate a JWT token with user info
    payload = {
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expires in 1 hour
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    # Redirect the user to the frontend with the token in the query parameter
    return redirect(f"{frontend_url}/auth?token={token}")


@app.route("/check_login")
def check_login():
    """
    Checks the login status by verifying the JWT token sent by the client.
    """
    token = request.headers.get("Authorization")
    if token:
        token = token.replace("Bearer ", "")  # Remove 'Bearer ' prefix
        
        try:
            # Decode the token to verify its validity
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            email = payload.get('email')
            
            # Return user info (email) if token is valid
            return jsonify({"status": "authenticated", "email": email})
        
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
    else:
        return jsonify({"status": "not_authenticated"}), 401


@app.route('/get-gift-categories', methods=['POST'])
def get_gift_categories():
    data = request.json["data_to_send"]
    print(data)
    budget = data["budget"]
    aiu = data["agentInUse"]
    email = aiu[0]
    name_of_agent = aiu[1]
    occassion = data["occasion"]
    season = data["season"]

    agent_ref = db.collection('Agents').where('email', '==', email).where('name', '==', name_of_agent).stream()
    
    agent_data = None
    agent_document_id = None
    for agent in agent_ref:
        agent_data = agent.to_dict()  
        agent_document_id = agent.id  

    if not agent_data:
        print("Agent not found for", email, name_of_agent)
        return jsonify({"error": "Agent not found for the given email and name"}), 400
    
    print("Found agent with document ID:", agent_document_id)


    age = db.collection('Agents').document(agent_document_id).get().to_dict().get('age')
    gender = db.collection('Agents').document(agent_document_id).get().to_dict().get('country')
    country = db.collection('Agents').document(agent_document_id).get().to_dict().get('gender')#
    info_about_person = db.collection('Agents').document(agent_document_id).get().to_dict().get('extraInfo')
    print(age, gender, country, info_about_person)
    prompt = f"What are some gift categories from amazon that meet the following: age: {age}, gender: {gender}, budget: {budget}, occassion: {occassion}, season: {season} extra info: {info_about_person}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "give a 5 options answer each only a couple of words long, DO NOT give books please!"}, #not using books as its terrible lol
            {"role": "user", "content": prompt}
        ],
        max_tokens=35,
        temperature=0.1
    )
    gift_categories = response.choices[0].message.content.splitlines()
    print("Gift cats: ",gift_categories) 
    return jsonify({"categories": gift_categories})

@app.route('/get-product', methods=['POST'])
def get_random_product():
    data = request.json
    query = data.get("query", "")
    budget = data.get("budget", 50)
    min_price = int(budget)*0.5

    aiu = data["agentInUse"]
    email = aiu[0]
    name_of_agent = aiu[1]

    agent_ref = db.collection('Agents').where('email', '==', email).where('name', '==', name_of_agent).stream()
    
    agent_data = None
    agent_document_id = None
    for agent in agent_ref:
        agent_data = agent.to_dict()  
        agent_document_id = agent.id  

    if not agent_data:
        print("Agent not found for", email, name_of_agent)
        return jsonify({"error": "Agent not found for the given email and name"}), 400
    
    print("Found agent with document ID:", agent_document_id)


    age = db.collection('Agents').document(agent_document_id).get().to_dict().get('age')
    gender = db.collection('Agents').document(agent_document_id).get().to_dict().get('gender')

    query = re.sub(r'^\d+\.\s*', '', query).strip()
    encoded_query = quote(query)
    encoded_query = (encoded_query)
    
    print("Query: ", encoded_query)

    conn = http.client.HTTPSConnection("real-time-amazon-data.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': rapid_key,
        'x-rapidapi-host': "real-time-amazon-data.p.rapidapi.com"
    }

    for i in range(5):
        print(f"Attempt {i + 1}: Fetching products...")

        print("in try")
        conn.request("GET", f"/search?query={encoded_query}&page=1&country=US&sort_by=RELEVANCE&min_price={min_price}&max_price={budget}&product_condition=ALL&is_prime=false&deals_and_discounts=NONE", headers=headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        print("Data: ", data)
        products = data.get("data", {}).get("products", [])
        if not products:
            print("error: No products found")
            return jsonify({"error": "No products found"})

        random.shuffle(products)
        product = products[0]
        print("Product: ",product)
        return jsonify({
            "asin": product["asin"],
            "name": product["product_title"],
            "price": product.get("product_price", 0),
            "photo": product.get("product_photo", "none"),
            "link": product.get("product_url"),
        })


    return jsonify({"error": "Failed to fetch products after multiple retries"}), 500
    

@app.route('/agent-recommend', methods=['POST'])

def agent_recommend():
    conn = http.client.HTTPSConnection("real-time-amazon-data.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': rapid_key,
        'x-rapidapi-host': "real-time-amazon-data.p.rapidapi.com"
    }
    print("Received request to recommend")
    data = request.json
    print("Data: ", data)


    try:
        # Extract product details safely
        product_info = data.get("product", {})
        product_name = product_info.get("name", "Unknown")
        asin = product_info.get("asin", "")
        price = product_info.get("product_price", 0)

        agent_in_use = data.get("agentInUse", [])
        if not agent_in_use or len(agent_in_use) < 2:
            return jsonify({"error": "Invalid agent data"}), 400
        
        email = agent_in_use[0].lower()
        name_of_agent = agent_in_use[1]

        ep = f"/product-details?asin={asin}&country=US"
        print("using asin: ", asin)


        max_retries = 3
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1}: Fetching product details...")
            try:
                conn.request("GET", ep, headers=headers)
                res = conn.getresponse()
                if res.status == 200:
                    break  # Exit loop if successful
                else:
                    pass
            except http.client.RemoteDisconnected:
                pass
                time.sleep(2 ** attempt)  # Exponential backoff (2, 4, 8 sec)
        
        # Read and parse response
        data_res = res.read()
        decoded_response = data_res.decode("utf-8")
        parsed_data = json.loads(decoded_response)

        # Extract category and brand safely
        category_path = parsed_data.get("data", {}).get("category_path", [])
        category = category_path[0].get("name", "Unknown") if category_path else "Unknown"
        brand = parsed_data.get("data", {}).get("product_details", {}).get("brand", "Unknown")



    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return jsonify({"error": "Invalid JSON response from API"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "An error occurred while fetching product details"}), 500

    # Process category and generate input vector
    try:
        cldis_category, category, categoryid, category_binary = em.auto_sort(
            cache_categories, word=category, max_distance=10,
            bucket_array=bucket_categories, type_of_distance_calc="COSINE SIMILARITY",
            amount_of_binary_digits=10
        )

        cldis_target, target, targetid, target_binary = em.auto_sort(
            cache_targets, word=product_name, max_distance=10,
            bucket_array=bucket_targets, type_of_distance_calc="COSINE SIMILARITY",
            amount_of_binary_digits=4
        )

        llm_output = em.llm_call(f"what category should this product be in: {product_name}")
        print(f"LLM output: {llm_output}")

        cldis, genre, bucketid, genre_binary = em.auto_sort(
            cache, word=llm_output, max_distance=10, bucket_array=bucket,
            type_of_distance_calc="COSINE SIMILARITY", amount_of_binary_digits=10
        )

        input_to_agent = np.concatenate([genre_binary, target_binary, np.array(category_binary)])

        print(f"Input to agent: {input_to_agent}")

        # Get agent recommendation
        response = agentResponse(input_to_agent, email, name_of_agent)
        recommendation_score = (sum(response) / len(response)) * 100 if sum(response) != 0 else 0

        return jsonify({
            "genre": genre,
            "target": target,
            "recommendation_score": recommendation_score
        })
    
    


    except Exception as e:
        return jsonify({"error": "Error during recommendation processing"}), 500


@app.route('/trainAgent', methods=["POST"])
def trainAgent():
    data = request.json
    Label = data["Label"]
    print("training agent: ", Label)
    product_name = data.get("product_name", "")
    aiu = data["agentInUse"]
    email = aiu[0].lower()
    name_of_agent = aiu[1]
    price = data.get("price", 0)
    price = str(price)
    match = re.search(r"[-+]?\d*\.\d+|\d+", price)  
    if match:
        price = int(float(match.group()))  
        print(price)
    else:
        print("No match found")

    #embedding bucketing
    cldis, genre, bucketid, genre_binary = em.auto_sort(
        cache, word=product_name, max_distance=10, bucket_array=bucket,
        type_of_distance_calc="COSINE SIMILARITY", amount_of_binary_digits=10
    )
    cldis_target, target, targetid, target_binary = em.auto_sort(
        cache_targets, word=product_name, max_distance=10, bucket_array=bucket_targets,
        type_of_distance_calc="COSINE SIMILARITY", amount_of_binary_digits=4
    )

    cldis_category, category, categoryid, category_binary = em.auto_sort(
        cache_categories, word=product_name, max_distance=10, bucket_array=bucket_categories,
        type_of_distance_calc="COSINE SIMILARITY", amount_of_binary_digits=5
    )


    input_to_agent = np.concatenate([genre_binary, target_binary, category_binary])


    print("Training agent with label: ", Label)
    try:
        trainAgentCall(input_to_agent,Label,  email, name_of_agent)
        print("Trainned agent")
        return jsonify({"message": "Training data saved successfully"}), 200
    except Exception as e:
        print(f"Error saving training data: {e}")
        return jsonify({"error": "Error saving training data"}), 500

def verify_password(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_apikey}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json()  #return the user data
    else:
        return None  # auth failed... password incorrect

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    print(data)
    email = data.get("email").lower()
    password = data.get("password")
    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    # Verify email and password
    user_data = verify_password(email, password)

    if user_data:
        return jsonify({"message": f"Welcome {email}!", "uid": user_data["localId"]}), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 401
    
@app.route("/createAccount", methods=["POST"])
def createAccount():
    data = request.json

    email = data.get("email").lower()
    password = data.get("password")
    try:
        user = auth.get_user_by_email(email)
        return jsonify({"message": "User already exists, try logging into your account", "uid": user.uid}), 200
    except auth.UserNotFoundError:
        user = auth.create_user(email=email, password=password)
        return jsonify({"message": "User created, you can now log in to your account", "uid": user.uid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@app.route("/createNewAgent", methods=["POST"])
def createNewAgent():
    data=request.json
    email = data.get("email").lower()
    country = data.get("selectedCountry")
    print(data)
    print(country)
    age = data.get("age")
    gender = data.get("gender")
    agent_name = data.get("newAgentName")
    extra_info = data.get("extraInfo")
    ##Note if we are integrating ao labs api, put the uid in the agent info so that it is stored in the database and easily accessible
    Agent_info={
        "email":email,
        "name": agent_name,
        "country": country,
        "age": age,
        "gender": gender,
        "extraInfo": extra_info
    }
    print(agent_name)
    check_agent = db.collection('Agents').where('email', '==', email).where('name', '==', agent_name).stream()
    if any(check_agent):
        return jsonify({"message": "Agent with this name already exists."}), 400

    doc_ref = db.collection('Agents').add(Agent_info)
    return jsonify({"message": "Agent Created"}), 200

@app.route("/deleteAgent", methods=["POST"])
def deleteAgent():
    data = request.json["agentInUse"]
    email = data[0]
    name_of_agent = data[1]

    agent_ref = db.collection('Agents').where('email', '==', email).where('name', '==', name_of_agent).stream()
    
    found_agent = None
    for agent in agent_ref:
        found_agent = agent

    agentDelete(email, name_of_agent)
    
    if found_agent:
        # Delete the found agent document
        found_agent.reference.delete()
        return jsonify({"message": "Agent successfully deleted"}), 200
    else:
        return jsonify({"error": "Agent not found"}), 404
    
    



@app.route("/getAgents", methods=["POST"])
def getAgents():
    print("Received request to get agents")
    data = request.json
    email = data.get("email").lower()
    
    # Get the 'Agents' collection from Firestore
    agents_ref = db.collection('Agents')
    user_agents = agents_ref.where('email', '==', email).stream()
    
    agents_list = []
    

    for agent in user_agents:
        agent_data = agent.to_dict() 
        agents_list.append(agent_data)


        inputs_ref = agent.reference.collection('inputs').stream()
        outputs_ref = agent.reference.collection('outputs').stream()
        
        inputs = []  
        outputs = []  
        

        for input_doc in inputs_ref:
            inputs.append(input_doc.to_dict())  # Append input data
        
        for output_doc in outputs_ref:
            outputs.append(output_doc.to_dict())  # Append output data

        agent_data['inputs'] = inputs
        agent_data['outputs'] = outputs
        


        print("Agent Data: ", agent_data)
    
    if not agents_list:
        return jsonify({"message": "No agents found for this user"}), 200

    return jsonify(agents_list)

@app.route("/saveProduct", methods=["POST"])
def saveProduct():
    try:
        data = request.json
        aiu = data.get("agentInUse", [])
        product = data.get("product", {})

        if len(aiu) < 2:
            return jsonify({"error": "Invalid agent data"}), 400

        email = aiu[0].lower()
        name_of_agent = aiu[1]

        print("Product: ", product)

        # Query the agent document
        agent_query = db.collection('Agents').where('email', '==', email).where('name', '==', name_of_agent).stream()
        agent_doc = next(agent_query, None)  # Get the first matching document

        if not agent_doc:
            return jsonify({"error": "Agent not found"}), 404

        agent_ref = db.collection('Agents').document(agent_doc.id)  # Correct document reference

        # Update the product field
        agent_ref.collection('products').add(product)

        return jsonify({"message": "Product updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/getProducts", methods=["POST"])
def getProducts():
    try:
        data = request.json
        aiu = data.get("agentInUse", [])

        if not isinstance(aiu, list) or len(aiu) < 2:
            return jsonify({"error": "Invalid agent data"}), 400

        email = aiu[0].lower()
        name_of_agent = aiu[1]

        # Query the agent document
        agent_query = db.collection('Agents').where('email', '==', email).where('name', '==', name_of_agent).stream()
        agent_doc = next(agent_query, None)  # Get the first matching document

        if not agent_doc:
            return jsonify({"error": "Agent not found"}), 404

        agent_ref = db.collection('Agents').document(agent_doc.id)  # Correct document reference

        # Fetch products
        products_query = agent_ref.collection('products').stream()
        products = [product.to_dict() for product in products_query]  # Convert documents to dict

        return jsonify({"products": products}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/')
def home():
    return "Testing"

if __name__ == '__main__':

    app.run(debug=True)