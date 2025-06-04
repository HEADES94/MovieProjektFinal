"""
data_models.py - SQLAlchemy Datenmodelle für MovieProjekt
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

# Datenbankverbindung (für Tests: In-Memory)
TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Basisklasse für deklarative Modelle
Base = declarative_base()

class UserMovie(Base):
    """
    Assoziationstabelle für User und Movie mit zusätzlicher Bewertung und Kommentar.
    """
    __tablename__ = 'user_movies'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('users.id'))
    movie_id = Column('movie_id', Integer, ForeignKey('movies.id'))
    user_rating = Column('user_rating', Float, default=0.0)
    user_comment = Column('user_comment', String)
    users = relationship("User", back_populates="user_movies", overlaps="users,movies")
    movies = relationship("Movie", back_populates="user_movies", overlaps="users,movies")

    def __repr__(self) -> str:
        return (f"<UserMovie(user_id={self.user_id}, movie_id={self.movie_id}, "
                f"user_rating={self.user_rating})>")

class User(Base):
    """
    User-Modell: Ein Benutzer kann mehrere Filme bewerten.
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    movies = relationship("Movie", secondary="user_movies",
                          back_populates="users", overlaps="user_movies,movies")
    user_movies = relationship("UserMovie", back_populates="users",
                               overlaps="user_movies,movies")

    def __repr__(self) -> str:
        return f"<User(name='{self.name}', id={self.id if self.id else 'None'})>"

class Movie(Base):
    """
    Movie-Modell: Ein Film kann von mehreren Benutzern bewertet werden.
    """
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    director = Column(String)
    year = Column(Integer)
    poster = Column(String)
    rating = Column(Float)
    genre = Column(String)
    country = Column(String)
    plot = Column(String)
    users = relationship("User", secondary="user_movies",
                         back_populates="movies", overlaps="user_movies,users")
    user_movies = relationship("UserMovie", back_populates="movies",
                               overlaps="user_movies,users")

    def __repr__(self) -> str:
        return f"<Movie(name={self.name}, id={self.id if self.id else 'None'})>"

if __name__ == "__main__":
    # Erstelle die Tabellen, falls das Skript direkt ausgeführt wird.
    Base.metadata.create_all(engine)
    print("Tables created!")