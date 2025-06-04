"""
sqlite_data_manager.py - Datenmanager für SQLite-Operationen in MovieProjekt
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import List, Dict, Any, Type, Optional

from data_models import Base, User, Movie, UserMovie
from movie_api import OMDBClient
from datamanager.data_manager_interface import DataManagerInterface

# Define the database connection string.
TEST_DB_URL = "sqlite:///:memory:"

class SQliteDataManager(DataManagerInterface):
    """
    Datenmanager für alle Datenbankoperationen (CRUD) mit SQLite.
    """
    def __init__(self, db_url: str):
        """
        Initialisiere den Datenmanager mit einer Datenbank-URL.
        """
        self.engine = create_engine(db_url)
        self.SessionFactory = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_db(self):
        """
        Kontextmanager für eine Datenbank-Session.
        """
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise ConnectionError("Database connection error!")
        finally:
            session.close()

    @property
    def users(self) -> List[Type[User]]:
        """
        Gibt alle User-Objekte zurück.
        Returns:
            list: Liste von User-Objekten
        """
        with self.SessionFactory() as session:
            users = session.query(User).all()
            return users

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Hole einen User anhand der ID.
        Args:
            user_id (int): Die User-ID.
        Returns:
            User oder None
        """
        with self.SessionFactory() as session:
            user = session.query(User).filter_by(id=user_id).first()
            return user

    def add_user(self, user: User) -> None:
        """
        Füge einen User zur Datenbank hinzu.
        Args:
            user (User): Das User-Objekt.
        """
        with self.SessionFactory() as session:
            session.add(user)
            session.commit()

    @property
    def movies(self) -> List[Type[Movie]]:
        """
        Gibt alle Movie-Objekte zurück.
        Returns:
            list: Liste von Movie-Objekten
        """
        with self.SessionFactory() as session:
            return session.query(Movie).all()

    def set_user_movies(self, user_id: int, movie_id: int, user_rating: float = 0.0) -> Optional[str]:
        """
        Füge einen Film zur User-Liste hinzu oder aktualisiere die Bewertung.
        Args:
            user_id (int): Die User-ID.
            movie_id (int): Die Movie-ID.
            user_rating (float): Bewertung des Users.
        Returns:
            Optional[str]: Fehlermeldung oder None bei Erfolg.
        """
        with self.SessionFactory() as session:
            user = session.query(User).filter_by(id=user_id).first()
            movie = session.query(Movie).filter_by(id=movie_id).first()
            if user and movie:
                existing_associations = session.query(UserMovie).filter_by(
                    user_id=user_id, movie_id=movie_id
                ).first()
                if existing_associations:
                    # Update bestehende Assoziation
                    session.query(UserMovie).filter_by(user_id=user_id, movie_id=movie_id).update(
                        {"user_rating": user_rating}
                    )
                else:
                    # Neue Assoziation anlegen
                    association = UserMovie(user_id=user_id, movie_id=movie_id,
                                            user_rating=user_rating)
                    session.add(association)
                session.commit()
            elif movie is None:
                return "Failed to add movie, check ID and try again!"
            else:
                return "User not found."

    def get_user_movies(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Hole alle Filme eines Users mit Bewertung und Kommentar.
        Args:
            user_id (int): Die User-ID.
        Returns:
            list: Liste von Dictionaries mit Filmdetails und User-Bewertung
        """
        with self.SessionFactory() as session:
            user_movies = session.query(UserMovie).filter_by(user_id=user_id).all()
            if user_movies:
                movies_with_ratings = []
                for association in user_movies:
                    movie = session.query(Movie).filter_by(id=association.movie_id).first()
                    if movie:
                        movies_with_ratings.append({
                            "id": movie.id,
                            "name": movie.name,
                            "director": movie.director,
                            "year": movie.year,
                            "poster": movie.poster,
                            "genre": movie.genre,
                            "country": movie.country,
                            "plot": movie.plot,
                            "rating": movie.rating,
                            "user_rating": association.user_rating,
                            "user_comment": association.user_comment if association.user_comment else None
                        })
                return movies_with_ratings
            return []

    def get_user_movie(self, user_id: int, movie_id: int) -> Dict[str, Any]:
        """
        Hole die UserMovie-Relation für einen bestimmten User und Film.
        Args:
            user_id (int): Die User-ID.
            movie_id (int): Die Movie-ID.
        Returns:
            dict: Details zum Film und zur Bewertung/Kommentar des Users
        """
        with self.SessionFactory() as session:
            user_movie = session.query(UserMovie).filter_by(user_id=user_id, movie_id=movie_id).first()
            if user_movie:
                movie = session.query(Movie).filter_by(id=movie_id).first()
                return {
                    "id": movie.id,
                    "name": movie.name,
                    "director": movie.director,
                    "year": movie.year,
                    "poster": movie.poster,
                    "genre": movie.genre,
                    "country": movie.country,
                    "plot": movie.plot,
                    "rating": movie.rating,
                    "user_rating": user_movie.user_rating,
                    "user_comment": user_movie.user_comment if user_movie.user_comment else None
                }
            return {}

    def set_movie(self, movie_title: str) -> Optional[Movie]:
        """
        Füge einen neuen Film zur Datenbank hinzu (oder hole ihn, falls schon vorhanden).
        Args:
            movie_title (str): Titel des Films.
        Returns:
            Movie oder None
        """
        with self.SessionFactory() as session:
            movie = session.query(Movie).filter_by(name=movie_title).first()
            if movie:
                return movie
            new_movie = OMDBClient().get_movie(title=movie_title)
            if new_movie is None:
                raise ValueError("Movie not found")
            movie = Movie(**new_movie)
            session.add(movie)
            session.commit()
        return movie

    def update_user_movie(self, user_id: int, movie_id: int, update_data: dict) -> Optional[dict]:
        """
        Aktualisiere Bewertung/Kommentar eines Users zu einem Film.
        Args:
            user_id (int): Die User-ID.
            movie_id (int): Die Movie-ID.
            update_data (dict): Felder zum Aktualisieren.
        Returns:
            dict: Die aktualisierten Filmdaten
        """
        with self.SessionFactory() as session:
            movie = session.query(Movie).filter_by(id=movie_id).first()
            if movie:
                session.query(UserMovie).filter_by(user_id=user_id,
                                                   movie_id=movie_id).update(update_data)
                session.commit()
                return {
                    "id": movie.id,
                    "name": movie.name,
                    "director": movie.director,
                    "year": movie.year,
                    "poster": movie.poster,
                    "genre": movie.genre,
                    "country": movie.country,
                    "plot": movie.plot,
                    "rating": movie.rating,
                    "user_rating": update_data.get("user_rating", 0.0),
                    "user_comment": update_data.get("user_comment", None)
                }
            return None

    def delete_movie(self, movie_id: int) -> bool:
        """
        Lösche einen Film aus der Datenbank (inkl. aller User-Relationen).
        Args:
            movie_id (int): Die Movie-ID.
        Returns:
            bool: True bei Erfolg, sonst False
        """
        with self.SessionFactory() as session:
            movie = session.query(Movie).filter_by(id=movie_id).first()
            if movie:
                session.flush()
                session.query(UserMovie).filter_by(movie_id=movie_id).delete()
                session.query(Movie).filter_by(id=movie_id).delete()
                session.commit()
                return True
            return False

    def delete_user(self, user_id: int) -> bool:
        """
        Lösche einen User aus der Datenbank (inkl. aller User-Relationen).
        Args:
            user_id (int): Die User-ID.
        Returns:
            bool: True bei Erfolg, sonst False
        """
        with self.SessionFactory() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                session.flush()
                session.query(UserMovie).filter_by(user_id=user_id).delete()
                session.query(User).filter_by(id=user_id).delete()
                session.commit()
                return True
            return False

    def delete_user_movie(self, user_id: int, movie_id: int) -> bool:
        """
        Lösche die UserMovie-Relation für einen bestimmten User und Film.
        Args:
            user_id (int): Die User-ID.
            movie_id (int): Die Movie-ID.
        Returns:
            bool: True bei Erfolg, sonst False
        """
        with self.SessionFactory() as session:
            association = session.query(UserMovie).filter_by(user_id=user_id, movie_id=movie_id).first()
            if association:
                session.delete(association)
                session.commit()
                return True
            return False

    def get_movie(self, movie_id: int) -> Optional[Movie]:
        """
        Hole einen Film anhand der ID.
        Args:
            movie_id (int): Die Movie-ID.
        Returns:
            Movie oder None
        """
        with self.SessionFactory() as session:
            movie = session.query(Movie).filter_by(id=movie_id).first()
            return movie

def main():
    data_manager = SQliteDataManager("sqlite:///movie_app.db")

    with data_manager.SessionFactory() as session:
        # Create some users
        user1 = User(name="Joshi")
        user2 = User(name="Icke")
        data_manager.add_user(user1)
        data_manager.add_user(user2)
        session.add_all([user1, user2])
        session.commit()

        # Create some movies
        movie1 = data_manager.set_movie("The Matrix")
        movie2 = data_manager.set_movie("Interstellar")

        # Associate movies with users and assign ratings
        print(f"user1:{user1}, movie1:{movie1}")
        data_manager.set_user_movies(user1.id, movie1.id)
        print(data_manager.get_user_movies(user1.id))
        data_manager.set_user_movies(user1.id, movie2.id, 8.5)
        data_manager.set_user_movies(user2.id, movie2.id, 9.2)

        # Get and print user movies (use a new session for querying)

        print("Alice's movies:", data_manager.get_user_movies(user1.id))
        print("Bob's movies:", data_manager.get_user_movies(user2.id))

        # Get and print all movies
        print("All movies:", session.query(Movie).all())

        # Example of updating a movie (use a new session)
        updated_movie = data_manager.update_user_movie(user1.id, movie1.id,
                                                      {"user_rating":
                                                          7.2})
        print("Updated movie:", updated_movie)

        # Example of deleting a movie (use a new session)
        deleted = data_manager.delete_movie(movie1.id)
        print("Deleted movie1:", deleted)

        print("All movies after deletion:", session.query(Movie).all())


if __name__ == "__main__":
    main()

