#!/usr/bin/env python3
"""
Database Reset and Movie Import Script.
Resets the database and imports clean movie data from various categories.
"""

import os
import sys
import requests
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datamanager.sqlite_data_manager import SQliteDataManager
from data_models import Movie, User, UserMovie, Review, QuizAttempt, UserAchievement, Achievement, WatchlistItem, Actor, SuggestedQuestion
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_reset.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseResetAndImport:
    """Class for resetting database and importing movie data."""

    def __init__(self):
        self.tmdb_api_key = os.getenv('TMDB_API_KEY')
        self.omdb_api_key = os.getenv('OMDB_API_KEY')
        self.data_manager = SQliteDataManager("sqlite:///movie_app.db")
        self.session_counter = 0
        self.imported_movies = set()

        if not self.tmdb_api_key or not self.omdb_api_key:
            raise ValueError("API Keys missing in .env file!")

    def reset_database(self, keep_users: bool = True):
        """Reset the database, optionally keeping user data."""
        logger.info("Starting Database Reset...")

        with self.data_manager.SessionFactory() as session:
            try:
                if keep_users:
                    session.query(UserMovie).delete()
                    session.query(Review).delete()
                    session.query(QuizAttempt).delete()
                    session.query(UserAchievement).delete()
                    session.query(WatchlistItem).delete()
                    session.query(SuggestedQuestion).delete()
                    logger.info("User-related data cleared, users preserved")
                else:
                    session.query(User).delete()
                    logger.info("All user data cleared")

                session.query(Movie).delete()
                session.query(Actor).delete()
                session.query(Achievement).delete()
                session.commit()

                logger.info("Database reset completed successfully")
                return True

            except Exception as e:
                session.rollback()
                logger.error(f"Error during database reset: {str(e)}")
                return False

    def get_movie_details_from_omdb(self, title: str, year: str = None) -> Optional[Dict]:
        """Get detailed movie information from OMDB API."""
        try:
            params = {
                'apikey': self.omdb_api_key,
                't': title,
                'plot': 'full'
            }
            if year:
                params['y'] = year

            response = requests.get('http://www.omdbapi.com/', params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get('Response') == 'True':
                return data
            else:
                logger.warning(f"OMDB: No data found for {title}")
                return None

        except Exception as e:
            logger.error(f"OMDB API error for {title}: {str(e)}")
            return None

    def get_movies_from_tmdb(self, category: str, pages: int = 5) -> List[Dict]:
        """Get movies from TMDB API by category."""
        movies = []
        base_url = "https://api.themoviedb.org/3"

        category_endpoints = {
            'popular': '/movie/popular',
            'top_rated': '/movie/top_rated',
            'upcoming': '/movie/upcoming',
            'now_playing': '/movie/now_playing'
        }

        endpoint = category_endpoints.get(category, '/movie/popular')

        for page in range(1, pages + 1):
            try:
                params = {
                    'api_key': self.tmdb_api_key,
                    'page': page,
                    'language': 'en-US'
                }

                response = requests.get(f"{base_url}{endpoint}", params=params, timeout=10)
                response.raise_for_status()

                data = response.json()
                results = data.get('results', [])

                if not results:
                    break

                movies.extend(results)
                logger.info(f"Fetched page {page} of {category}: {len(results)} movies")

                time.sleep(0.25)  # Rate limiting

            except Exception as e:
                logger.error(f"Error fetching {category} page {page}: {str(e)}")
                break

        return movies

    def import_movie(self, movie_data: Dict) -> Optional[Movie]:
        """Import a single movie into the database."""
        try:
            title = movie_data.get('title', '').strip()
            if not title or title in self.imported_movies:
                return None

            release_date = movie_data.get('release_date', '')
            release_year = None
            if release_date:
                try:
                    release_year = int(release_date.split('-')[0])
                except:
                    pass

            omdb_data = self.get_movie_details_from_omdb(title, str(release_year) if release_year else None)

            rating = 0.0
            if omdb_data:
                try:
                    imdb_rating = omdb_data.get('imdbRating', 'N/A')
                    if imdb_rating != 'N/A':
                        rating = float(imdb_rating)
                except:
                    pass

            movie = Movie(
                title=title,
                release_year=release_year,
                plot=movie_data.get('overview', ''),
                genre=omdb_data.get('Genre', '') if omdb_data else '',
                director=omdb_data.get('Director', '') if omdb_data else '',
                rating=rating,
                poster_url=f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}" if movie_data.get('poster_path') else None,
                country=omdb_data.get('Country', '') if omdb_data else ''
            )

            self.imported_movies.add(title)
            return movie

        except Exception as e:
            logger.error(f"Error importing movie {title}: {str(e)}")
            return None

    def run_import(self, categories: List[str] = None, pages_per_category: int = 10):
        """Run the complete import process."""
        if categories is None:
            categories = ['popular', 'top_rated', 'upcoming', 'now_playing']

        logger.info(f"Starting import for categories: {categories}")

        with self.data_manager.SessionFactory() as session:
            total_imported = 0

            for category in categories:
                logger.info(f"Processing category: {category}")

                tmdb_movies = self.get_movies_from_tmdb(category, pages_per_category)
                logger.info(f"Found {len(tmdb_movies)} movies in {category}")

                for movie_data in tmdb_movies:
                    movie = self.import_movie(movie_data)
                    if movie:
                        session.add(movie)
                        total_imported += 1

                        if total_imported % 50 == 0:
                            session.commit()
                            logger.info(f"Imported {total_imported} movies so far...")

                session.commit()
                logger.info(f"Completed category {category}")
                time.sleep(1)  # Pause between categories

            logger.info(f"Import completed: {total_imported} movies imported")
            return total_imported

    def create_default_achievements(self):
        """Create default achievements in the database."""
        default_achievements = [
            {'code': 'quiz_beginner', 'name': '🎉 Quiz Beginner', 'description': 'Complete your first quiz!'},
            {'code': 'perfect_quiz', 'name': '🎯 Perfect Quiz', 'description': 'Achieve perfect score in a quiz!'},
            {'code': 'quiz_expert', 'name': '🎓 Quiz Expert', 'description': 'Complete a hard quiz with at least 8 correct answers!'},
            {'code': 'first_watchlist', 'name': '📺 First Collector', 'description': 'Add your first movie to watchlist!'},
            {'code': 'first_review', 'name': '📝 First Critic', 'description': 'Write your first review!'},
        ]

        with self.data_manager.SessionFactory() as session:
            for ach_data in default_achievements:
                existing = session.query(Achievement).filter_by(code=ach_data['code']).first()
                if not existing:
                    achievement = Achievement(
                        code=ach_data['code'],
                        name=ach_data['name'],
                        description=ach_data['description']
                    )
                    session.add(achievement)

            session.commit()
            logger.info("Default achievements created")


def main():
    """Main function to run the database reset and import."""
    print("🎬 MovieProjekt Database Reset and Import")
    print("=" * 50)

    reset_choice = input("Reset database? (y/n) [y]: ").strip().lower()
    if reset_choice != 'n':
        keep_users = input("Keep user data? (y/n) [y]: ").strip().lower() != 'n'

        importer = DatabaseResetAndImport()

        if importer.reset_database(keep_users):
            print("✅ Database reset completed")

            import_choice = input("Import new movies? (y/n) [y]: ").strip().lower()
            if import_choice != 'n':
                pages = int(input("Pages per category [10]: ").strip() or "10")
                imported_count = importer.run_import(pages_per_category=pages)
                print(f"✅ Imported {imported_count} movies")

                importer.create_default_achievements()
                print("✅ Default achievements created")
        else:
            print("❌ Database reset failed")
    else:
        print("Database reset skipped")


if __name__ == "__main__":
    main()
