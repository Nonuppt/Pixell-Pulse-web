from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os

app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv("DATABASE_URI")

client = MongoClient(MONGO_URI)

db = client["appname"]
media = db["Pixell_Pulse_files"]


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "name": "Pixell Pulse API",
        "version": "1.0"
    })


@app.route("/movies")
def movies():
    result = []

    for movie in media.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "file_name": 1,
            "file_size": 1,
            "file_type": 1,
            "mime_type": 1,
            "caption": 1,
            "cover": 1
        }
    ).limit(50):

        result.append({
            "id": movie.get("id"),
            "file_name": movie.get("file_name"),
            "file_size": movie.get("file_size"),
            "file_type": movie.get("file_type"),
            "mime_type": movie.get("mime_type"),
            "caption": movie.get("caption"),
            "cover": movie.get("cover")
        })

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
