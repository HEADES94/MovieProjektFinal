"""SQLAlchemy data models for MovieProjekt."""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from flask_login import UserMixin

TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


class Movie(Base):
    """Movie model representing a film in the database."""
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    release_year = Column(Integer)
    plot = Column(Text)
    genre = Column(String(255))
    director = Column(String(255))
    rating = Column(Float)
    poster_url = Column(String(500))
    country = Column(String(255))

    movie_actors = relationship('MovieActor', back_populates='movie', overlaps="actors,movies")
    actors = relationship('Actor', secondary='movie_actors', back_populates='movies', overlaps="movie_actors")
    reviews = relationship('Review', back_populates='movie')
    quiz_questions = relationship('QuizQuestion', back_populates='movie')

    def __repr__(self) -> str:
        return f"<Movie(title={self.title}, id={self.id if self.id else 'None'})>"


class User(UserMixin, Base):
    """User model representing a user who can rate movies."""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    theme = Column(String(20), default='system')
    email_notifications = Column(Boolean, default=True)

    reviews = relationship("Review", back_populates="user")
    watchlist_items = relationship("WatchlistItem", back_populates="user")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    achievements = relationship("Achievement", secondary="user_achievements", back_populates="users", overlaps="achievements")
    suggested_questions = relationship("SuggestedQuestion", back_populates="user")
    user_movies = relationship("UserMovie", back_populates="user")

    @property
    def name(self):
        """Backward compatibility property for name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    def __repr__(self) -> str:
        return f"<User(name='{self.name}', id={self.id if self.id else 'None'})>"


class Actor(Base):
    """Actor model representing a film actor."""
    __tablename__ = 'actors'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    birth_year = Column(Integer)
    bio = Column(Text)

    movie_actors = relationship('MovieActor', back_populates='actor', overlaps="actors,movies")
    movies = relationship('Movie', secondary='movie_actors', back_populates='actors', overlaps="movie_actors")


class MovieActor(Base):
    """Association table for Movie-Actor many-to-many relationship."""
    __tablename__ = 'movie_actors'
    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=False)
    actor_id = Column(Integer, ForeignKey('actors.id'), nullable=False)
    role_name = Column(String(255))

    movie = relationship('Movie', back_populates='movie_actors', overlaps="actors,movies")
    actor = relationship('Actor', back_populates='movie_actors', overlaps="actors,movies")


class Review(Base):
    """Review model representing a user's review of a movie."""
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=False)
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='reviews')
    movie = relationship('Movie', back_populates='reviews')


class WatchlistItem(Base):
    """WatchlistItem model representing a user's watchlist entry for a movie."""
    __tablename__ = 'watchlist'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    added_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watchlist_items")
    movie = relationship("Movie")


class MovieRecommendation(Base):
    """MovieRecommendation model representing a movie recommended to a user."""
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
    """QuizQuestion model representing a question in the movie quiz."""
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
    attempt_questions = relationship("QuizAttemptQuestion", back_populates="question")


class AIQuestionMetadata(Base):
    """AIQuestionMetadata model representing metadata for AI-generated quiz questions."""
    __tablename__ = 'ai_question_metadata'
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('quiz_questions.id'))
    ai_model = Column(String)
    temperature = Column(Float)
    prompt = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("QuizQuestion", back_populates="ai_metadata")


class QuizAttempt(Base):
    """QuizAttempt model representing a user's attempt to complete a quiz."""
    __tablename__ = 'quiz_attempts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))  # Hinzugefügt für film-spezifische Statistiken
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    difficulty = Column(String(10), default='medium')
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="quiz_attempts")
    movie = relationship("Movie")  # Hinzugefügt für film-spezifische Beziehung
    attempt_questions = relationship("QuizAttemptQuestion", back_populates="attempt")


class QuizAttemptQuestion(Base):
    """Verknüpfungstabelle zwischen QuizAttempt und QuizQuestion"""
    __tablename__ = 'quiz_attempt_questions'
    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey('quiz_attempts.id'))
    question_id = Column(Integer, ForeignKey('quiz_questions.id'))
    user_answer = Column(Text)
    is_correct = Column(Boolean)
    answered_at = Column(DateTime, default=datetime.utcnow)

    attempt = relationship("QuizAttempt", back_populates="attempt_questions")
    question = relationship("QuizQuestion", back_populates="attempt_questions")


class Highscore(Base):
    """Highscore model representing a user's high score for a movie."""
    __tablename__ = 'highscores'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    best_score = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    movie = relationship("Movie")


class SuggestedQuestion(Base):
    """SuggestedQuestion model representing a question suggested by a user."""
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
    """QuestionVote model representing a user's vote on a suggested question."""
    __tablename__ = 'question_votes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    suggested_question_id = Column(Integer, ForeignKey('suggested_questions.id'))
    vote = Column(Integer)  # 1 für upvote, -1 für downvote
    voted_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    question = relationship("SuggestedQuestion", back_populates="votes")


class Achievement(Base):
    """Achievement model representing a user's achievement."""
    __tablename__ = 'achievements'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)  # Geändert von 'title' zu 'name'
    description = Column(Text)
    code = Column(String(50), unique=True)  # Eindeutiger Code für jedes Achievement

    users = relationship("User", secondary="user_achievements", back_populates="achievements", overlaps="achievements")


class UserAchievement(Base):
    """UserAchievement model representing a user's earned achievement."""
    __tablename__ = 'user_achievements'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    achievement_id = Column(Integer, ForeignKey('achievements.id'))
    earned_at = Column(DateTime, default=datetime.utcnow)


class UserMovie(Base):
    """UserMovie model linking users with their personal movie information."""
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
    """Initializes the database and creates all tables."""
    global engine
    if db_url:
        engine = create_engine(db_url)
    Base.metadata.create_all(engine)


def drop_db():
    """Drops all tables."""
    Base.metadata.drop_all(engine)


if __name__ == "__main__":
    # Create the tables if the script is run directly.
    Base.metadata.create_all(engine)
    print("Tables created!")