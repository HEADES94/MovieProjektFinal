"""
auth_service.py - Service für Benutzerauthentifizierung
"""
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin
from sqlalchemy.orm import Session
from data_models import User

class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def register_user(self, username: str, email: str, password: str) -> Optional[User]:
        """
        Registriert einen neuen Benutzer.
        """
        # Prüfe ob Benutzer oder Email bereits existiert
        if self.session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first():
            return None

        # Erstelle neuen Benutzer
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )

        try:
            self.session.add(user)
            self.session.commit()
            return user
        except Exception:
            self.session.rollback()
            return None

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authentifiziert einen Benutzer.
        """
        user = self.session.query(User).filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            return user
        return None

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Ändert das Passwort eines Benutzers.
        """
        user = self.session.query(User).get(user_id)

        if not user or not check_password_hash(user.password_hash, old_password):
            return False

        user.password_hash = generate_password_hash(new_password)
        self.session.commit()
        return True

def init_login_manager(app) -> LoginManager:
    """
    Initialisiert den Flask-Login LoginManager.
    """
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Bitte melde dich an, um diese Seite zu sehen.'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from datamanager.sqlite_data_manager import SQliteDataManager
        data_manager = SQliteDataManager("sqlite:///movie_app.db")
        with data_manager.SessionFactory() as session:
            return session.query(User).get(int(user_id))

    return login_manager
