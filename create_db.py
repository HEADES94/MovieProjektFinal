from data_models import init_db
from sqlalchemy import create_engine

# Erstelle eine neue SQLite-Datenbank
DB_URL = "sqlite:///movie_app.db"

if __name__ == "__main__":
    # Initialisiere die Datenbank
    init_db(DB_URL)
