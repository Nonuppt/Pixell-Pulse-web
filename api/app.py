from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
import re
import requests
from functools import lru_cache

app = Flask(__name__)
CORS(app)

# =========================================================
# CONFIG
# =========================================================

MONGO_URI = os.getenv("DATABASE_URI")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not MONGO_URI:
    raise RuntimeError("DATABASE_URI environment variable is missing")

client = MongoClient(MONGO_URI)

# IMPORTANT:
# Keep these exactly as your current working API.
db = client["appname"]
media = db["Pixell_Pulse_files"]

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE = "https://image.tmdb.org/t/p/w500"

BOT_USERNAME = "Gomzybot"


# =========================================================
# QUALITY ORDER
# =========================================================

QUALITY_ORDER = {
    "360p": 1,
    "480p": 2,
    "720p": 3,
    "1080p": 4,
    "2160p": 5
}


# =========================================================
# CLEAN TITLE
# =========================================================

def parse_file_name(file_name):

    name = str(file_name or "").strip()

    # Extension
    name = re.sub(
        r"\.(mkv|mp4|avi|mov|wmv|flv|ts|webm)$",
        "",
        name,
        flags=re.I
    )

    # =====================================================
    # REMOVE PIXELL PULSE / TELEGRAM WATERMARK
    # =====================================================

    name = re.sub(
        r"@?\s*Pixell[\s_]*Pulse.*$",
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
        r"ᴏɪɴ.*$",
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

    # =====================================================
    # QUALITY
    # =====================================================

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

    # =====================================================
    # YEAR
    # =====================================================

    year_match = re.search(
        r"\b(19\d{2}|20\d{2})\b",
        name
    )

    year = (
        int(year_match.group(1))
        if year_match
        else None
    )

    # =====================================================
    # SEASON / EPISODE
    # =====================================================

    season = None
    episode = None

    match = re.search(
        r"\bS(\d{1,2})\s*E(\d{1,3})\b",
        name,
        flags=re.I
    )

    if match:

        season = int(match.group(1))
        episode = int(match.group(2))

    else:

        match = re.search(
            r"\bSeason\s*(\d{1,2})\b",
            name,
            flags=re.I
        )

        if match:
            season = int(match.group(1))

        match = re.search(
            r"\bS(\d{1,2})\b",
            name,
            flags=re.I
        )

        if match and season is None:
            season = int(match.group(1))

        match = re.search(
            r"\bEpisode\s*(\d{1,3})\b",
            name,
            flags=re.I
        )

        if match:
            episode = int(match.group(1))

        match = re.search(
            r"\bE(\d{1,3})\b",
            name,
            flags=re.I
        )

        if match and episode is None:
            episode = int(match.group(1))

    # =====================================================
    # TITLE
    # =====================================================

    title = name

    patterns = [

        # Season / episode
        r"\bS\d{1,2}E\d{1,3}\b",
        r"\bSeason\s*\d{1,2}\b",
        r"\bEpisode\s*\d{1,3}\b",
        r"\bS\d{1,2}\b",
        r"\bE\d{1,3}\b",

        # Quality
        r"\b2160p\b",
        r"\b1080p\b",
        r"\b720p\b",
        r"\b480p\b",
        r"\b360p\b",

        # Sources
        r"\bWEB[- .]?DL\b",
        r"\bWEB[- .]?Rip\b",
        r"\bWEBRip\b",
        r"\bWEB\b",
        r"\bBluRay\b",
        r"\bBRRip\b",
        r"\bBDRip\b",
        r"\bHDRip\b",
        r"\bHDTV\b",
        r"\bDVDRip\b",
        r"\bHDTC\b",
        r"\bHDTS\b",
        r"\bHDCAM\b",
        r"\bCAMRip\b",
        r"\bCAM\b",
        r"\bLiNE\b",
        r"\bLINE\b",

        # Release tags
        r"\bV\d+\b",
        r"\bCleaned\b",
        r"\bComplete\b",
        r"\bProper\b",
        r"\bRepack\b",
        r"\bUncut\b",
        r"\bORG\b",
        r"\bOriginal\b",

        # Codecs
        r"\bHEVC\b",
        r"\bx264\b",
        r"\bx265\b",
        r"\bHx264\b",
        r"\bHx265\b",
        r"\bH264\b",
        r"\bH265\b",
        r"\bH\.264\b",
        r"\bH\.265\b",
        r"\bAV1\b",
        r"\b10bit\b",
        r"\b8bit\b",

        # Subtitle
        r"\bESubx264\b",
        r"\bESubx265\b",
        r"\bESubs?\b",
        r"\bSubs?\b",
        r"\bSubtitles?\b",

        # Audio
        r"\b5\.1\b",
        r"\b7\.1\b",
        r"\b2\.0\b",
        r"\bAAC\b",
        r"\bAC3\b",
        r"\bDDP\b",
        r"\bDD\+?\b",
        r"\bEAC3\b",
        r"\bDolby\b",
        r"\bAtmos\b",

        # Languages
        r"\bHindi\b",
        r"\bHind\b",
        r"\bEnglish\b",
        r"\bTamil\b",
        r"\bTelugu\b",
        r"\bMalayalam\b",
        r"\bKannada\b",
        r"\bPunjabi\b",
        r"\bBengali\b",
        r"\bMarathi\b",
        r"\bGujarati\b",
        r"\bUrdu\b",
        r"\bChinese\b",
        r"\bKorean\b",
        r"\bJapanese\b",

        # Extra tags
        r"\bNF\b",
        r"\bHC\b",
        r"\bHQ\b",
        r"\bHD\b",
        r"\bHx\b",
        r"\bmkv\b",
        r"\bmp4\b",
        r"\bavi\b",
        r"\bREMUX\b"
    ]

    for pattern in patterns:

        title = re.sub(
            pattern,
            " ",
            title,
            flags=re.I
        )

    # Remove year
    if year:

        title = re.sub(
            rf"\b{year}\b",
            " ",
            title
        )

    # Remove common leftover numeric audio
    title = re.sub(
        r"\b\d+\s+\d+\b",
        " ",
        title
    )

    # Separators
    title = re.sub(
        r"[\[\]\(\)\{\}_\-]+",
        " ",
        title
    )

    # Multiple spaces
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


# =========================================================
# TMDB POSTER
# =========================================================

@lru_cache(maxsize=1000)
def get_poster(title, year=None):

    if not TMDB_API_KEY or not title:
        return None

    try:

        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "language": "en-US",
            "include_adult": "false"
        }

        if year:
            params["year"] = year

        response = requests.get(
            f"{TMDB_BASE}/search/movie",
            params=params,
            timeout=8
        )

        if response.status_code != 200:
            return None

        data = response.json()

        results = data.get(
            "results",
            []
        )

        if not results:
            return None

        poster_path = results[0].get(
            "poster_path"
        )

        if not poster_path:
            return None

        return TMDB_IMAGE + poster_path

    except Exception:
        return None


