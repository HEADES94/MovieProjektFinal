"""
data_models.py - SQLAlchemy Datenmodelle für MovieProjekt
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from flask_login import UserMixin

# Datenbankverbindung (für Tests: In-Memory)
TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Basisklasse für deklarative Modelle
Base = declarative_base()

class Movie(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    release_year = Column(Integer)
    description = Column(Text)
    genre = Column(String(255))
    director = Column(String(255))
    rating = Column(Float)
    poster_url = Column(String(500))
    country = Column(String(255))

    # Beziehungen mit overlaps-Parameter
    movie_actors = relationship('MovieActor', back_populates='movie', overlaps="actors,movies")
    actors = relationship('Actor', secondary='movie_actors', back_populates='movies', overlaps="movie_actors")
    reviews = relationship('Review', back_populates='movie')
    quiz_questions = relationship('QuizQuestion', back_populates='movie')

    def __repr__(self) -> str:
        return f"<Movie(title={self.title}, id={self.id if self.id else 'None'})>"

class User(UserMixin, Base):
    """
    User-Modell: Ein Benutzer kann mehrere Filme bewerten.
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)  # Für Abwärtskompatibilität
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    theme = Column(String, default='system')
    email_notifications = Column(Boolean, default=True)
    favorite_movie_id = Column(Integer, ForeignKey('movies.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    favorite_movie = relationship("Movie", foreign_keys=[favorite_movie_id])
    reviews = relationship("Review", back_populates="user")
    watchlist_items = relationship("WatchlistItem", back_populates="user")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    achievements = relationship("Achievement", secondary="user_achievements", back_populates="users", overlaps="achievements")
    suggested_questions = relationship("SuggestedQuestion", back_populates="user")
    user_movies = relationship("UserMovie", back_populates="user")

    @property
    def is_active(self):
        return True

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    def __repr__(self) -> str:
        return f"<User(name='{self.name}', id={self.id if self.id else 'None'})>"

class Actor(Base):
    __tablename__ = 'actors'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    birth_year = Column(Integer)
    bio = Column(Text)

    # Beziehungen mit overlaps-Parameter
    movie_actors = relationship('MovieActor', back_populates='actor', overlaps="actors,movies")
    movies = relationship('Movie', secondary='movie_actors', back_populates='actors', overlaps="movie_actors")

class MovieActor(Base):
    __tablename__ = 'movie_actors'
    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=False)
    actor_id = Column(Integer, ForeignKey('actors.id'), nullable=False)
    role_name = Column(String(255))

    # Beziehungen mit overlaps-Parameter
    movie = relationship('Movie', back_populates='movie_actors', overlaps="actors,movies")
    actor = relationship('Actor', back_populates='movie_actors', overlaps="actors,movies")

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=False)
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Beziehungen
    user = relationship('User', back_populates='reviews')
    movie = relationship('Movie', back_populates='reviews')

class WatchlistItem(Base):
    __tablename__ = 'watchlist'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    added_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watchlist_items")
    movie = relationship("Movie")

class MovieRecommendation(Base):
    __tablename__ = 'movie_recommendations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    reason = Column(Text)
    score = Column(Float)
    recommended_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    movie = relationship("Movie")

class QuizQuestion(Base):
    __tablename__ = 'quiz_questions'
    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movies.id'))
    question_text = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    wrong_answer_1 = Column(Text, nullable=False)
    wrong_answer_2 = Column(Text, nullable=False)
    wrong_answer_3 = Column(Text, nullable=False)
    source = Column(String)  # 'manual' oder 'ai'
    question_usage_count = Column(Integer, default=0)
    correct_answer_rate = Column(Float, default=0.0)
    difficulty = Column(String)  # 'easy', 'medium', 'hard'

    movie = relationship("Movie", back_populates="quiz_questions")
    ai_metadata = relationship("AIQuestionMetadata", back_populates="question", uselist=False)

class AIQuestionMetadata(Base):
    __tablename__ = 'ai_question_metadata'
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('quiz_questions.id'))
    ai_model = Column(String)
    temperature = Column(Float)
    prompt = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("QuizQuestion", back_populates="ai_metadata")

class QuizAttempt(Base):
    __tablename__ = 'quiz_attempts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    score = Column(Integer)
    correct_count = Column(Integer)
    max_possible_score = Column(Integer, default=10)  # Standardmäßig 10 Punkte
    difficulty = Column(String, default='mittel')  # 'leicht', 'mittel', 'schwer'
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="quiz_attempts")
    movie = relationship("Movie")

class Highscore(Base):
    __tablename__ = 'highscores'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    best_score = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    movie = relationship("Movie")

class SuggestedQuestion(Base):
    __tablename__ = 'suggested_questions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    question_text = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    wrong_answer_1 = Column(Text, nullable=False)
    wrong_answer_2 = Column(Text, nullable=False)
    wrong_answer_3 = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='pending')  # 'pending', 'approved', 'rejected'

    user = relationship("User", back_populates="suggested_questions")
    movie = relationship("Movie")
    votes = relationship("QuestionVote", back_populates="question")

class QuestionVote(Base):
    __tablename__ = 'question_votes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    suggested_question_id = Column(Integer, ForeignKey('suggested_questions.id'))
    vote = Column(Integer)  # 1 für upvote, -1 für downvote
    voted_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    question = relationship("SuggestedQuestion", back_populates="votes")

class Achievement(Base):
    __tablename__ = 'achievements'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    code = Column(String(50), unique=True)  # Eindeutiger Code für jedes Achievement

    users = relationship("User", secondary="user_achievements", back_populates="achievements", overlaps="achievements")

class UserAchievement(Base):
    __tablename__ = 'user_achievements'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    achievement_id = Column(Integer, ForeignKey('achievements.id'))
    earned_at = Column(DateTime, default=datetime.utcnow)

class UserMovie(Base):
    """
    UserMovie-Modell: Verknüpft Benutzer mit ihren persönlichen Filminformationen
    """
    __tablename__ = 'user_movies'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    watched = Column(Boolean, default=False)
    favorite = Column(Boolean, default=False)
    personal_rating = Column(Integer)
    watch_date = Column(DateTime)
    notes = Column(Text)

    user = relationship("User", back_populates="user_movies")
    movie = relationship("Movie")

def init_db(db_url=None):
    """Initialisiert die Datenbank und erstellt alle Tabellen"""
    global engine
    if db_url:
        engine = create_engine(db_url)
    Base.metadata.create_all(engine)

def drop_db():
    """Löscht alle Tabellen"""
    Base.metadata.drop_all(engine)

if __name__ == "__main__":
    # Erstelle die Tabellen, falls das Skript direkt ausgeführt wird.
    Base.metadata.create_all(engine)
    print("Tables created!")