"""
Movie Update Service - Automatische Aktualisierung der Filmdatenbank
"""
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Set
from dotenv import load_dotenv
from datamanager.sqlite_data_manager import SQliteDataManager
from data_models import Movie

# Lade Umgebungsvariablen
load_dotenv()

class MovieUpdateService:
    def __init__(self, data_manager: SQliteDataManager):
        self.data_manager = data_manager
        self.tmdb_api_key = os.getenv("TMDB_API_KEY")
        self.base_url = "https://api.themoviedb.org/3"
        self._processed_titles: Set[str] = set()
        self._last_update = None
        self._update_interval = timedelta(hours=1)  # Nur alle Stunde aktualisieren

    def normalize_title(self, title: str) -> str:
        """Normalisiert einen Filmtitel für besseren Vergleich"""
        import re
        # Entferne Sonderzeichen und mache alles lowercase
        normalized = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())
        # Entferne mehrfache Leerzeichen
        normalized = ' '.join(normalized.split())
        return normalized

    def clean_title(self, title: str) -> str:
        """Bereinigt einen Filmtitel von häufigen Variationen"""
        # Entferne häufige Zusätze
        removals = [
            r'\s*\([^)]*\)',  # Klammern und Inhalt
            r'\s*\[[^\]]*\]',  # Eckige Klammern und Inhalt
            r'\s*-\s*.*$',     # Alles nach einem Bindestrich
            r'\s*:\s*.*$',     # Alles nach einem Doppelpunkt
            r'\s+\d{4}$',      # Jahreszahl am Ende
            r'\s*(Part|Teil)\s*\d+',  # "Part" oder "Teil" mit Nummer
            r'\s*HD\s*$',      # HD am Ende
            r'\s*\d+p\s*$',    # Auflösung (z.B. 1080p)
        ]

        result = title
        for pattern in removals:
            import re
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        return result.strip()

    def get_new_movies(self) -> List[Dict]:
        """Holt neue Filme von TMDB API"""
        # Datum für neue Filme (letzte 30 Tage)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        url = f"{self.base_url}/discover/movie"
        params = {
            'api_key': self.tmdb_api_key,
            'primary_release_date.gte': start_date.strftime('%Y-%m-%d'),
            'primary_release_date.lte': end_date.strftime('%Y-%m-%d'),
            'sort_by': 'release_date.desc',
            'language': 'de-DE'  # Deutsche Sprache für Filmtitel
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # Löst eine Exception bei HTTP-Fehlern aus

            if response.status_code == 200:
                movies = response.json().get('results', [])
                # Entferne Duplikate basierend auf normalisierten Titeln
                unique_movies = {}
                for movie in movies:
                    # Bereinige und normalisiere den Titel
                    clean_title = self.clean_title(movie['title'])
                    norm_title = self.normalize_title(clean_title)

                    if norm_title not in self._processed_titles and norm_title not in unique_movies:
                        unique_movies[norm_title] = movie
                        self._processed_titles.add(norm_title)

                return list(unique_movies.values())

        except requests.exceptions.RequestException as e:
            print(f"Fehler beim API-Aufruf: {e}")

        return []

    def is_similar_title(self, title1: str, title2: str, threshold: float = 0.9) -> bool:
        """Überprüft ob zwei Titel ähnlich sind"""
        from difflib import SequenceMatcher

        # Bereinige und normalisiere beide Titel
        clean1 = self.clean_title(title1)
        clean2 = self.clean_title(title2)
        norm1 = self.normalize_title(clean1)
        norm2 = self.normalize_title(clean2)

        # Berechne die Ähnlichkeit
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity >= threshold

    def update_movie_database(self) -> int:
        """
        Aktualisiert die Filmdatenbank mit neuen Filmen.
        Returns:
            int: Anzahl der hinzugefügten Filme
        """
        if (self._last_update and
            datetime.now() - self._last_update < self._update_interval):
            return 0

        new_movies = self.get_new_movies()
        added_count = 0

        with self.data_manager.SessionFactory() as session:
            for movie_data in new_movies:
                # Überprüfe, ob der Film bereits existiert
                existing_movie = session.query(Movie).filter_by(
                    title=movie_data['title']
                ).first()

                if not existing_movie:
                    # Erstelle einen neuen Film
                    try:
                        release_date = datetime.strptime(
                            movie_data.get('release_date', ''),
                            '%Y-%m-%d'
                        ).year if movie_data.get('release_date') else None
                    except ValueError:
                        release_date = None

                    movie = Movie(
                        title=movie_data['title'],
                        release_year=release_date,
                        plot=movie_data.get('overview', ''),
                        poster_url=f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}" if movie_data.get('poster_path') else None
                    )
                    session.add(movie)
                    added_count += 1

            session.commit()

        self._last_update = datetime.now()
        return added_count
