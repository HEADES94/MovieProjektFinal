"""
data_manager_interface.py - Interface für verschiedene Datenmanager-Implementierungen
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from data_models import User, Movie, UserMovie

class DataManagerInterface(ABC):
    """Abstract Base Class für Datenmanager."""

    @abstractmethod
    def get_user(self, user_id: int) -> Optional[User]:
        """Hole einen Benutzer anhand seiner ID."""
        pass

    @abstractmethod
    def get_users(self) -> List[User]:
        """Hole alle Benutzer."""
        pass

    @property
    @abstractmethod
    def users(self) -> List[User]:
        """Property für alle Benutzer."""
        pass

    @property
    @abstractmethod
    def movies(self) -> List[Movie]:
        """Property für alle Filme."""
        pass

    @abstractmethod
    def get_movie(self, movie_id: int) -> Optional[Movie]:
        """Hole einen Film anhand seiner ID."""
        pass

    @abstractmethod
    def get_movies(self) -> List[Movie]:
        """Hole alle Filme."""
        pass

    @abstractmethod
    def get_user_movies(self, user_id: int) -> List[Dict]:
        """Hole alle Filme eines Benutzers mit Bewertungen."""
        pass

    @abstractmethod
    def get_user_movie(self, user_id: int, movie_id: int) -> Optional[Dict]:
        """Hole einen spezifischen Film eines Benutzers mit Bewertung."""
        pass

    @abstractmethod
    def set_movie(self, title: str) -> Optional[Movie]:
        """Füge einen neuen Film hinzu."""
        pass

    @abstractmethod
    def set_user_movies(self, user_id: int, movie_id: int) -> bool:
        """Füge einen Film zur Liste eines Benutzers hinzu."""
        pass

    @abstractmethod
    def update_user_movie(self, user_id: int, movie_id: int, update_data: Dict) -> bool:
        """Aktualisiere die Bewertung eines Films für einen Benutzer."""
        pass

    @abstractmethod
    def delete_movie(self, movie_id: int) -> bool:
        """Lösche einen Film."""
        pass

    @abstractmethod
    def delete_user_movie(self, user_id: int, movie_id: int) -> bool:
        """Lösche einen Film aus der Liste eines Benutzers."""
        pass
