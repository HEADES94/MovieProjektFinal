"""
Migration: Füge movie_id zur quiz_attempts Tabelle hinzu
"""
import sqlite3
import os

def add_movie_id_to_quiz_attempts():
    """Fügt movie_id Spalte zur quiz_attempts Tabelle hinzu"""
    db_path = '/Users/joshui/PycharmProjects/MovieProjektFinal/movie_app.db'

    if not os.path.exists(db_path):
        print(f"Datenbank nicht gefunden: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Prüfe ob movie_id Spalte bereits existiert
        cursor.execute("PRAGMA table_info(quiz_attempts)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'movie_id' not in columns:
            print("Füge movie_id Spalte zur quiz_attempts Tabelle hinzu...")
            cursor.execute('ALTER TABLE quiz_attempts ADD COLUMN movie_id INTEGER')
            print("movie_id Spalte erfolgreich hinzugefügt!")
        else:
            print("movie_id Spalte existiert bereits.")

        conn.commit()

    except Exception as e:
        print(f"Fehler bei der Migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_movie_id_to_quiz_attempts()
