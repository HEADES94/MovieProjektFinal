"""
data_manager_interface.py - Abstraktes Interface für Datenmanager in MovieProjekt
"""
from abc import ABC, abstractmethod
from typing import Any

class DataManagerInterface(ABC):
    """
    Abstraktes Interface für Datenmanager (User/Movie-Operationen).
    """
    @abstractmethod
    def users(self) -> Any:
        """Gibt alle User zurück."""
        pass

    @abstractmethod
    def users(self, user: Any) -> None:
        """Fügt einen User hinzu."""
        pass

    @abstractmethod
    def get_user_movies(self, user_id: int) -> Any:
        """Gibt alle Filme eines Users zurück."""
        pass

    @abstractmethod
    def set_user_movies(self, user_id: int, movie_id: int, user_rating: float) -> Any:
        """Fügt einen Film zur User-Liste hinzu."""
        pass