# =========================================================
# TELEGRAM LINK
# =========================================================

def telegram_link(title, quality):

    # Same format used by the existing bot links.
    payload = f"getfile-{title}-{quality}"

    return (
        f"https://t.me/{BOT_USERNAME}"
        f"?start={payload.replace(' ', '-')}"
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "status": "online",
        "name": "Pixell Pulse API",
        "version": "4.0"
    })


# =========================================================
# MOVIES
# =========================================================

@app.route("/movies")
def movies():

    grouped = {}

    cursor = media.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "file_ref": 1,
            "file_name": 1,
            "file_size": 1,
            "file_type": 1,
            "mime_type": 1,
            "caption": 1
        }
    ).limit(5000)

    for document in cursor:

        file_name = document.get(
            "file_name",
            ""
        )

        parsed = parse_file_name(
            file_name
        )

        title = parsed["title"]

        if not title:
            continue

        # =================================================
        # IMPORTANT:
        # Normalize title so different qualities become
        # ONE movie card.
        # =================================================

        normalized_title = re.sub(
            r"\s+",
            " ",
            title.lower()
        ).strip()

        key = (
            normalized_title,
            parsed["year"]
        )

        # =================================================
        # CREATE MOVIE
        # =================================================

        if key not in grouped:

            grouped[key] = {

                "title": title,

                "year": parsed["year"],

                "type": (
                    "Series"
                    if (
                        parsed["season"] is not None
                        or parsed["episode"] is not None
                    )
                    else "Movie"
                ),

                "poster": get_poster(
                    title,
                    parsed["year"]
                ),

                "qualities": [],

                "files": [],

                "seasons": {}

            }

        item = grouped[key]

        # =================================================
        # FILE INFORMATION
        # =================================================

        file_info = {

            "id": document.get("id"),

            "file_ref": document.get(
                "file_ref"
            ),

            "file_name": file_name,

            "quality": parsed["quality"],

            "telegram": (
                telegram_link(
                    title,
                    parsed["quality"]
                )
                if parsed["quality"]
                else None
            )
        }

        item["files"].append(
            file_info
        )

        # =================================================
        # SERIES
        # =================================================

        if parsed["season"] is not None:

            season_number = parsed[
                "season"
            ]

            if season_number not in item[
                "seasons"
            ]:

                item["seasons"][
                    season_number
                ] = {

                    "season": season_number,

                    "qualities": [],

                    "episodes": {}

                }

            season_data = item[
                "seasons"
            ][season_number]

            quality = parsed[
                "quality"
            ]

            if (
                quality
                and quality not in
                season_data["qualities"]
            ):

                season_data[
                    "qualities"
                ].append(quality)

            # Episode
            if parsed["episode"] is not None:

                episode_number = parsed[
                    "episode"
                ]

                if episode_number not in (
                    season_data["episodes"]
                ):

                    season_data[
                        "episodes"
                    ][episode_number] = {

                        "episode": episode_number,

                        "qualities": []

                    }

                if (
                    quality
                    and quality not in
                    season_data[
                        "episodes"
                    ][episode_number][
                        "qualities"
                    ]
                ):

                    season_data[
                        "episodes"
                    ][episode_number][
                        "qualities"
                    ].append(quality)

        # =================================================
        # MOVIE
        # =================================================

        else:

            quality = parsed[
                "quality"
            ]

            if (
                quality
                and quality not in
                item["qualities"]
            ):

                item["qualities"].append(
                    quality
                )


    # =====================================================
    # FINALIZE
    # =====================================================

    result = []

    for item in grouped.values():

        # Sort movie qualities
        item["qualities"].sort(
            key=lambda q:
            QUALITY_ORDER.get(q, 99)
        )

        # =================================================
        # Convert seasons dictionary -> list
        # =================================================

        seasons = []

        for season_number, season_data in (
            item["seasons"].items()
        ):

            season_data[
                "qualities"
            ].sort(
                key=lambda q:
                QUALITY_ORDER.get(q, 99)
            )

            episodes = []

            for episode_number, episode_data in (
                season_data[
                    "episodes"
                ].items()
            ):

                episode_data[
                    "qualities"
                ].sort(
                    key=lambda q:
                    QUALITY_ORDER.get(q, 99)
                )

                episodes.append(
                    episode_data
                )

            episodes.sort(
                key=lambda x:
                x["episode"]
            )

            season_data[
                "episodes"
            ] = episodes

            seasons.append(
                season_data
            )

        seasons.sort(
            key=lambda x:
            x["season"]
        )

        item["seasons"] = seasons

        # =================================================
        # FILES NOT NEEDED BY FRONTEND
        # Keep only useful quality links.
        # =================================================

        item["files"] = [
            f for f in item["files"]
            if f.get("quality")
        ]

        result.append(item)


    # =====================================================
    # SORT MOVIES
    # =====================================================

    result.sort(
        key=lambda x: (
            -(x["year"] or 0),
            x["title"].lower()
        )
    )

    return jsonify(result)


# =========================================================
# SEARCH
# =========================================================

@app.route("/search")
def search():

    query = request.args.get(
        "q",
        ""
    ).strip().lower()

    if not query:
        return jsonify([])

    all_movies = movies().get_json()

    results = [
        movie
        for movie in all_movies
        if query in movie["title"].lower()
    ]

    return jsonify(results)


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            8000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
