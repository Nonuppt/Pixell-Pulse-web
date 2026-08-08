from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import os
import re

app = Flask(__name__)
CORS(app)

# =========================
# MONGODB
# =========================

MONGO_URI = os.getenv("DATABASE_URI")

client = MongoClient(MONGO_URI)

db = client["appname"]
media = db["Pixell_Pulse_files"]


# =========================
# QUALITY ORDER
# =========================

QUALITY_ORDER = {
    "360p": 1,
    "480p": 2,
    "720p": 3,
    "1080p": 4,
    "2160p": 5
}


# =========================
# FILE NAME PARSER
# =========================

def parse_file_name(file_name):

    name = file_name or ""

    # Remove file extension
    name = re.sub(
        r"\.(mkv|mp4|avi|mov|wmv|flv)$",
        "",
        name,
        flags=re.I
    )

    # ---------------------------------
    # Remove Telegram / channel watermark
    # ---------------------------------

    name = re.sub(
        r"@?Pixell[\s_]*Pulse.*$",
        "",
        name,
        flags=re.I
    )

    name = re.sub(
        r"ᵊᴏɪɴ.*$",
        "",
        name,
        flags=re.I
    )

    name = re.sub(
        r"➤.*$",
        "",
        name,
        flags=re.I
    )

    # ---------------------------------
    # Quality
    # ---------------------------------

    quality_match = re.search(
        r"\b(2160p|1080p|720p|480p|360p)\b",
        name,
        flags=re.I
    )

    quality = (
        quality_match.group(1).lower()
        if quality_match
        else None
    )

    # ---------------------------------
    # Year
    # ---------------------------------

    year_match = re.search(
        r"\b(19\d{2}|20\d{2})\b",
        name
    )

    year = (
        int(year_match.group(1))
        if year_match
        else None
    )

    # ---------------------------------
    # Season / Episode
    # ---------------------------------

    season = None
    episode = None

    # S01E01
    se_match = re.search(
        r"\bS(\d{1,2})E(\d{1,3})\b",
        name,
        flags=re.I
    )

    if se_match:

        season = int(se_match.group(1))
        episode = int(se_match.group(2))

    else:

        # S01
        season_match = re.search(
            r"\bS(\d{1,2})\b",
            name,
            flags=re.I
        )

        if season_match:
            season = int(
                season_match.group(1)
            )

        # E01
        episode_match = re.search(
            r"\bE(\d{1,3})\b",
            name,
            flags=re.I
        )

        if episode_match:
            episode = int(
                episode_match.group(1)
            )

    # ---------------------------------
    # TITLE
    # ---------------------------------

    title = name

    # Season / Episode
    title = re.sub(
        r"\bS\d{1,2}E\d{1,3}\b",
        " ",
        title,
        flags=re.I
    )

    title = re.sub(
        r"\bS\d{1,2}\b",
        " ",
        title,
        flags=re.I
    )

    title = re.sub(
        r"\bE\d{1,3}\b",
        " ",
        title,
        flags=re.I
    )

    # Quality
    title = re.sub(
        r"\b2160p\b|\b1080p\b|\b720p\b|\b480p\b|\b360p\b",
        " ",
        title,
        flags=re.I
    )

    # Sources
    source_patterns = [
        r"\bWEB[- .]?DL\b",
        r"\bWEB[- .]?Rip\b",
        r"\bWEB\b",
        r"\bBluRay\b",
        r"\bBRRip\b",
        r"\bBDRip\b",
        r"\bHDRip\b",
        r"\bHDTV\b",
        r"\bDVDRip\b",
        r"\bCAMRip\b",
        r"\bCAM\b",
        r"\bPreDVD\b",
        r"\bDVD\b"
    ]

    for pattern in source_patterns:
        title = re.sub(
            pattern,
            " ",
            title,
            flags=re.I
        )

    # Video codecs
    codec_patterns = [
        r"\bHEVC\b",
        r"\bx264\b",
        r"\bx265\b",
        r"\bH\.?264\b",
        r"\bH\.?265\b",
        r"\bAV1\b",
        r"\b10bit\b",
        r"\b8bit\b",
        r"\bHi10P\b"
    ]

    for pattern in codec_patterns:
        title = re.sub(
            pattern,
            " ",
            title,
            flags=re.I
        )

    # Audio information
    audio_patterns = [
        r"\b5\.1\b",
        r"\b5 1\b",
        r"\b7\.1\b",
        r"\b7 1\b",
        r"\b2\.0\b",
        r"\b2 0\b",
        r"\bAAC\b",
        r"\bAC3\b",
        r"\bDDP\b",
        r"\bDD\+\b",
        r"\bDolby\b",
        r"\bAtmos\b",
        r"\bEAC3\b"
    ]

    for pattern in audio_patterns:
        title = re.sub(
            pattern,
            " ",
            title,
            flags=re.I
        )

    # Languages
    language_patterns = [
        r"\bHindi\b",
        r"\bEnglish\b",
        r"\bTamil\b",
        r"\bTelugu\b",
        r"\bMalayalam\b",
        r"\bKannada\b",
        r"\bPunjabi\b",
        r"\bBengali\b",
        r"\bMarathi\b",
        r"\bGujarati\b",
        r"\bUrdu\b"
    ]

    for pattern in language_patterns:
        title = re.sub(
            pattern,
            " ",
            title,
            flags=re.I
        )

    # Subtitles
    subtitle_patterns = [
        r"\bESub\b",
        r"\bESubs\b",
        r"\bSUB\b",
        r"\bSUBS\b",
        r"\bSubtitle\b",
        r"\bSubtitles\b"
    ]

    for pattern in subtitle_patterns:
        title = re.sub(
            pattern,
            " ",
            title,
            flags=re.I
        )

    # Common unwanted text
    unwanted_patterns = [
        r"\bHx\b",
        r"\bH\.?264\b",
        r"\bH\.?265\b",
        r"\bmkv\b",
        r"\bmp4\b",
        r"\bavi\b",
        r"\bmov\b",
        r"\bREMUX\b",
        r"\bPROPER\b",
        r"\bREPACK\b",
        r"\bUNCUT\b"
    ]

    for pattern in unwanted_patterns:
        title = re.sub(
            pattern,
            " ",
            title,
            flags=re.I
        )

    # Remove year from title
    if year:

        title = re.sub(
            rf"\b{year}\b",
            " ",
            title
        )

    # Remove common numeric leftovers
    title = re.sub(
        r"\b\d+\s+\d+\b",
        " ",
        title
    )

    # Remove resolution-like numbers
    title = re.sub(
        r"\b\d{3,4}k\b",
        " ",
        title,
        flags=re.I
    )

    # Remove separators
    title = re.sub(
        r"[\[\]\(\)\{\}_\-]+",
        " ",
        title
    )

    # Remove repeated spaces
    title = re.sub(
        r"\s+",
        " ",
        title
    ).strip()

    return {
        "title": title,
        "year": year,
        "quality": quality,
        "season": season,
        "episode": episode
    }


