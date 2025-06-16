"""
sqlite_data_manager.py - SQLite-Implementierung des DataManager-Interfaces
"""
from contextlib import contextmanager
from typing import List, Optional, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .data_manager_interface import DataManagerInterface
from data_models import Base, User, Movie, UserMovie, Achievement
from movie_api import OMDBClient

class SQliteDataManager(DataManagerInterface):
    """SQLite-Implementierung des DataManager-Interfaces."""

    def __init__(self, db_url: str):
        """Initialisiere die Datenbankverbindung."""
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionFactory = sessionmaker(bind=self.engine)
        self.omdb_client = OMDBClient()
        self._init_achievements()

    @contextmanager
    def get_session(self):
        """Context Manager für Datenbank-Sessions."""
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    @property
    def users(self) -> List[User]:
        """Property für alle Benutzer."""
        with self.get_session() as session:
            return session.query(User).all()

    @property
    def movies(self) -> List[Movie]:
        """Property für alle Filme."""
        with self.get_session() as session:
            return session.query(Movie).all()

    def get_user(self, user_id: int) -> Optional[User]:
        """Hole einen Benutzer anhand seiner ID."""
        with self.get_session() as session:
            return session.query(User).get(user_id)

    def get_users(self) -> List[User]:
        """Hole alle Benutzer."""
        with self.get_session() as session:
            return session.query(User).all()

    def get_movie(self, movie_id: int) -> Optional[Movie]:
        """Hole einen Film anhand seiner ID."""
        with self.get_session() as session:
            return session.query(Movie).get(movie_id)

    def get_movies(self) -> List[Movie]:
        """Hole alle Filme."""
        with self.get_session() as session:
            return session.query(Movie).all()

    def get_user_movies(self, user_id: int) -> List[Dict]:
        """Hole alle Filme eines Benutzers mit Bewertungen."""
        with self.get_session() as session:
            user_movies = session.query(UserMovie).filter_by(user_id=user_id).all()
            result = []
            for um in user_movies:
                movie = session.query(Movie).get(um.movie_id)
                if movie:
                    result.append({
                        "id": movie.id,
                        "name": movie.title,
                        "director": movie.director,
                        "year": movie.release_year,
                        "poster": movie.poster_url,
                        "rating": movie.rating,
                        "genre": movie.genre,
                        "country": movie.country,
                        "plot": movie.plot,
                        "user_rating": um.user_rating,
                        "user_comment": um.user_comment
                    })
            return result

    def get_user_movie(self, user_id: int, movie_id: int) -> Optional[Dict]:
        """Hole einen spezifischen Film eines Benutzers mit Bewertung."""
        with self.get_session() as session:
            user_movie = session.query(UserMovie).filter_by(
                user_id=user_id, movie_id=movie_id).first()
            if not user_movie:
                return None

            movie = session.query(Movie).get(movie_id)
            if not movie:
                return None

            return {
                "id": movie.id,
                "name": movie.title,
                "director": movie.director,
                "year": movie.release_year,
                "poster": movie.poster_url,
                "rating": movie.rating,
                "genre": movie.genre,
                "country": movie.country,
                "plot": movie.plot,
                "user_rating": user_movie.user_rating,
                "user_comment": user_movie.user_comment
            }

    def set_movie(self, title: str) -> Optional[Movie]:
        """
        Füge einen neuen Film hinzu oder aktualisiere einen bestehenden.
        Holt die Filmdaten von der OMDB API.
        """
        # Prüfe zuerst, ob der Film bereits existiert
        existing_movie = self.get_movie_by_title(title)
        if existing_movie:
            print(f"Film bereits vorhanden: {title}")
            return existing_movie

        # Hole Filmdaten von OMDB
        movie_data = self.omdb_client.get_movie(title)
        if not movie_data:
            print(f"Keine OMDB-Daten gefunden für: {title}")
            return None

        try:
            with self.get_session() as session:
                movie = Movie(
                    title=movie_data["name"],
                    director=movie_data["director"],
                    release_year=int(movie_data["year"][:4]) if movie_data["year"] else None,
                    genre=movie_data["genre"],
                    poster_url=movie_data["poster"],
                    rating=float(movie_data["rating"]) if movie_data["rating"] != "N/A" else None,
                    country=movie_data["country"],
                    plot=movie_data["plot"],
                    description=movie_data["plot"]
                )
                session.add(movie)
                session.commit()
                print(f"Film hinzugefügt: {movie.title}")
                return movie
        except Exception as e:
            print(f"Fehler beim Hinzufügen von {title}: {str(e)}")
            return None

    def set_user_movies(self, user_id: int, movie_id: int) -> bool:
        """Füge einen Film zur Liste eines Benutzers hinzu."""
        with self.get_session() as session:
            existing = session.query(UserMovie).filter_by(
                user_id=user_id, movie_id=movie_id).first()
            if existing:
                return False

            user_movie = UserMovie(user_id=user_id, movie_id=movie_id)
            session.add(user_movie)
            session.commit()
            return True

    def update_user_movie(self, user_id: int, movie_id: int, update_data: Dict) -> bool:
        """Aktualisiere die Bewertung eines Films für einen Benutzer."""
        with self.get_session() as session:
            user_movie = session.query(UserMovie).filter_by(
                user_id=user_id, movie_id=movie_id).first()
            if not user_movie:
                return False

            for key, value in update_data.items():
                setattr(user_movie, key, value)
            session.commit()
            return True

    def delete_movie(self, movie_id: int) -> bool:
        """Lösche einen Film und alle zugehörigen Bewertungen."""
        with self.get_session() as session:
            movie = session.query(Movie).get(movie_id)
            if not movie:
                return False

            session.query(UserMovie).filter_by(movie_id=movie_id).delete()
            session.delete(movie)
            session.commit()
            return True

    def delete_user_movie(self, user_id: int, movie_id: int) -> bool:
        """Lösche einen Film aus der Liste eines Benutzers."""
        with self.get_session() as session:
            user_movie = session.query(UserMovie).filter_by(
                user_id=user_id, movie_id=movie_id).first()
            if not user_movie:
                return False

            session.delete(user_movie)
            session.commit()
            return True

    def get_movie_by_title(self, title: str) -> Optional[Movie]:
        """Hole einen Film anhand seines Titels."""
        with self.get_session() as session:
            return session.query(Movie).filter(Movie.title.ilike(f"%{title}%")).first()

    def _init_achievements(self):
        """Initialisiert die Standard-Achievements."""
        achievements = [
            {
                "title": "🎯 Perfect Quiz",
                "description": "Erreiche die perfekte Punktzahl in einem Quiz!",
                "code": "perfect_quiz"
            },
            {
                "title": "🏆 First Highscore",
                "description": "Erreiche deinen ersten Highscore!",
                "code": "first_highscore"
            },
            {
                "title": "👑 Quiz Master",
                "description": "Erreiche in 5 verschiedenen Quizzen mindestens 400 Punkte!",
                "code": "quiz_master"
            },
            {
                "title": "🎓 Quiz Profi",
                "description": "Schließe ein schweres Quiz mit mindestens 1000 Punkten ab!",
                "code": "quiz_expert"
            },
            {
                "title": "📚 Wissensdurst",
                "description": "Beantworte 100 Fragen korrekt!",
                "code": "knowledge_seeker"
            },
            {
                "title": "🎬 Film Enthusiast",
                "description": "Schließe Quizze zu 10 verschiedenen Filmen ab!",
                "code": "movie_enthusiast"
            },
            {
                "title": "🌟 Perfektionist",
                "description": "Erreiche 3 perfekte Quizze in Folge!",
                "code": "perfectionist"
            },
            {
                "title": "🔥 Streak Master",
                "description": "Beantworte 20 Fragen in Folge richtig!",
                "code": "streak_master"
            }
        ]
        with self.SessionFactory() as session:
            for achievement_data in achievements:
                existing = session.query(Achievement).filter_by(
                    code=achievement_data["code"]).first()
                if not existing:
                    achievement = Achievement(**achievement_data)
                    session.add(achievement)
            session.commit()
