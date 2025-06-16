"""
auth_service.py - Service für Benutzerauthentifizierung
"""
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin
from data_models import User
from datamanager.sqlite_data_manager import SQliteDataManager

class AuthService:
    def __init__(self, data_manager: SQliteDataManager):
        self.data_manager = data_manager

    @staticmethod
    def hash_password(password: str) -> str:
        """Erstellt einen Hash aus dem Passwort"""
        return generate_password_hash(password)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Überprüft, ob das Passwort zum Hash passt"""
        return check_password_hash(password_hash, password)

    def register_user(self, username: str, email: str, password: str) -> Optional[User]:
        """
        Registriert einen neuen Benutzer.
        """
        with self.data_manager.SessionFactory() as session:
            # Prüfe ob Benutzer oder Email bereits existiert
            if session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first():
                return None

            try:
                # Erstelle neuen Benutzer
                user = User(
                    username=username,
                    email=email,
                    password_hash=self.hash_password(password)
                )
                session.add(user)
                session.commit()
                # Aktualisiere den Benutzer mit der Session
                session.refresh(user)
                return user
            except Exception as e:
                session.rollback()
                raise Exception(f"Fehler bei der Registrierung: {str(e)}")

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authentifiziert einen Benutzer.
        """
        with self.data_manager.SessionFactory() as session:
            user = session.query(User).filter_by(email=email).first()
            if user and self.verify_password(password, user.password_hash):
                return user
        return None

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Ändert das Passwort eines Benutzers.
        """
        with self.data_manager.SessionFactory() as session:
            user = session.query(User).get(user_id)
            if not user or not self.verify_password(old_password, user.password_hash):
                return False

            user.password_hash = self.hash_password(new_password)
            session.commit()
            return True

def init_login_manager(app):
    """Initialisiert und konfiguriert den Login Manager"""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'  # Name der Login-Route
    login_manager.login_message = 'Bitte melden Sie sich an, um diese Seite zu sehen.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from data_models import User
        from datamanager.sqlite_data_manager import SQliteDataManager

        data_manager = SQliteDataManager("sqlite:///movie_app.db")
        with data_manager.SessionFactory() as session:
            return session.query(User).get(int(user_id))

    return login_manager
