from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
import re

app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv("DATABASE_URI")
client = MongoClient(MONGO_URI)

db = client["mydb"]
media = db["Media"]


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "name": "Pixell Pulse API"
    })


@app.route("/movies")
def movies():

    result = []

    for movie in media.find({}, {
        "file_name": 1,
        "file_size": 1,
        "caption": 1
    }).limit(50):

        name = movie.get("file_name", "")

        result.append({
            "title": name,
            "size": movie.get("file_size"),
            "caption": movie.get("caption")
        })

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
