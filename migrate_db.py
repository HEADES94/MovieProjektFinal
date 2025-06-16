"""
Migrations-Skript für die Datenbank
"""
import sqlite3
from data_models import Base, engine

def migrate_database():
    # Verbindung zur Datenbank herstellen
    conn = sqlite3.connect('movie_app.db')
    cursor = conn.cursor()

    try:
        # Backup der bestehenden Daten
        cursor.execute("CREATE TABLE IF NOT EXISTS quiz_attempts_backup AS SELECT * FROM quiz_attempts")

        # Alte Tabelle löschen
        cursor.execute("DROP TABLE IF EXISTS quiz_attempts")

        # Neue Tabelle mit aktualisiertem Schema erstellen
        Base.metadata.create_all(engine)

        # Daten aus dem Backup in die neue Tabelle kopieren
        cursor.execute("""
            INSERT INTO quiz_attempts 
            (id, user_id, movie_id, score, correct_count, created_at, max_possible_score)
            SELECT 
                id, user_id, movie_id, score, correct_count, created_at, 10
            FROM quiz_attempts_backup
        """)

        # Backup-Tabelle löschen
        cursor.execute("DROP TABLE quiz_attempts_backup")

        # Änderungen speichern
        conn.commit()
        print("Migration erfolgreich durchgeführt!")

    except Exception as e:
        print(f"Fehler bei der Migration: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
