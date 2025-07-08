#!/usr/bin/env python3
"""
Erweiterte TMDB-Import für 2000 saubere Filme
Mit verbesserter Poster-Behandlung
"""

import os
import sys
import requests
import time
import logging
import re
from typing import List, Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datamanager.sqlite_data_manager import SQliteDataManager
from data_models import Movie
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extended_tmdb_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ExtendedTMDBImporter:
    def __init__(self):
        self.tmdb_api_key = os.getenv('TMDB_API_KEY')
        self.data_manager = SQliteDataManager("sqlite:///movie_app.db")
        self.imported_titles = set()
        self.target_count = 2000  # Ziel: 2000 Filme

        if not self.tmdb_api_key:
            raise ValueError("TMDB API Key fehlt!")

        self.genres = {
            28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
            99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
            27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
            53: "Thriller", 10752: "War", 37: "Western"
        }

        # Blacklist für problematische Inhalte
        self.forbidden_words = [
            'playboy', 'playmate', 'nude', 'naked', 'erotic', 'xxx', 'porn', 'adult',
            'sex', 'sexy', 'sensual', 'seduction', 'desire', 'lust', 'bikini', 'strip',
            'escort', 'massage', 'fetish', 'temptation', 'softcore', 'hardcore'
        ]

        # IMDB Top Ratings für Korrektur
        self.imdb_ratings = {
            "The Shawshank Redemption": 9.3,
            "The Godfather": 9.2,
            "The Dark Knight": 9.0,
            "The Godfather Part II": 9.0,
            "12 Angry Men": 9.0,
            "Schindler's List": 8.9,
            "Pulp Fiction": 8.9,
            "The Lord of the Rings: The Return of the King": 8.9,
            "Fight Club": 8.8,
            "Forrest Gump": 8.8,
            "Inception": 8.7,
            "The Matrix": 8.7,
            "Goodfellas": 8.7,
            "Star Wars": 8.6,
            "The Green Mile": 8.6,
            "Saving Private Ryan": 8.6,
            "Terminator 2: Judgment Day": 8.5,
            "Back to the Future": 8.5,
            "The Lion King": 8.5,
            "Gladiator": 8.5,
            "The Departed": 8.5,
            "Alien": 8.4,
            "Django Unchained": 8.4,
            "WALL·E": 8.4
        }

    def get_current_count(self) -> int:
        """Gibt die aktuelle Anzahl Filme zurück."""
        try:
            with self.data_manager.SessionFactory() as session:
                return session.query(Movie).count()
        except:
            return 0

    def load_existing_titles(self):
        """Lädt bereits vorhandene Titel."""
        try:
            with self.data_manager.SessionFactory() as session:
                movies = session.query(Movie.title, Movie.release_year).all()
                self.imported_titles = {f"{movie.title.lower().replace(' ', '')}_{movie.release_year}" for movie in movies}
                logger.info(f"Geladene existierende Titel: {len(self.imported_titles)}")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Titel: {str(e)}")

    def is_clean_title(self, title: str) -> bool:
        """Überprüft ob der Titel sauber ist."""
        title_lower = title.lower()

        # Prüfe verbotene Wörter
        for word in self.forbidden_words:
            if word in title_lower:
                return False

        # Keine asiatischen Zeichen
        if re.search(r'[가-힣一-龯ひらがなカタカナ]', title):
            return False

        # Keine überlangen Titel
        if len(title) > 60:
            return False

        # Keine verdächtigen Sonderzeichen
        if re.search(r'[♥♦♠♣★☆♪♫◄►▲▼]', title):
            return False

        return True

    def is_quality_movie(self, movie: Dict) -> bool:
        """Prüft Filmqualität mit erweiterten Kriterien."""

        # Mindest-Bewertungen (lockerer für mehr Filme)
        vote_count = movie.get('vote_count', 0)
        if vote_count < 50:  # Reduziert von 200 auf 50
            return False

        # Mindest-Rating (lockerer)
        vote_average = movie.get('vote_average', 0)
        if vote_average < 5.5:  # Reduziert von 6.0 auf 5.5
            return False

        # Englisch oder Deutsch
        original_language = movie.get('original_language', '')
        if original_language not in ['en', 'de']:
            return False

        # Gültiges Release-Jahr (erweitert)
        release_date = movie.get('release_date', '')
        if release_date:
            try:
                year = int(release_date[:4])
                if year < 1940 or year > 2025:  # Erweitert von 1950
                    return False
            except:
                return False

        # Keine Adult-Inhalte
        adult = movie.get('adult', False)
        if adult:
            return False

        return True

    def get_corrected_rating(self, title: str, tmdb_rating: float) -> float:
        """Korrigiert Ratings mit IMDB-Daten."""

        # Prüfe IMDB Top-Liste
        for imdb_title, imdb_rating in self.imdb_ratings.items():
            if imdb_title.lower() in title.lower() or title.lower() in imdb_title.lower():
                logger.info(f"IMDB-Rating korrigiert: {title} -> {imdb_rating}")
                return imdb_rating

        # Korrigiere unrealistische Ratings
        if tmdb_rating > 9.5:
            return 8.5
        elif tmdb_rating < 5.5:
            return 5.5

        return tmdb_rating

    def validate_poster_url(self, poster_path: str) -> Optional[str]:
        """Validiert und gibt Poster-URL zurück."""
        if not poster_path:
            return None

        # Erstelle vollständige URL
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"

        # Teste URL kurz (ohne vollständigen Download)
        try:
            response = requests.head(poster_url, timeout=3)
            if response.status_code == 200:
                return poster_url
        except:
            pass

        return poster_url  # Gib URL trotzdem zurück, auch bei Fehlern

    def get_movies_from_endpoint(self, endpoint: str, params: Dict, pages: int = 5) -> List[Dict]:
        """Holt Filme von TMDB mit Filterung."""
        movies = []

        for page in range(1, pages + 1):
            try:
                current_params = params.copy()
                current_params.update({
                    'api_key': self.tmdb_api_key,
                    'page': page,
                    'language': 'en-US',
                    'region': 'US',
                    'include_adult': 'false'
                })

                response = requests.get(endpoint, params=current_params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if 'results' in data:
                    clean_movies = []
                    for movie in data['results']:
                        title = movie.get('title', '')
                        if (self.is_clean_title(title) and
                            self.is_quality_movie(movie)):
                            clean_movies.append(movie)

                    movies.extend(clean_movies)
                    logger.info(f"Seite {page}: {len(clean_movies)}/{len(data['results'])} saubere Filme")

                time.sleep(0.25)

            except Exception as e:
                logger.error(f"Fehler bei Seite {page}: {str(e)}")

        return movies

    def prepare_movie_data(self, movie: Dict) -> Optional[Dict]:
        """Bereitet Filmdaten vor."""
        try:
            title = movie.get('title', '').strip()
            if not title:
                return None

            # Release Jahr
            release_date = movie.get('release_date', '')
            try:
                release_year = int(release_date[:4]) if release_date else None
            except:
                release_year = None

            if not release_year:
                return None

            # Duplikat-Check
            movie_key = f"{title.lower().replace(' ', '')}_{release_year}"
            if movie_key in self.imported_titles:
                return None

            # Rating korrigieren
            tmdb_rating = movie.get('vote_average', 0)
            corrected_rating = self.get_corrected_rating(title, tmdb_rating)

            # Poster validieren
            poster_path = movie.get('poster_path')
            poster_url = self.validate_poster_url(poster_path)

            # Genre
            genre_ids = movie.get('genre_ids', [])
            genres = [self.genres.get(gid) for gid in genre_ids if gid in self.genres]
            genre_string = ', '.join(genres) if genres else 'Drama'

            # Beschreibung
            description = movie.get('overview', '').strip()
            if not description or len(description) < 20:
                description = f"Ein {genre_string}-Film aus dem Jahr {release_year}."

            # Prüfe Beschreibung auf problematische Inhalte
            desc_lower = description.lower()
            for word in self.forbidden_words:
                if word in desc_lower:
                    description = f"Ein {genre_string}-Film aus dem Jahr {release_year}."
                    break

            self.imported_titles.add(movie_key)

            return {
                'title': title,
                'genre': genre_string,
                'release_year': release_year,
                'description': description,
                'rating': corrected_rating,
                'poster_url': poster_url,
                'director': 'Unknown'
            }

        except Exception as e:
            logger.error(f"Fehler bei Vorbereitung: {str(e)}")
            return None

    def save_movies_batch(self, movies_data: List[Dict]) -> int:
        """Speichert Filme in Batches."""
        saved_count = 0

        try:
            with self.data_manager.SessionFactory() as session:
                for movie_data in movies_data:
                    try:
                        movie = Movie(
                            title=movie_data['title'],
                            genre=movie_data['genre'],
                            release_year=movie_data['release_year'],
                            description=movie_data['description'],
                            rating=movie_data['rating'],
                            poster_url=movie_data['poster_url'],
                            director=movie_data['director']
                        )
                        session.add(movie)
                        saved_count += 1
                    except Exception as e:
                        logger.error(f"Fehler beim Hinzufügen von '{movie_data['title']}': {str(e)}")

                session.commit()
                logger.info(f"Batch gespeichert: {saved_count} Filme")

        except Exception as e:
            logger.error(f"Fehler beim Batch-Speichern: {str(e)}")

        return saved_count

    def extend_database(self):
        """Erweitert die Datenbank auf 2000 Filme."""
        current_count = self.get_current_count()
        logger.info(f"Aktuelle Filme: {current_count}, Ziel: {self.target_count}")

        if current_count >= self.target_count:
            logger.info("Ziel bereits erreicht!")
            return

        self.load_existing_titles()
        needed_movies = self.target_count - current_count
        logger.info(f"Benötigte Filme: {needed_movies}")

        all_movies_data = []

        # Erweiterte Quellen für mehr Filme

        # 1. Top bewertete Filme (mehr Seiten)
        logger.info("Lade top bewertete Filme...")
        top_rated = self.get_movies_from_endpoint(
            "https://api.themoviedb.org/3/movie/top_rated",
            {'vote_count.gte': 100}, pages=15  # Mehr Seiten
        )

        # 2. Populäre Filme (mehr Seiten)
        logger.info("Lade populäre Filme...")
        popular = self.get_movies_from_endpoint(
            "https://api.themoviedb.org/3/movie/popular",
            {'vote_count.gte': 100}, pages=12  # Mehr Seiten
        )

        # 3. Filme nach Genres (erweitert)
        logger.info("Lade Filme nach Genres...")
        all_genres = [28, 35, 18, 53, 27, 878, 80, 10749, 12, 14, 16, 10751, 99, 36, 10402, 9648, 10752, 37]

        for genre_id in all_genres:
            genre_name = self.genres.get(genre_id, f"Genre_{genre_id}")
            logger.info(f"Lade {genre_name} Filme...")
            genre_movies = self.get_movies_from_endpoint(
                "https://api.themoviedb.org/3/discover/movie",
                {
                    'with_genres': genre_id,
                    'sort_by': 'vote_average.desc',
                    'vote_count.gte': 100,
                    'vote_average.gte': 6.0
                }, pages=8  # Mehr Seiten pro Genre
            )
            top_rated.extend(genre_movies)

        # 4. Filme nach Jahren (erweitert)
        logger.info("Lade Filme nach Jahren...")
        for year in range(2024, 1980, -1):  # Von 2024 bis 1980
            if len(all_movies_data) >= needed_movies:
                break
            year_movies = self.get_movies_from_endpoint(
                "https://api.themoviedb.org/3/discover/movie",
                {
                    'primary_release_year': year,
                    'sort_by': 'vote_average.desc',
                    'vote_count.gte': 50,
                    'vote_average.gte': 6.0
                }, pages=4
            )
            top_rated.extend(year_movies)

        # 5. Jetzt spielende Filme
        logger.info("Lade aktuelle Filme...")
        now_playing = self.get_movies_from_endpoint(
            "https://api.themoviedb.org/3/movie/now_playing",
            {}, pages=8
        )

        # Alle Filme verarbeiten
        all_tmdb_movies = top_rated + popular + now_playing
        logger.info(f"Verarbeite {len(all_tmdb_movies)} gesammelte Filme...")

        for movie in all_tmdb_movies:
            if len(all_movies_data) >= needed_movies:
                break

            prepared = self.prepare_movie_data(movie)
            if prepared:
                all_movies_data.append(prepared)

        # Speichern
        logger.info(f"Speichere {len(all_movies_data)} neue Filme...")
        batch_size = 50
        total_saved = 0

        for i in range(0, len(all_movies_data), batch_size):
            batch = all_movies_data[i:i + batch_size]
            saved = self.save_movies_batch(batch)
            total_saved += saved

            if total_saved % 200 == 0:
                logger.info(f"Fortschritt: {total_saved} neue Filme gespeichert")

        # Final Count
        final_count = self.get_current_count()
        logger.info(f"Erweiterung abgeschlossen! Filme in DB: {final_count}")
        logger.info(f"Neue Filme hinzugefügt: {total_saved}")

def main():
    try:
        importer = ExtendedTMDBImporter()
        importer.extend_database()
    except Exception as e:
        logger.error(f"Kritischer Fehler: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
