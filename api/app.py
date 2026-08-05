from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "name": "Pixell Pulse API",
        "version": "1.0"
    })

@app.route("/movies")
def movies():
    return jsonify([
        {
            "title": "Loki",
            "year": 2021,
            "type": "Series",
            "qualities": ["480p", "720p", "1080p"],
            "telegram": "https://t.me/Gomzybot?start=getfile-Loki"
        }
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
