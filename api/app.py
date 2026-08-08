from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import os
import re

app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv("DATABASE_URI")

client = MongoClient(MONGO_URI)
db = client["appname"]
media = db["Pixell_Pulse_files"]


def parse_file_name(file_name):
    name = re.sub(r"\.(mkv|mp4|avi|mov)$", "", file_name, flags=re.I)

    # Quality
    quality_match = re.search(
        r"(2160p|1080p|720p|480p|360p)",
        name,
        re.I
    )

    quality = quality_match.group(1).lower() if quality_match else None

    # Year
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", name)
    year = int(year_match.group(1)) if year_match else None

    # Season / Episode
    season_match = re.search(r"\bS(\d{1,2})\b", name, re.I)
    episode_match = re.search(r"\bE(\d{1,3})\b", name, re.I)

    season = int(season_match.group(1)) if season_match else None
    episode = int(episode_match.group(1)) if episode_match else None

    # Remove technical information to create title
    title = name

    patterns = [
        r"\bS\d{1,2}E\d{1,3}\b",
        r"\bS\d{1,2}\b",
        r"\bE\d{1,3}\b",
        r"\b(2160p|1080p|720p|480p|360p)\b",
        r"\b(4K|WEB[- .]?DL|WEBRip|BluRay|BRRip|HDRip|HDTV|DVDRip)\b",
        r"\b(HEVC|x264|x265|H\.?264|H\.?265|10bit|ESub|ESubs)\b",
        r"\b(Hindi|English|Tamil|Telugu|Malayalam|Kannada|Punjabi|Bengali|Marathi)\b",
    ]

    for pattern in patterns:
        title = re.sub(pattern, " ", title, flags=re.I)

    if year:
        title = re.sub(rf"\b{year}\b", " ", title)

    title = re.sub(r"[\[\]\(\)\{\}_\-]+", " ", title)
    title = re.sub(r"\s+", " ", title).strip()

    return {
        "title": title,
        "year": year,
        "quality": quality,
        "season": season,
        "episode": episode
    }


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "name": "Pixell Pulse API",
        "version": "2.0"
    })


@app.route("/movies")
def movies():

    grouped = {}

    cursor = media.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "file_name": 1,
            "file_size": 1,
            "file_type": 1,
            "cover": 1
        }
    ).limit(1000)

    for movie in cursor:

        file_name = movie.get("file_name", "")

        parsed = parse_file_name(file_name)

        title = parsed["title"]

        if not title:
            continue

        key = f"{title.lower()}_{parsed['year']}"

        if key not in grouped:
            grouped[key] = {
                "title": title,
                "year": parsed["year"],
                "type": "Series" if parsed["season"] else "Movie",
                "qualities": [],
                "seasons": {}
            }

        item = grouped[key]

        # Movie
        if not parsed["season"]:

            if parsed["quality"]:
                if parsed["quality"] not in item["qualities"]:
                    item["qualities"].append(parsed["quality"])

        # Series
        else:

            season = parsed["season"]

            if season not in item["seasons"]:
                item["seasons"][season] = {
                    "season": season,
                    "qualities": []
                }

            if parsed["quality"]:
                if parsed["quality"] not in item["seasons"][season]["qualities"]:
                    item["seasons"][season]["qualities"].append(
                        parsed["quality"]
                    )

    # Quality sorting
    quality_order = {
        "360p": 1,
        "480p": 2,
        "720p": 3,
        "1080p": 4,
        "2160p": 5
    }

    for item in grouped.values():

        item["qualities"].sort(
            key=lambda x: quality_order.get(x, 99)
        )

        item["seasons"] = sorted(
            item["seasons"].values(),
            key=lambda x: x["season"]
        )

        for season in item["seasons"]:
            season["qualities"].sort(
                key=lambda x: quality_order.get(x, 99)
            )

    return jsonify(list(grouped.values()))


@app.route("/search")
def search():

    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    results = []

    cursor = media.find(
        {"file_name": {"$regex": query, "$options": "i"}},
        {
            "_id": 0,
            "file_name": 1
        }
    ).limit(100)

    seen = set()

    for movie in cursor:

        parsed = parse_file_name(movie.get("file_name", ""))

        title = parsed["title"]

        if title.lower() in seen:
            continue

        seen.add(title.lower())

        results.append({
            "title": title,
            "year": parsed["year"],
            "type": "Series" if parsed["season"] else "Movie"
        })

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
