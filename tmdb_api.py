"""
tmdb_api.py - TMDB API Client für MovieProjekt
"""
import os
import requests
from typing import Optional, Dict, List
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

class TMDBClient:
    """
    Client für die TMDB API, um Filmdaten und Poster abzurufen.
    """
    def __init__(self):
        self.api_key = TMDB_API_KEY

    def search_movie(self, title: str, year: str = None) -> Optional[Dict]:
        """
        Suche nach einem Film und hole detaillierte Informationen.
        """
        try:
            # Suche nach dem Film
            search_url = f"{BASE_URL}/search/movie"
            params = {
                "api_key": self.api_key,
                "query": title,
                "year": year
            }

            search_response = requests.get(search_url, params=params)
            search_data = search_response.json()

            if search_data.get("results"):
                movie = search_data["results"][0]
                movie_id = movie["id"]

                # Hole detaillierte Informationen
                details_url = f"{BASE_URL}/movie/{movie_id}"
                details_params = {
                    "api_key": self.api_key,
                    "append_to_response": "credits,images"
                }

                details_response = requests.get(details_url, params=details_params)
                details = details_response.json()

                return {
                    "title": details["title"],
                    "original_title": details["original_title"],
                    "director": next((crew["name"] for crew in details["credits"]["crew"]
                                   if crew["job"] == "Director"), "Unknown"),
                    "year": details["release_date"][:4],
                    "poster": f"https://image.tmdb.org/t/p/w500{details['poster_path']}" if details.get('poster_path') else None,
                    "backdrop": f"https://image.tmdb.org/t/p/original{details['backdrop_path']}" if details.get('backdrop_path') else None,
                    "imdb_id": details.get("imdb_id", "").replace("tt", ""),
                    "tmdb_id": details["id"],
                    "country": next((country["iso_3166_1"] for country in details["production_countries"]), "Unknown"),
                    "genre": [genre["name"] for genre in details["genres"]],
                    "plot": details["overview"],
                    "runtime": details["runtime"],
                    "vote_average": details["vote_average"],
                    "vote_count": details["vote_count"],
                    "popularity": details["popularity"],
                    "cast": [{"name": cast["name"], "character": cast["character"]}
                            for cast in details["credits"]["crew"][:10]]
                }

            return None

        except Exception as e:
            print(f"Fehler bei der TMDB-Abfrage: {str(e)}")
            return None

    def get_movie_poster(self, tmdb_id: str) -> Optional[str]:
        """
        Hole den Poster-URL für einen Film.
        """
        try:
            url = f"{BASE_URL}/movie/{tmdb_id}/images"
            params = {"api_key": self.api_key}

            response = requests.get(url, params=params)
            data = response.json()

            if data.get("posters"):
                poster_path = data["posters"][0]["file_path"]
                return f"https://image.tmdb.org/t/p/w500{poster_path}"

            return None

        except Exception as e:
            print(f"Fehler beim Abrufen des Posters: {str(e)}")
            return None

