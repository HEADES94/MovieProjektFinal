"""
Migration: Füge theme und email_notifications Spalten zur users Tabelle hinzu
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def add_theme_settings_to_users():
    """Fügt theme und email_notifications Spalten zur users Tabelle hinzu"""

    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="movie_app_postgres",
            user=os.getenv('DB_USER', 'joshui'),
            password=os.getenv('DB_PASSWORD', '')
        )
        cursor = conn.cursor()

        # Prüfe ob theme Spalte bereits existiert
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'theme'
        """)

        if not cursor.fetchone():
            print("Füge theme Spalte zur users Tabelle hinzu...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN theme VARCHAR(20) DEFAULT 'system'
            """)

        # Prüfe ob email_notifications Spalte bereits existiert
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'email_notifications'
        """)

        if not cursor.fetchone():
            print("Füge email_notifications Spalte zur users Tabelle hinzu...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN email_notifications BOOLEAN DEFAULT TRUE
            """)

        print("Theme-Einstellungen erfolgreich hinzugefügt!")
        conn.commit()

    except Exception as e:
        print(f"Fehler bei der Migration: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_theme_settings_to_users()
