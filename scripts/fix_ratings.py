#!/usr/bin/env python3
"""
Rating-Bereinigung: Korrigiert unrealistische und problematische Ratings
"""

import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datamanager.sqlite_data_manager import SQliteDataManager
from data_models import Movie

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_ratings():
    """Bereinigt unrealistische Ratings und entfernt problematische Filme."""
    data_manager = SQliteDataManager("sqlite:///movie_app.db")

    # Problematische Begriffe
    forbidden_keywords = ['succubus', 'kill shot', 'playboy', 'nude', 'erotic', 'xxx', 'adult']

    # IMDB Top-Ratings für Korrektur
    imdb_ratings = {
        "The Shawshank Redemption": 9.3,
        "The Godfather": 9.2,
        "The Dark Knight": 9.0,
        "The Godfather Part II": 9.0,
        "12 Angry Men": 9.0,
        "Schindler's List": 8.9,
        "Pulp Fiction": 8.9
    }

    with data_manager.SessionFactory() as session:
        # 1. Entferne problematische Filme
        logger.info("Entferne problematische Filme...")
        deleted_count = 0

        for keyword in forbidden_keywords:
            problematic_movies = session.query(Movie).filter(
                Movie.title.ilike(f'%{keyword}%')
            ).all()

            for movie in problematic_movies:
                logger.info(f"Lösche problematischen Film: {movie.title}")
                session.delete(movie)
                deleted_count += 1

        # 2. Korrigiere unrealistische Ratings (über 10 oder unter 0)
        logger.info("Korrigiere unrealistische Ratings...")
        corrected_count = 0

        unrealistic_movies = session.query(Movie).filter(
            (Movie.rating > 10) | (Movie.rating < 0)
        ).all()

        for movie in unrealistic_movies:
            old_rating = movie.rating

            # Prüfe IMDB-Klassiker zuerst
            corrected = False
            for imdb_title, imdb_rating in imdb_ratings.items():
                if imdb_title.lower() in movie.title.lower():
                    movie.rating = imdb_rating
                    corrected = True
                    break

            if not corrected:
                # Für andere Filme: setze vernünftiges Rating
                if movie.rating > 1000000:  # Extrem hohe Werte
                    movie.rating = 7.5
                elif movie.rating > 100:
                    movie.rating = 8.0
                elif movie.rating > 10:
                    movie.rating = movie.rating / 10  # Teile durch 10
                elif movie.rating < 0:
                    movie.rating = 6.0

            logger.info(f"Korrigiert: {movie.title} ({old_rating} -> {movie.rating})")
            corrected_count += 1

        # 3. Korrigiere IMDB-Klassiker
        logger.info("Korrigiere IMDB-Klassiker...")
        imdb_corrected = 0

        for imdb_title, imdb_rating in imdb_ratings.items():
            movies = session.query(Movie).filter(
                Movie.title.ilike(f'%{imdb_title}%')
            ).all()

            for movie in movies:
                if abs(movie.rating - imdb_rating) > 0.1:  # Nur wenn unterschiedlich
                    old_rating = movie.rating
                    movie.rating = imdb_rating
                    logger.info(f"IMDB-Korrektur: {movie.title} ({old_rating} -> {imdb_rating})")
                    imdb_corrected += 1

        session.commit()

        # Final Stats
        final_count = session.query(Movie).count()
        top_movies = session.query(Movie).order_by(Movie.rating.desc()).limit(10).all()

        logger.info(f"\n=== BEREINIGUNG ABGESCHLOSSEN ===")
        logger.info(f"Gelöschte problematische Filme: {deleted_count}")
        logger.info(f"Korrigierte unrealistische Ratings: {corrected_count}")
        logger.info(f"IMDB-Korrekturen: {imdb_corrected}")
        logger.info(f"Finale Anzahl Filme: {final_count}")

        logger.info(f"\nTop 10 nach Bereinigung:")
        for i, movie in enumerate(top_movies, 1):
            logger.info(f"{i:2d}. {movie.title} ({movie.release_year}): {movie.rating}/10")

if __name__ == "__main__":
    clean_ratings()
