"""
movie_api.py - OMDB API Client für MovieProjekt
"""
import os
import requests
from typing import Optional, Dict
import dotenv

# Lade Umgebungsvariablen
dotenv.load_dotenv()

API_KEY = os.getenv("OMDB_API_KEY")
BASE_URL = f"http://www.omdbapi.com/?i=tt3896198&apikey={API_KEY}"

class OMDBClient:
    """
    Client für die OMDB API, um Filmdaten anhand des Titels abzurufen.
    """
    def __init__(self):
        self.BASE_URL = BASE_URL

    def get_movie(self, title: str) -> Optional[Dict]:
        """
        Hole Filmdaten von der OMDB API anhand des Titels.
        Args:
            title (str): Der Titel des Films.
        Returns:
            dict: Filmdaten (Name, Regisseur, Jahr, Poster, Land, Genre, Plot, Bewertung)
            oder None, falls kein Film gefunden wurde.
        """
        url = self.BASE_URL + "&t=" + title
        response = requests.get(url)
        if response.status_code == 200 and response.json().get("Response") == "True":
            data = response.json()
            new_movie = {
                "name": data["Title"],
                "director": data["Director"],
                "year": data["Year"],
                "poster": data["Poster"],
                "country": data["Country"],
                "genre": data["Genre"],
                "plot": data["Plot"],
                "rating": data["imdbRating"]
            }
            return new_movie
        return None