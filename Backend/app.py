from flask import Flask, request, jsonify
import random
from openai import OpenAI
import json
import re
import numpy as np
import http.client
from urllib.parse import quote

from dotenv import load_dotenv
import embedding_bucketing.embedding_model_test as em
from ao_core import Agent

from Arch__giftrecommender import arch
from flask_cors import CORS

from firebase_admin import credentials, auth
import firebase_admin
from firebase_admin import firestore
import numpy as np
import os
app = Flask(__name__)
CORS(app)

load_dotenv()


openai_key = os.getenv("OPENAI_KEY")
rapid_key = os.getenv("RAPID_KEY")
firebase_sdk = json.loads(os.getenv("FIREBASE_SDK"))

cred = credentials.Certificate(firebase_sdk)
firebase_admin.initialize_app(cred)

db = firestore.client()

with open("google-countries.json") as f:
    country_data = json.load(f)

client = OpenAI(api_key=openai_key)
em.config(openai_key)

possible_genres = ["Clothes", "Electronics", "Books For Children", "Toys", "Jewelry", "Home", "Beauty", "Sports", "Food", "Music", "Movies", "Games", "Art", "Travel", "Pets", "Health", "Fitness", "Tech", "DIY", "Gardening", "Cooking", "Crafts", "Cars", "Outdoors", "Office", "School", "Baby", "Party", "Wedding", "Grooming", "Books For Teenagers", "Drama Book", "Science Fiction Books", "Romance Books", "Dolls", "Purse"]
targets = ["Unisex", "Adult Male", "Adult Female","Female Teenager","Male Tennager", "Children/ Kids"]


cache_targets, bucket_targets = em.init("embedding_targets_cache", targets)
cache, bucket = em.init("embedding_cache", possible_genres)

agent = None

conn = http.client.HTTPSConnection("real-time-amazon-data.p.rapidapi.com")
headers = {
    'x-rapidapi-key': rapid_key,
    'x-rapidapi-host': "real-time-amazon-data.p.rapidapi.com"
}

@app.route('/get-gift-categories', methods=['POST'])
def get_gift_categories():
    data = request.json["data_to_send"]
    print(data)
    budget = data["budget"]
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
    gender = db.collection('Agents').document(agent_document_id).get().to_dict().get('country')
    country = db.collection('Agents').document(agent_document_id).get().to_dict().get('gender')
    print(age, gender, country)
    prompt = f"What are some gift categories from amazon that meet the following: age: {age}, gender: {gender}, budget: {budget}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "give a 5 options answer each only a couple of words long"},
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
    encoded_query = (encoded_query+"%20for"+"%20"+ gender)
    
    print("Query: ", encoded_query)

    conn.request("GET", f"/search?query={encoded_query}&page=1&country=US&sort_by=RELEVANCE&min_price={min_price}&max_price={budget}&product_condition=ALL&is_prime=false&deals_and_discounts=NONE", headers=headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
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
        "photo": product.get("product_photo", "none")
    })

