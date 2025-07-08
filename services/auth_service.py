"""Service for user authentication."""
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin
from data_models import User
from datamanager.sqlite_data_manager import SQliteDataManager
import os


class AuthService:
    """Service for handling user authentication and authorization."""

    def __init__(self, data_manager: SQliteDataManager):
        self.data_manager = data_manager

    @staticmethod
    def hash_password(password: str) -> str:
        """Create a hash from the password."""
        return generate_password_hash(password)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Check if the password matches the hash."""
        return check_password_hash(password_hash, password)

    def register_user(self, username: str, email: str, password: str) -> Optional[User]:
        """Register a new user."""
        with self.data_manager.SessionFactory() as session:
            if session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first():
                return None

            try:
                user = User(
                    username=username,
                    email=email,
                    password_hash=self.hash_password(password)
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                return user
            except Exception as e:
                session.rollback()
                raise Exception(f"Registration error: {str(e)}")

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        with self.data_manager.SessionFactory() as session:
            user = session.query(User).filter_by(email=email).first()
            if user and self.verify_password(password, user.password_hash):
                return user
        return None

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change a user's password."""
        with self.data_manager.SessionFactory() as session:
            user = session.query(User).get(user_id)
            if not user or not self.verify_password(old_password, user.password_hash):
                return False

            user.password_hash = self.hash_password(new_password)
            session.commit()
            return True


def init_login_manager(app):
    """Initialize and configure the login manager."""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from data_models import User
        from datamanager.sqlite_data_manager import SQliteDataManager
        import os

        db_url = os.getenv('DATABASE_URL', 'postgresql://localhost/movie_app_postgres')
        data_manager = SQliteDataManager(db_url)
        with data_manager.SessionFactory() as session:
            return session.query(User).get(int(user_id))

    return login_manager