# =========================
# HOME
# =========================

@app.route("/")
def home():

    return jsonify({
        "status": "online",
        "name": "Pixell Pulse API",
        "version": "2.2"
    })


# =========================
# MOVIES
# =========================

@app.route("/movies")
def movies():

    grouped = {}

    cursor = media.find(
        {},
        {
            "_id": 0,
            "file_name": 1
        }
    ).limit(2000)

    for movie in cursor:

        file_name = movie.get(
            "file_name",
            ""
        )

        parsed = parse_file_name(
            file_name
        )

        title = parsed["title"]

        if not title:
            continue

        # Unique title + year
        key = (
            title.lower(),
            parsed["year"]
        )

        if key not in grouped:

            grouped[key] = {
                "title": title,
                "year": parsed["year"],
                "type": (
                    "Series"
                    if parsed["season"] is not None
                    else "Movie"
                ),
                "qualities": [],
                "seasons": {}
            }

        item = grouped[key]

        # -------------------------
        # Movie
        # -------------------------

        if parsed["season"] is None:

            quality = parsed["quality"]

            if quality:

                if quality not in item["qualities"]:

                    item["qualities"].append(
                        quality
                    )

        # -------------------------
        # Series
        # -------------------------

        else:

            season_number = parsed["season"]

            if season_number not in item["seasons"]:

                item["seasons"][
                    season_number
                ] = {
                    "season": season_number,
                    "qualities": []
                }

            quality = parsed["quality"]

            if quality:

                if quality not in item["seasons"][
                    season_number
                ]["qualities"]:

                    item["seasons"][
                        season_number
                    ]["qualities"].append(
                        quality
                    )

    # ---------------------------------
    # Sort
    # ---------------------------------

    result = []

    for item in grouped.values():

        item["qualities"].sort(
            key=lambda x:
            QUALITY_ORDER.get(x, 99)
        )

        seasons = []

        for season in item["seasons"].values():

            season["qualities"].sort(
                key=lambda x:
                QUALITY_ORDER.get(x, 99)
            )

            seasons.append(
                season
            )

        seasons.sort(
            key=lambda x:
            x["season"]
        )

        item["seasons"] = seasons

        result.append(item)

    # Newest first
    result.sort(
        key=lambda x:
        x["year"] or 0,
        reverse=True
    )

    return jsonify(result)


# =========================
# SEARCH
# =========================

@app.route("/search")
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return jsonify([])

    results = []

    cursor = media.find(
        {
            "file_name": {
                "$regex": query,
                "$options": "i"
            }
        },
        {
            "_id": 0,
            "file_name": 1
        }
    ).limit(500)

    seen = set()

    for movie in cursor:

        parsed = parse_file_name(
            movie.get(
                "file_name",
                ""
            )
        )

        title = parsed["title"]

        if not title:
            continue

        key = (
            title.lower(),
            parsed["year"]
        )

        if key in seen:
            continue

        seen.add(key)

        results.append({
            "title": title,
            "year": parsed["year"],
            "type": (
                "Series"
                if parsed["season"] is not None
                else "Movie"
            )
        })

    results.sort(
        key=lambda x:
        x["year"] or 0,
        reverse=True
    )

    return jsonify(results)


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8000
    )
