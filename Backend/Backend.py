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
import ao_core as ao

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
print(firebase_sdk)
cred = credentials.Certificate(firebase_sdk)
firebase_admin.initialize_app(cred)

db = firestore.client()

with open("google-countries.json") as f:
    country_data = json.load(f)

client = OpenAI(api_key=openai_key)

possible_genres = ["Clothes", "Electronics", "Books For Children", "Toys", "Jewelry", "Home", "Beauty", "Sports", "Food", "Music", "Movies", "Games", "Art", "Travel", "Pets", "Health", "Fitness", "Tech", "DIY", "Gardening", "Cooking", "Crafts", "Cars", "Outdoors", "Office", "School", "Baby", "Party", "Wedding", "Holidays", "Grooming", "Books For Teenagers", "Drama Book", "Science Fiction Books", "Romance Books", "Gift Card", "Dolls"]

em.config(openai_key)
cache, bucket = em.init("embedding_cache", possible_genres)
agent = None

@app.route('/get-gift-categories', methods=['POST'])
def get_gift_categories():
    data = request.json
    age = data.get("age", 18)
    gender = data.get("gender", [])
    budget = data.get("budget", 50)
    prompt = f"What are some gift categories that meet the following: age: {age}, gender: {gender}, budget: {budget}"
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
    return jsonify({"categories": gift_categories})

@app.route('/get-product', methods=['POST'])
def get_random_product():
    data = request.json
    query = data.get("query", "")
    budget = data.get("budget", 50)
    encoded_query = quote(query)

    conn = http.client.HTTPSConnection("real-time-amazon-data.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': Rapid_key,
        'x-rapidapi-host': "real-time-amazon-data.p.rapidapi.com"
    }
    conn.request("GET", f"/search?query={encoded_query}&page=1&country=US&sort_by=RELEVANCE&min_price=5&max_price={budget}&product_condition=ALL&is_prime=false&deals_and_discounts=NONE", headers=headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    products = data.get("data", {}).get("products", [])
    if not products:
        return jsonify({"error": "No products found"})

    random.shuffle(products)
    product = products[0]
    print("Product: ",product)
    print(product)
    return jsonify({
        "name": product["product_title"],
        "price": product.get("product_original_price", 0),
        "photo": product.get("product_photo", "none")
    })

@app.route('/agent-recommend', methods=['POST'])
def agent_recommend():
    data = request.json
    product_name = data.get("product", "")["name"]
    price = data.get("product", "").get("product_price", 0)
    print("product: ", product_name)
    agent_in_use = data.get("agentInUse")
    email = agent_in_use[0]
    name_of_agent = agent_in_use[1]
    print("Agent info:", email, name_of_agent)
    
    price = data.get("price", 0)
    price = str(price)
    
    if price:
        match = re.search(r"[-+]?\d*\.\d+|\d+", price)
        if match:
            price = float(match.group())
        else:
            price = int(price)
    else:
        print("No price provided.")
    
  
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
    

    agent = ao.Agent(arch)  
    

    try:
        inputs_ref = db.collection('Agents').document(agent_document_id).collection('inputs').stream()
        outputs_ref = db.collection('Agents').document(agent_document_id).collection('outputs').stream()
    except Exception as e:
        print(f"Error fetching inputs or outputs: {e}")
        return jsonify({"error": "Error fetching data from Firestore"}), 500

    inputs = [input_doc.to_dict() for input_doc in list(inputs_ref)]
    outputs = [output_doc.to_dict() for output_doc in list(outputs_ref)]
    

    print(f"Retrieved {len(inputs)} inputs and {len(outputs)} outputs.")
    

    

    def convert_to_binary_array(binary_string):
        return [int(bit) for bit in binary_string]
    
    binary_inputs = []
    binary_outputs = []
    
    for input_data in inputs:
        for key, value in input_data.items():

            binary_inputs.append(convert_to_binary_array(value))
    
    for output_data in outputs:
        for key, value in output_data.items():

            binary_outputs.append(convert_to_binary_array(value))
    

    for i in range(len(binary_outputs)):
        try:
            print(f"Training with input: {binary_inputs[i]}, output: {binary_outputs[i]}")
            agent.next_state(INPUT=binary_inputs[i], LABEL=binary_outputs[i])
        except Exception as e:
            print(f"Error during next_state call: {e}")
            return jsonify({"error": "Error during agent training"}), 500


    try:
        cldis, genre, bucketid, genre_binary = em.auto_sort(
            cache, word=product_name, max_distance=10, bucket_array=bucket,
            type_of_distance_calc="COSINE SIMILARITY", amount_of_binary_digits=10
        )
    except Exception as e:
        print(f"Error during auto_sort: {e}")
        return jsonify({"error": "Error during auto_sort processing"}), 500
    

    if price < 25:
        price_binary = [0, 0]
    elif price < 50:
        price_binary = [0, 1]
    elif price < 100:
        price_binary = [1, 0]
    else:
        price_binary = [1, 1]

    input_to_agent = np.concatenate([price_binary, genre_binary])


    try:
        response = agent.next_state(input_to_agent)
        if sum(response) ==0:
            recommendation_score = 0
        else:
            recommendation_score = (sum(response) / len(response)) * 100
    except Exception as e:
        print(f"Error during agent recommendation: {e}")
        return jsonify({"error": "Error during recommendation calculation"}), 500
    
    return jsonify({
        "genre": genre,
        "recommendation_score": recommendation_score
    })



@app.route('/trainAgent', methods=["POST"])
def trainAgent():
    data = request.json
    print("data: ", data)
    Label = data["Label"]
    product_name = data.get("product_name", "")
    aiu = data["agentInUse"]
    email = aiu[0]
    name_of_agent = aiu[1]
    price = data.get("price", 0)
    price = str(price)
    match = re.search(r"[-+]?\d*\.\d+|\d+", price)  # Search for the number pattern
    if match:
        price = int(float(match.group()))  # Convert the matched string to a float, then to an integer
        print(price)
    else:
        print("No match found")

    
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

    input_to_agent = np.concatenate([price_binary, genre_binary])
    agent_ref = db.collection('Agents').where('email', '==', email).where('name', '==', name_of_agent).stream()
    
    agent_data = None
    agent_document_id = None
    for agent in agent_ref:
        agent_data = agent.to_dict()  
        agent_document_id = agent.id  
    inputdata = {
        "inputs":input_to_agent.tolist()
    }
    outputdata= {
        "outputs":Label
    }
    if Label:
            try:
                inputs_ref = db.collection('Agents').document(agent_document_id).collection('inputs').add(inputdata)
                outputs_ref = db.collection('Agents').document(agent_document_id).collection('outputs').add(outputdata)
            except Exception as e:
                print(f"Error fetching inputs or outputs: {e}")
                return jsonify({"error": "Error fetching data from Firestore"}), 500
    else:
        print("not label")

    return jsonify({
    "response": "200",

    })

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    print(data)
    email = data.get("email")
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

    email = data.get("email")
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
    email = data.get("email")
    agent_name = data.get("newAgentName")
    Agent_info={
        "email":email,
        "name": agent_name,
    }
    doc_ref = db.collection('Agents').add(Agent_info)
    agent = ao.Agent(arch, "agent")
    return jsonify({"message": "Trip saved successfully"}), 200

@app.route("/getAgents", methods=["POST"])
def getAgents():
    print("Received request to get agents")
    data = request.json
    email = data.get("email")
    
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



if __name__ == '__main__':
    app.run(debug=True)
