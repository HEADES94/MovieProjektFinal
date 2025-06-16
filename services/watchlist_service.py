"""
watchlist_service.py - Service für die Watchlist-Funktionalität
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from data_models import WatchlistItem, Movie, User, UserAchievement
from services.achievement_service import AchievementService
from datamanager.data_manager_interface import DataManagerInterface

class WatchlistService:
    """Service zur Verwaltung der Benutzer-Watchlists."""

    def __init__(self, data_manager: DataManagerInterface):
        self.data_manager = data_manager

    def add_to_watchlist(self, user_id: int, movie_id: int) -> Optional[WatchlistItem]:
        """
        Fügt einen Film zur Watchlist eines Benutzers hinzu.
        Prüft auch auf mögliche Achievements.
        Returns:
            WatchlistItem wenn erfolgreich hinzugefügt
            None wenn Film bereits in der Watchlist
        Raises:
            Exception wenn der Film nicht existiert
        """
        try:
            with self.data_manager.SessionFactory() as session:
                # Prüfe ob der Film bereits in der Watchlist ist
                existing = session.query(WatchlistItem).filter_by(
                    user_id=user_id,
                    movie_id=movie_id
                ).first()

                if existing:
                    return existing  # Film ist bereits in der Watchlist

                # Prüfe ob der Film existiert
                movie = session.query(Movie).get(movie_id)
                if not movie:
                    raise Exception(f"Film mit ID {movie_id} existiert nicht.")

                watchlist_item = WatchlistItem(
                    user_id=user_id,
                    movie_id=movie_id,
                    added_at=datetime.utcnow()
                )

                session.add(watchlist_item)
                session.commit()

                # Achievement prüfen und ggf. vergeben
                achievement_service = AchievementService(self.data_manager)
                with self.data_manager.SessionFactory() as session2:
                    count = session2.query(WatchlistItem).filter_by(user_id=user_id).count()
                    # Achievement vergeben, wenn mindestens 10 Einträge und noch nicht erhalten
                    user_ach = session2.query(UserAchievement).join(Achievement).filter(
                        UserAchievement.user_id == user_id,
                        Achievement.code == 'watchlist_add_10'
                    ).first()
                    if count >= 10 and not user_ach:
                        achievement_service._grant_achievement(user_id, 'watchlist_add_10', session2)
                    session2.commit()

                return watchlist_item

        except Exception as e:
            raise Exception(f"Fehler beim Hinzufügen zur Watchlist: {str(e)}")

    def get_watchlist(self, user_id: int) -> List[WatchlistItem]:
        """Holt alle Watchlist-Einträge eines Benutzers."""
        try:
            with self.data_manager.SessionFactory() as session:
                items = session.query(WatchlistItem).filter_by(user_id=user_id).all()
                # Lade die zugehörigen Filme explizit
                for item in items:
                    item.movie = session.query(Movie).get(item.movie_id)
                return items
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Watchlist: {str(e)}")

    def remove_from_watchlist(self, user_id: int, movie_id: int) -> bool:
        """Entfernt einen Film aus der Watchlist eines Benutzers."""
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
            raise Exception(f"Fehler beim Entfernen von der Watchlist: {str(e)}")

    def is_in_watchlist(self, user_id: int, movie_id: int) -> bool:
        """Prüft ob ein Film bereits in der Watchlist des Benutzers ist."""
        try:
            with self.data_manager.SessionFactory() as session:
                return session.query(WatchlistItem).filter_by(
                    user_id=user_id,
                    movie_id=movie_id
                ).first() is not None
        except Exception as e:
            raise Exception(f"Fehler beim Prüfen der Watchlist: {str(e)}")

    def get_watchlist_count(self, user_id: int) -> int:
        """Gibt die Anzahl der Filme in der Watchlist zurück."""
        try:
            with self.data_manager.SessionFactory() as session:
                return session.query(WatchlistItem).filter_by(user_id=user_id).count()
        except Exception as e:
            raise Exception(f"Fehler beim Zählen der Watchlist-Einträge: {str(e)}")
