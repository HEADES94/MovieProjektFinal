"""
Movie Update Service - Automatic movie database updates.
"""
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Set
from dotenv import load_dotenv
from datamanager.sqlite_data_manager import SQliteDataManager
from data_models import Movie, Actor, MovieActor

# Load environment variables
load_dotenv()

class MovieUpdateService:
    """Service for automatic movie database updates."""

    def __init__(self, data_manager: SQliteDataManager):
        self.data_manager = data_manager
        self.tmdb_api_key = os.getenv("TMDB_API_KEY")
        self.omdb_api_key = os.getenv("OMDB_API_KEY")
        self.base_url = "https://api.themoviedb.org/3"
        self.omdb_url = "http://www.omdbapi.com/"
        self._processed_titles: Set[str] = set()
        self._last_update = None
        self._update_interval = timedelta(hours=1)
        self.headers = {
            'Authorization': f'Bearer {self.tmdb_api_key}',
            'accept': 'application/json'
        }

    def normalize_title(self, title: str) -> str:
        """Normalize a movie title for better comparison."""
        import re
        # Remove special characters and make everything lowercase
        normalized = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())
        # Remove multiple spaces
        normalized = ' '.join(normalized.split())
        return normalized

    def clean_title(self, title: str) -> str:
        """Clean a movie title from common variations."""
        # Remove common additions
        removals = [
            r'\s*\([^)]*\)',  # Parentheses and content
            r'\s*\[[^\]]*\]',  # Square brackets and content
            r'\s*-\s*.*$',     # Everything after a hyphen
            r'\s*:\s*.*$',     # Everything after a colon
            r'\s+\d{4}$',      # Year at the end
            r'\s*(Part|Teil)\s*\d+',  # "Part" or "Teil" with number
            r'\s*HD\s*$',      # HD at the end
            r'\s*\d+p\s*$',    # Resolution (e.g. 1080p)
        ]

        result = title
        for pattern in removals:
            import re
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        return result.strip()

    def get_new_movies(self) -> List[Dict]:
        """Get new movies from TMDB API."""
        # Date for movies from the last 30 years
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 30)  # 30 years

        url = f"{self.base_url}/discover/movie"
        params = {
            'api_key': self.tmdb_api_key,
            'primary_release_date.gte': start_date.strftime('%Y-%m-%d'),
            'primary_release_date.lte': end_date.strftime('%Y-%m-%d'),
            'sort_by': 'popularity.desc',  # Sort by popularity
            'language': 'de-DE',
            'region': 'DE',
            'with_release_type': '2|3',  # Theater and Digital
            'vote_average.gte': 1,  # At least 1 star
            'include_adult': 'false',
            'page': 1
        }

        all_movies = []
        try:
            # Fetch up to 50 pages of results for significantly more movies
            for page in range(1, 51):
                params['page'] = page
                response = requests.get(url, params=params, timeout=15)  # Increased timeout to 15s
                response.raise_for_status()

                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    print(f"Page {page}: {len(results)} movies found")
                    if not results:  # If no more results, exit the loop
                        break
                    all_movies.extend(results)
                else:
                    print(f"Error on page {page}: Status {response.status_code}")

            # Remove duplicates based on normalized titles
            unique_movies = {}
            for movie in all_movies:
                if not movie.get('title'):  # Skip entries without a title
                    continue

                # Clean and normalize the title
                clean_title = self.clean_title(movie['title'])
                norm_title = self.normalize_title(clean_title)

                if norm_title not in self._processed_titles and norm_title not in unique_movies:
                    unique_movies[norm_title] = movie
                    self._processed_titles.add(norm_title)

            print(f"Total unique movies found: {len(unique_movies)}")
            return list(unique_movies.values())

        except requests.exceptions.RequestException as e:
            print(f"Error fetching movies: {e}")
            return []

    def is_similar_title(self, title1: str, title2: str, threshold: float = 0.9) -> bool:
        """Check if two titles are similar."""
        from difflib import SequenceMatcher

        # Clean and normalize both titles
        clean1 = self.clean_title(title1)
        clean2 = self.clean_title(title2)
        norm1 = self.normalize_title(clean1)
        norm2 = self.normalize_title(clean2)

        # Calculate the similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity >= threshold

    def get_actors_from_omdb(self, title: str) -> List[Dict]:
        """Fetch actors from OMDB API."""
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
                            'role_name': ''  # OMDB does not provide role information
                        })
                return actors
            return []
        except Exception as e:
            print(f"Error fetching actors from OMDB: {e}")
            return []

    def update_movie_database(self) -> int:
        """
        Update the movie database with new movies.
        Returns:
            int: Number of movies added
        """
        if (self._last_update and
            datetime.now() - self._last_update < self._update_interval):
            return 0

        new_movies = self.get_new_movies()
        added_count = 0

        with self.data_manager.SessionFactory() as session:
            try:
                for movie_data in new_movies:
                    # Check if the movie already exists
                    existing_movie = session.query(Movie).filter_by(
                        title=movie_data['title']
                    ).first()

                    if not existing_movie:
                        # Fetch additional details from OMDB
                        try:
                            omdb_data = self.get_movie_details_from_omdb(movie_data['title'])
                        except Exception as e:
                            print(f"OMDB API error for {movie_data['title']}: {e}")
                            omdb_data = {}

                        # Create a new movie
                        try:
                            release_date = datetime.strptime(
                                movie_data.get('release_date', ''),
                                '%Y-%m-%d'
                            ).year if movie_data.get('release_date') else None
                        except ValueError:
                            release_date = None

                        # Safe conversion of IMDB rating
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
                        session.flush()  # So we have the movie.id

                        # Fetch and add actors
                        actors = self.get_actors_from_omdb(movie_data['title'])
                        for actor_data in actors:
                            # Check if actor already exists
                            actor = session.query(Actor).filter_by(
                                name=actor_data['name']
                            ).first()

                            if not actor:
                                actor = Actor(name=actor_data['name'])
                                session.add(actor)
                                session.flush()

                            # Link movie and actor
                            movie_actor = MovieActor(
                                movie_id=movie.id,
                                actor_id=actor.id,
                                role_name=actor_data.get('role_name', '')
                            )
                            session.add(movie_actor)

                        print(f"Movie added: {movie.title}")
                        added_count += 1

                session.commit()
                self._last_update = datetime.now()
                print(f"Successfully added {added_count} new movies")
                return added_count

            except Exception as e:
                print(f"Error updating movie database: {e}")
                session.rollback()
                return 0

    def get_movie_details_from_omdb(self, title: str) -> dict:
        """Fetch detailed movie information from OMDB."""
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
            print(f"No OMDB data found for: {title}")
            return {}
        except Exception as e:
            print(f"Error fetching OMDB details for {title}: {e}")
            return {}

    def add_movie(self, title: str) -> Movie:
        """Manually add a single movie."""
        with self.data_manager.SessionFactory() as session:
            try:
                # Check if the movie already exists
                existing_movie = session.query(Movie).filter(
                    Movie.title.ilike(f"%{title}%")
                ).first()

                if existing_movie:
                    return existing_movie

                # Fetch movie data from OMDB
                movie_data = self.get_movie_details_from_omdb(title)
                if not movie_data:
                    return None

                # Safe conversion of values
                year = int(movie_data.get('Year', '0').split('–')[0]) if movie_data.get('Year', 'N/A') != 'N/A' else None
                rating = float(movie_data.get('imdbRating', '0')) if movie_data.get('imdbRating', 'N/A') != 'N/A' else None

                # Create new movie
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
                print(f"Error adding {title}: {str(e)}")
                return None

    def validate_movie_data(self, movie_data: Dict) -> bool:
        """Validate movie data before saving."""
        try:
            # Validate title
            title = movie_data.get('title', '').strip()
            if not title or len(title) < 2:
                return False

            # Validate and correct rating
            rating = movie_data.get('rating', 0)
            if isinstance(rating, (int, float)):
                if rating > 10:  # Correct broken ratings
                    rating = rating / 1000000 if rating > 1000000 else min(rating / 100, 10)
                rating = max(0, min(rating, 10))  # Between 0 and 10
                movie_data['rating'] = round(rating, 1)
            else:
                movie_data['rating'] = 0.0

            # Validate release year
            year = movie_data.get('release_year')
            if year:
                try:
                    year = int(year)
                    if year < 1900 or year > 2030:
                        movie_data['release_year'] = None
                except (ValueError, TypeError):
                    movie_data['release_year'] = None

            # Validate poster URL
            poster_url = movie_data.get('poster_url', '')
            if poster_url and not poster_url.startswith(('http://', 'https://')):
                movie_data['poster_url'] = None

            return True

        except Exception as e:
            print(f"Error in data validation: {str(e)}")
            return False

    def check_for_duplicates(self, title: str, year: int = None) -> bool:
        """Check for duplicate movies in the database."""
        try:
            with self.data_manager.SessionFactory() as session:
                query = session.query(Movie).filter(Movie.title.ilike(f"%{title}%"))
                if year:
                    query = query.filter(Movie.release_year == year)

                existing = query.first()
                return existing is not None
        except Exception as e:
            print(f"Error checking for duplicates: {str(e)}")
            return False
