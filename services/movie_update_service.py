"""
Movie Update Service - Automatische Aktualisierung der Filmdatenbank
"""
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Set
from dotenv import load_dotenv
from datamanager.sqlite_data_manager import SQliteDataManager
from data_models import Movie, Actor, MovieActor

# Lade Umgebungsvariablen
load_dotenv()

class MovieUpdateService:
    def __init__(self, data_manager: SQliteDataManager):
        self.data_manager = data_manager
        self.tmdb_api_key = os.getenv("TMDB_API_KEY")
        self.omdb_api_key = os.getenv("OMDB_API_KEY")
        self.base_url = "https://api.themoviedb.org/3"
        self.omdb_url = "http://www.omdbapi.com/"
        self._processed_titles: Set[str] = set()
        self._last_update = None
        self._update_interval = timedelta(hours=1)  # Zurück zum normalen Intervall von 1 Stunde
        self.headers = {
            'Authorization': f'Bearer {self.tmdb_api_key}',
            'accept': 'application/json'
        }

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
        # Datum für Filme der letzten 30 Jahre
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 30)  # 30 Jahre

        url = f"{self.base_url}/discover/movie"
        params = {
            'api_key': self.tmdb_api_key,
            'primary_release_date.gte': start_date.strftime('%Y-%m-%d'),
            'primary_release_date.lte': end_date.strftime('%Y-%m-%d'),
            'sort_by': 'popularity.desc',  # Nach Popularität sortieren
            'language': 'de-DE',
            'region': 'DE',
            'with_release_type': '2|3',  # Theater und Digital
            'vote_average.gte': 1,  # Mindestens 1 Stern
            'include_adult': 'false',
            'page': 1
        }

        all_movies = []
        try:
            # Hole bis zu 50 Seiten von Ergebnissen für deutlich mehr Filme
            for page in range(1, 51):
                params['page'] = page
                response = requests.get(url, params=params, timeout=15)  # Timeout auf 15s erhöht
                response.raise_for_status()

                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    print(f"Seite {page}: {len(results)} Filme gefunden")
                    if not results:  # Wenn keine Ergebnisse mehr, beende die Schleife
                        break
                    all_movies.extend(results)
                else:
                    print(f"Fehler bei Seite {page}: Status {response.status_code}")

            # Entferne Duplikate basierend auf normalisierten Titeln
            unique_movies = {}
            for movie in all_movies:
                if not movie.get('title'):  # Überspringe Einträge ohne Titel
                    continue

                # Bereinige und normalisiere den Titel
                clean_title = self.clean_title(movie['title'])
                norm_title = self.normalize_title(clean_title)

                if norm_title not in self._processed_titles and norm_title not in unique_movies:
                    unique_movies[norm_title] = movie
                    self._processed_titles.add(norm_title)

            print(f"Insgesamt gefundene Filme: {len(unique_movies)}")
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

    def get_actors_from_omdb(self, title: str) -> List[Dict]:
        """Hole Schauspieler von OMDB API"""
        try:
            params = {
                'apikey': self.omdb_api_key,
                't': title,
                'plot': 'short'
            }
            response = requests.get(self.omdb_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get('Response') == 'True' and 'Actors' in data:
                actors = []
                for actor_name in data['Actors'].split(','):
                    actor_name = actor_name.strip()
                    if actor_name:
                        actors.append({
                            'name': actor_name,
                            'role_name': ''  # OMDB gibt keine Rolleninformationen
                        })
                return actors
            return []
        except Exception as e:
            print(f"Fehler beim Abrufen der Schauspieler von OMDB: {e}")
            return []

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
            try:
                for movie_data in new_movies:
                    # Überprüfe, ob der Film bereits existiert
                    existing_movie = session.query(Movie).filter_by(
                        title=movie_data['title']
                    ).first()

                    if not existing_movie:
                        # Hole zusätzliche Details von OMDB
                        try:
                            omdb_data = self.get_movie_details_from_omdb(movie_data['title'])
                        except Exception as e:
                            print(f"OMDB API Fehler für {movie_data['title']}: {e}")
                            omdb_data = {}

                        # Erstelle einen neuen Film
                        try:
                            release_date = datetime.strptime(
                                movie_data.get('release_date', ''),
                                '%Y-%m-%d'
                            ).year if movie_data.get('release_date') else None
                        except ValueError:
                            release_date = None

                        # Sichere Konvertierung der IMDB-Bewertung
                        try:
                            imdb_rating = omdb_data.get('imdbRating', '0')
                            rating = float(imdb_rating) if imdb_rating and imdb_rating != 'N/A' else 0.0
                        except (ValueError, TypeError):
                            rating = 0.0

                        movie = Movie(
                            title=movie_data['title'],
                            release_year=release_date,
                            description=movie_data.get('overview', ''),
                            poster_url=f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}" if movie_data.get('poster_path') else None,
                            rating=rating,
                            genre=omdb_data.get('Genre', '') if omdb_data.get('Genre') != 'N/A' else '',
                            director=omdb_data.get('Director', '') if omdb_data.get('Director') != 'N/A' else ''
                        )
                        session.add(movie)
                        session.flush()  # Damit wir die movie.id haben

                        # Hole und füge Schauspieler hinzu
                        actors = self.get_actors_from_omdb(movie_data['title'])
                        for actor_data in actors:
                            # Prüfe ob Schauspieler bereits existiert
                            actor = session.query(Actor).filter_by(
                                name=actor_data['name']
                            ).first()

                            if not actor:
                                actor = Actor(name=actor_data['name'])
                                session.add(actor)
                                session.flush()

                            # Verknüpfe Film und Schauspieler
                            movie_actor = MovieActor(
                                movie_id=movie.id,
                                actor_id=actor.id,
                                role_name=actor_data.get('role_name', '')
                            )
                            session.add(movie_actor)

                        print(f"Film hinzugefügt: {movie.title}")
                        added_count += 1

                session.commit()
                self._last_update = datetime.now()
                print(f"Erfolgreich {added_count} neue Filme hinzugefügt")
                return added_count

            except Exception as e:
                print(f"Fehler beim Aktualisieren der Filmdatenbank: {e}")
                session.rollback()
                return 0

    def get_movie_details_from_omdb(self, title: str) -> dict:
        """Hole detaillierte Filminformationen von OMDB"""
        try:
            params = {
                'apikey': self.omdb_api_key,
                't': title,
                'plot': 'full'
            }
            response = requests.get(self.omdb_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get('Response') == 'True':
                return data
            print(f"Keine OMDB-Daten gefunden für: {title}")
            return {}
        except Exception as e:
            print(f"Fehler beim Abrufen der OMDB-Details für {title}: {e}")
            return {}

    def add_movie(self, title: str) -> Movie:
        """Fügt einen einzelnen Film manuell hinzu"""
        with self.data_manager.SessionFactory() as session:
            try:
                # Prüfe ob der Film bereits existiert
                existing_movie = session.query(Movie).filter(
                    Movie.title.ilike(f"%{title}%")
                ).first()

                if existing_movie:
                    return existing_movie

                # Hole Filmdaten von OMDB
                movie_data = self.get_movie_details_from_omdb(title)
                if not movie_data:
                    return None

                # Sichere Konvertierung der Werte
                year = int(movie_data.get('Year', '0').split('–')[0]) if movie_data.get('Year', 'N/A') != 'N/A' else None
                rating = float(movie_data.get('imdbRating', '0')) if movie_data.get('imdbRating', 'N/A') != 'N/A' else None

                # Erstelle neuen Film
                new_movie = Movie(
                    title=movie_data.get('Title', title),
                    description=movie_data.get('Plot', ''),
                    release_year=year,
                    genre=movie_data.get('Genre', ''),
                    director=movie_data.get('Director', ''),
                    rating=rating,
                    poster_url=movie_data.get('Poster', '') if movie_data.get('Poster', '') != 'N/A' else '',
                    country=movie_data.get('Country', '')
                )

                session.add(new_movie)
                session.commit()
                session.refresh(new_movie)
                return new_movie

            except Exception as e:
                session.rollback()
                print(f"Fehler beim Hinzufügen von {title}: {str(e)}")
                return None
