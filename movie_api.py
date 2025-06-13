"""
movie_api.py - OMDB API Client für MovieProjekt
"""
import os
import requests
from typing import Optional, Dict, List
import dotenv

# Lade Umgebungsvariablen
dotenv.load_dotenv()

API_KEY = os.getenv("OMDB_API_KEY")
BASE_URL = "http://www.omdbapi.com/"

class OMDBClient:
    """
    Client für die OMDB API, um Filmdaten anhand des Titels abzurufen.
    """
    def __init__(self):
        self.api_key = API_KEY

    def search_movies(self, search_term: str) -> List[Dict]:
        """
        Suche nach Filmen mit einem Suchbegriff.
        Args:
            search_term (str): Der Suchbegriff
        Returns:
            list: Liste von gefundenen Filmen
        """
        try:
            params = {
                'apikey': self.api_key,
                's': search_term,
                'type': 'movie'
            }

            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("Response") == "True" and "Search" in data:
                return data["Search"]
            return []

        except Exception as e:
            print(f"Fehler bei der Filmsuche: {str(e)}")
            return []

    def get_movie(self, title: str) -> Optional[Dict]:
        """
        Hole Filmdaten von der OMDB API anhand des Titels.
        Versucht zuerst eine exakte Suche, dann eine Ähnlichkeitssuche.
        Args:
            title (str): Der Titel des Films.
        Returns:
            dict: Filmdaten oder None, falls kein Film gefunden wurde.
        """
        try:
            # Erst versuchen mit exaktem Titel
            params = {
                'apikey': self.api_key,
                't': title,
                'type': 'movie',
                'plot': 'full'
            }

            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("Response") == "True":
                return {
                    "name": data.get("Title", ""),
                    "director": data.get("Director", "N/A"),
                    "year": data.get("Year", ""),
                    "poster": data.get("Poster", ""),
                    "country": data.get("Country", "N/A"),
                    "genre": data.get("Genre", "N/A"),
                    "plot": data.get("Plot", "N/A"),
                    "rating": data.get("imdbRating", "N/A")
                }

            # Wenn nicht gefunden, versuche Suche
            search_results = self.search_movies(title)
            if search_results:
                # Hole Details des ersten Suchergebnisses
                movie_id = search_results[0]['imdbID']
                params['i'] = movie_id
                del params['t']

                response = requests.get(BASE_URL, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()
                if data.get("Response") == "True":
                    return {
                        "name": data.get("Title", ""),
                        "director": data.get("Director", "N/A"),
                        "year": data.get("Year", ""),
                        "poster": data.get("Poster", ""),
                        "country": data.get("Country", "N/A"),
                        "genre": data.get("Genre", "N/A"),
                        "plot": data.get("Plot", "N/A"),
                        "rating": data.get("imdbRating", "N/A")
                    }

            print(f"Film nicht gefunden: {title}")
            return None

        except requests.RequestException as e:
            print(f"Fehler bei der OMDB-API-Anfrage für {title}: {str(e)}")
            return None
        except Exception as e:
            print(f"Unerwarteter Fehler bei der Filmsuche für {title}: {str(e)}")
            return None
