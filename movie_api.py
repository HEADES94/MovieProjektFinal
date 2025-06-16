"""
movie_api.py - OMDB API Client für MovieProjekt
"""
import os
import requests
from typing import Optional, Dict
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

OMDB_API_KEY = os.getenv("OMDB_API_KEY")
BASE_URL = "http://www.omdbapi.com/"

class OMDBClient:
    """
    Client für die OMDB API
    """
    def __init__(self):
        self.api_key = OMDB_API_KEY

    def get_movie(self, title: str, year: str = None) -> Optional[Dict]:
        """
        Hole Filmdaten von der OMDB API
        """
        try:
            params = {
                "apikey": self.api_key,
                "t": title,
                "y": year,
                "plot": "full"
            }

            response = requests.get(BASE_URL, params=params)
            data = response.json()

            if data.get("Response") == "True":
                return {
                    "name": data.get("Title", ""),
                    "director": data.get("Director", ""),
                    "year": data.get("Year", ""),
                    "poster": data.get("Poster", ""),
                    "rating": data.get("imdbRating", "N/A"),
                    "genre": data.get("Genre", ""),
                    "country": data.get("Country", ""),
                    "plot": data.get("Plot", "")
                }
            return None

        except Exception as e:
            print(f"Fehler beim Abrufen der Filmdaten: {str(e)}")
            return None
