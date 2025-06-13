"""
watchlist_service.py - Service für die Watchlist-Funktionalität
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from data_models import WatchlistItem, Movie, User
from services.achievement_service import AchievementService

class WatchlistService:
    """Service zur Verwaltung der Benutzer-Watchlists."""

    def __init__(self, session: Session):
        self.session = session
        self.achievement_service = AchievementService(session)

    def add_to_watchlist(self, user_id: int, movie_id: int) -> Optional[WatchlistItem]:
        """
        Fügt einen Film zur Watchlist eines Benutzers hinzu.
        Prüft auch auf mögliche Achievements.
        """
        # Prüfe ob der Film bereits in der Watchlist ist
        existing = self.session.query(WatchlistItem).filter_by(
            user_id=user_id,
            movie_id=movie_id
        ).first()

        if existing:
            return None

        watchlist_item = WatchlistItem(
            user_id=user_id,
            movie_id=movie_id,
            added_at=datetime.utcnow()
        )

        self.session.add(watchlist_item)
        self.session.commit()

        # Prüfe auf neue Achievements
        self.achievement_service.check_achievements(user_id)

        return watchlist_item

    def remove_from_watchlist(self, user_id: int, movie_id: int) -> bool:
        """Entfernt einen Film aus der Watchlist eines Benutzers."""
        watchlist_item = self.session.query(WatchlistItem).filter_by(
            user_id=user_id,
            movie_id=movie_id
        ).first()

        if not watchlist_item:
            return False

        self.session.delete(watchlist_item)
        self.session.commit()
        return True

    def get_watchlist(self, user_id: int) -> List[dict]:
        """
        Holt die Watchlist eines Benutzers mit allen Filminformationen.
        Returns:
            List[dict]: Liste von Dictionaries mit Film- und Watchlist-Informationen
        """
        watchlist_items = self.session.query(WatchlistItem)\
            .filter_by(user_id=user_id)\
            .order_by(WatchlistItem.added_at.desc())\
            .all()

        result = []
        for item in watchlist_items:
            movie = self.session.query(Movie).get(item.movie_id)
            if movie:
                result.append({
                    "id": item.id,
                    "movie": movie,
                    "added_at": item.added_at
                })

        return result

    def is_in_watchlist(self, user_id: int, movie_id: int) -> bool:
        """Prüft ob ein Film bereits in der Watchlist des Benutzers ist."""
        return self.session.query(WatchlistItem).filter_by(
            user_id=user_id,
            movie_id=movie_id
        ).first() is not None

    def get_watchlist_count(self, user_id: int) -> int:
        """Gibt die Anzahl der Filme in der Watchlist zurück."""
        return self.session.query(WatchlistItem).filter_by(user_id=user_id).count()