@app.route('/agent-recommend', methods=['POST'])
def agent_recommend():
    data = request.json
    print("data: ", data)
    product_name = data.get("product", "")["name"]
    asin = data.get("product", "")["asin"]
    price = data.get("product", "").get("product_price", 0)
    agent_in_use = data.get("agentInUse")
    email = agent_in_use[0].lower()
    name_of_agent = agent_in_use[1]
    print("Agent info:", email, name_of_agent)

    # Fetch agent data
    agent_ref = db.collection('Agents').where('email', '==', email).where('name', '==', name_of_agent).stream()
    agent_data = None
    agent_document_id = None
    for agent in agent_ref:
        agent_data = agent.to_dict()
        agent_document_id = agent.id

    if not agent_document_id:
        return jsonify({"error": "Agent not found"}), 400

    # Initialize AO agent
    agent = Agent(arch)

    # Fetch all training data and train the agent
    try:
        training_data_ref = db.collection('Agents').document(agent_document_id).collection('training_data').stream()
        for training_data_doc in training_data_ref:
            training_data = training_data_doc.to_dict()
            binary_input = np.array(training_data["input"])
            binary_output = np.array(training_data["output"])
            agent.reset_state()
            agent.next_state(INPUT=binary_input, LABEL=binary_output)
    except Exception as e:
        print(f"Error training agent: {e}")
        return jsonify({"error": "Error training agent"}), 500
    
    try:
        cldis_target, target, targetid, target_binary = em.auto_sort(cache_targets, word=product_name, max_distance=10, bucket_array=bucket_targets, type_of_distance_calc="COSINE SIMILARITY", amount_of_binary_digits=4)
    except Exception as e:
        print(f"Error during auto_sort: {e}")
        return jsonify({"error": "Error during auto_sort processing"}), 500

    # Process product category and generate input vector
    cldis, genre, bucketid, genre_binary = em.auto_sort(
        cache, word=product_name, max_distance=10, bucket_array=bucket,
        type_of_distance_calc="COSINE SIMILARITY", amount_of_binary_digits=10
    )
    if price < 25:
        price_binary = [0, 0]
    elif price < 50:
        price_binary = [0, 1]
    elif price < 100:
        price_binary = [1, 0]
    else:
        price_binary = [1, 1]

    input_to_agent = np.concatenate([price_binary, genre_binary, target_binary])

    # Get agent recommendation
    try:
        response = agent.next_state(input_to_agent)
        if sum(response) == 0:
            recommendation_score = 0
        else:
            recommendation_score = (sum(response) / len(response)) * 100
    except Exception as e:
        print(f"Error during recommendation: {e}")
        return jsonify({"error": "Error during recommendation"}), 500

    return jsonify({
        "genre": genre,
        "target": target,
        "recommendation_score": recommendation_score
    })



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

    # Price encoding
    if price < 25:
        price_binary = [0, 0]
    elif price < 50:
        price_binary = [0, 1]
    elif price < 100:
        price_binary = [1, 0]
    else:
        price_binary = [1, 1]

    input_to_agent = np.concatenate([price_binary, genre_binary, target_binary])

    # Fetch the agent's document
    agent_ref = db.collection('Agents').where('email', '==', email).where('name', '==', name_of_agent).stream()
    agent_data = None
    agent_document_id = None
    for agent in agent_ref:
        agent_data = agent.to_dict()
        agent_document_id = agent.id

    if not agent_document_id:
        return jsonify({"error": "Agent not found"}), 400

    # Store the input-output pair in the 'training_data' subcollection
    training_data = {
        "input": input_to_agent.tolist(),
        "output": Label
    }
    print("Training agent with label: ", Label)
    try:
        db.collection('Agents').document(agent_document_id).collection('training_data').add(training_data)
        return jsonify({"message": "Training data saved successfully"}), 200
    except Exception as e:
        print(f"Error saving training data: {e}")
        return jsonify({"error": "Error saving training data"}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    print(data)
    email = data.get("email").lower()
    password = data.get("password")
    try:

        user = auth.get_user_by_email(email)
        return jsonify({"message": f"Hello {user.email}", "uid": user.uid}), 200
    except auth.UserNotFoundError:
        print("error: User not found ")
        return jsonify({"error": "User not found, try registering your account first"}), 400
    except Exception as e:
        print("error: ",e)
        return jsonify({"error": str(e)}), 400
    
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
    print("hello")
    data=request.json
    email = data.get("email").lower()
    country = data.get("selectedCountry")
    print(data)
    print(country)
    age = data.get("age")
    gender = data.get("gender")
    agent_name = data.get("newAgentName")
    Agent_info={
        "email":email,
        "name": agent_name,
        "country": country,
        "age": age,
        "gender": gender,
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

@app.route('/')
def home():
    return "Testing"

if __name__ == '__main__':

    app.run(debug=True)
