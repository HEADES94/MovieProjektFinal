"""
Migration: Füge movie_id zur quiz_attempts Tabelle hinzu (PostgreSQL)
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def add_movie_id_to_quiz_attempts_postgresql():
    """Fügt movie_id Spalte zur quiz_attempts Tabelle in PostgreSQL hinzu"""

    conn = None
    # Verbindung zur PostgreSQL-Datenbank
    try:
        # Versuche verschiedene Benutzer (macOS Standard ist oft der aktuelle Benutzer)
        conn = psycopg2.connect(
            host="localhost",
            database="movie_app_postgres",
            user=os.getenv('DB_USER', 'joshui'),  # Standard macOS Benutzer
            password=os.getenv('DB_PASSWORD', '')
        )
        cursor = conn.cursor()

        # Prüfe ob movie_id Spalte bereits existiert
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'quiz_attempts' 
            AND column_name = 'movie_id'
        """)

        result = cursor.fetchone()

        if not result:
            print("Füge movie_id Spalte zur quiz_attempts Tabelle hinzu...")
            cursor.execute("""
                ALTER TABLE quiz_attempts 
                ADD COLUMN movie_id INTEGER REFERENCES movies(id)
            """)
            print("movie_id Spalte erfolgreich hinzugefügt!")
        else:
            print("movie_id Spalte existiert bereits.")

        conn.commit()

    except Exception as e:
        print(f"Fehler bei der Migration: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_movie_id_to_quiz_attempts_postgresql()
