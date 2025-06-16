"""
Konvertiert die Filmbewertungen von String zu Float
"""
from sqlalchemy import create_engine, text
import os

def convert_ratings():
    # Verbindung zur Datenbank herstellen
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'movie_app.db')
    engine = create_engine(f'sqlite:///{db_path}')

    with engine.connect() as conn:
        # Temporäre Spalte erstellen
        conn.execute(text("ALTER TABLE movies ADD COLUMN rating_float FLOAT"))

        # Daten konvertieren
        conn.execute(text("""
            UPDATE movies 
            SET rating_float = CAST(rating AS FLOAT) 
            WHERE rating IS NOT NULL AND rating != ''
        """))

        # Alte Spalte löschen und neue umbenennen
        conn.execute(text("DROP TABLE IF EXISTS movies_backup"))
        conn.execute(text("CREATE TABLE movies_backup AS SELECT * FROM movies"))
        conn.execute(text("DROP TABLE movies"))
        conn.execute(text("""
            CREATE TABLE movies (
                id INTEGER PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                release_year INTEGER,
                description TEXT,
                genre VARCHAR(255),
                director VARCHAR(255),
                rating FLOAT,
                poster_url VARCHAR(500),
                country VARCHAR(255)
            )
        """))
        conn.execute(text("""
            INSERT INTO movies 
            SELECT id, title, release_year, description, genre, director, 
                   rating_float, poster_url, country 
            FROM movies_backup
        """))
        conn.execute(text("DROP TABLE movies_backup"))

        conn.commit()

if __name__ == "__main__":
    convert_ratings()
