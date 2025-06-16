from sqlalchemy import create_engine, text

def update_quiz_table():
    # Verbindung zur Datenbank herstellen
    engine = create_engine('sqlite:///movie_app.db')

    # SQL-Befehl zum Hinzufügen der neuen Spalte
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE quiz_attempts ADD COLUMN difficulty STRING DEFAULT 'mittel'"))
            conn.commit()
            print("Erfolgreich 'difficulty' Spalte zu quiz_attempts hinzugefügt")
        except Exception as e:
            print(f"Fehler oder Spalte existiert bereits: {e}")

if __name__ == "__main__":
    update_quiz_table()
