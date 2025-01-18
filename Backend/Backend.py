from flask import Flask, request, jsonify
import random
from openai import OpenAI
import json
import re
import numpy as np
import http.client
from urllib.parse import quote

from config import openai_key, Rapid_key, firebase_sdk
import embedding_bucketing.embedding_model_test as em
import ao_core as ao

from Arch__giftrecommender import arch
from flask_cors import CORS

from firebase_admin import credentials, auth
import firebase_admin
from firebase_admin import firestore
import os
app = Flask(__name__)
CORS(app)


cred = credentials.Certificate(firebase_sdk)
firebase_admin.initialize_app(cred)

db = firestore.client()

with open("google-countries.json") as f:
    country_data = json.load(f)

client = OpenAI(api_key=openai_key)

possible_genres = ["Clothes", "Electronics", "Books For Children", "Toys", "Jewelry", "Home", "Beauty", "Sports", "Food", "Music", "Movies", "Games", "Art", "Travel", "Pets", "Health", "Fitness", "Tech", "DIY", "Gardening", "Cooking", "Crafts", "Cars", "Outdoors", "Office", "School", "Baby", "Party", "Wedding", "Holidays", "Grooming", "Books For Teenagers", "Drama Book", "Science Fiction Books", "Romance Books", "Gift Card", "Dolls"]

em.config(openai_key)
cache, bucket = em.init("embedding_cache", possible_genres)
agent = ao.Agent(arch, "agent")

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
    product_name = data.get("product_name", "")
    price = data.get("price", 0)
    price = str(price)
    if price:
        match = re.search(r"[-+]?\d*\.\d+|\d+", price)  # Search for the number pattern
        if match:
            price = (float(match.group()))  # Convert the matched string to a float, then to an integer
            print(price)
        else:
            price = int(price)
            print("No match found")
    else:
        print("no price")

    
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
    response = agent.next_state(input_to_agent)
    recommendation_score = (sum(response) / len(response)) * 100
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
    if Label:
        agent.next_state(input_to_agent, LABEL=Label)
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
    print(data)
    email = data.get("email")
    password = data.get("password")
    try:
        user = auth.get_user_by_email(email)
        return jsonify({"message": "User already exists, try logging into your account", "uid": user.uid}), 200
    except auth.UserNotFoundError:
        user = auth.create_user(email=email, password=password)
        return jsonify({"message": "User created, you can now log in to your account", "uid": user.uid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 200


if __name__ == '__main__':
    app.run(debug=True)
