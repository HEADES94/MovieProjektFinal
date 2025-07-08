"""Service for watchlist functionality."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from data_models import WatchlistItem, Movie, User, UserAchievement, Achievement
from services.achievement_service import AchievementService
from datamanager.data_manager_interface import DataManagerInterface


class WatchlistService:
    """Service for managing user watchlists."""

    def __init__(self, data_manager: DataManagerInterface):
        self.data_manager = data_manager

    def add_to_watchlist(self, user_id: int, movie_id: int) -> Optional[WatchlistItem]:
        """
        Add a movie to a user's watchlist.

        Returns:
            WatchlistItem if successfully added
            None if movie is already in watchlist
        Raises:
            Exception if movie doesn't exist
        """
        try:
            with self.data_manager.SessionFactory() as session:
                # Check if the movie is already in the watchlist
                existing = session.query(WatchlistItem).filter_by(
                    user_id=user_id,
                    movie_id=movie_id
                ).first()

                if existing:
                    return existing  # Movie is already in the watchlist

                # Check if the movie exists
                movie = session.query(Movie).get(movie_id)
                if not movie:
                    raise Exception(f"Movie with ID {movie_id} does not exist.")

                watchlist_item = WatchlistItem(
                    user_id=user_id,
                    movie_id=movie_id,
                    added_at=datetime.utcnow()
                )

                session.add(watchlist_item)
                session.commit()

                return watchlist_item

        except Exception as e:
            raise Exception(f"Error adding to watchlist: {str(e)}")

    def get_watchlist(self, user_id: int) -> List[WatchlistItem]:
        """Get all watchlist entries for a user."""
        try:
            with self.data_manager.SessionFactory() as session:
                items = session.query(WatchlistItem).filter_by(user_id=user_id).all()
                # Explicitly load the associated movies
                for item in items:
                    item.movie = session.query(Movie).get(item.movie_id)
                return items
        except Exception as e:
            raise Exception(f"Error loading watchlist: {str(e)}")

    def remove_from_watchlist(self, user_id: int, movie_id: int) -> bool:
        """Remove a movie from a user's watchlist."""
        try:
            with self.data_manager.SessionFactory() as session:
                item = session.query(WatchlistItem).filter_by(
                    user_id=user_id,
                    movie_id=movie_id
                ).first()

                if item:
                    session.delete(item)
                    session.commit()
                    return True
                return False
        except Exception as e:
            raise Exception(f"Error removing from watchlist: {str(e)}")

    def is_in_watchlist(self, user_id: int, movie_id: int) -> bool:
        """Check if a movie is already in the user's watchlist."""
        try:
            with self.data_manager.SessionFactory() as session:
                return session.query(WatchlistItem).filter_by(
                    user_id=user_id,
                    movie_id=movie_id
                ).first() is not None
        except Exception as e:
            raise Exception(f"Error checking watchlist: {str(e)}")

    def get_watchlist_count(self, user_id: int) -> int:
        """Get the number of movies in the watchlist."""
        try:
            with self.data_manager.SessionFactory() as session:
                return session.query(WatchlistItem).filter_by(user_id=user_id).count()
        except Exception as e:
            raise Exception(f"Error getting watchlist count: {str(e)}")

    def clear_watchlist(self, user_id: int) -> bool:
        """Clear all movies from a user's watchlist."""
        try:
            with self.data_manager.SessionFactory() as session:
                items = session.query(WatchlistItem).filter_by(user_id=user_id).all()
                for item in items:
                    session.delete(item)
                session.commit()
                return True
        except Exception as e:
            raise Exception(f"Error clearing watchlist: {str(e)}")

    def get_popular_watchlist_movies(self, limit: int = 10) -> List[dict]:
        """Get the most popular movies in watchlists."""
        try:
            with self.data_manager.SessionFactory() as session:
                from sqlalchemy import func

                popular_movies = session.query(
                    Movie,
                    func.count(WatchlistItem.movie_id).label('watchlist_count')
                ).join(
                    WatchlistItem, Movie.id == WatchlistItem.movie_id
                ).group_by(
                    Movie.id
                ).order_by(
                    func.count(WatchlistItem.movie_id).desc()
                ).limit(limit).all()

                return [{
                    'movie': movie,
                    'watchlist_count': count
                } for movie, count in popular_movies]

        except Exception as e:
            raise Exception(f"Error getting popular watchlist movies: {str(e)}")

    def get_recent_additions(self, user_id: int, limit: int = 5) -> List[WatchlistItem]:
        """Get the most recently added movies to a user's watchlist."""
        try:
            with self.data_manager.SessionFactory() as session:
                items = session.query(WatchlistItem).filter_by(
                    user_id=user_id
                ).order_by(
                    WatchlistItem.added_at.desc()
                ).limit(limit).all()

                for item in items:
                    item.movie = session.query(Movie).get(item.movie_id)

                return items
        except Exception as e:
            raise Exception(f"Error getting recent additions: {str(e)}")
