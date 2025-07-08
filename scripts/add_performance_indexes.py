"""
Database Performance Optimization Script
Fügt Indizes für bessere Query-Performance hinzu
"""
from datamanager.sqlite_data_manager import SQliteDataManager
from sqlalchemy import text

def add_database_indexes():
    """Fügt Performance-Indizes zur Datenbank hinzu"""
    data_manager = SQliteDataManager("postgresql://localhost/movie_app_postgres")

    with data_manager.SessionFactory() as session:
        try:
            # Indizes für Movie-Tabelle (häufigste Queries)
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_movie_title ON movies(title);",
                "CREATE INDEX IF NOT EXISTS idx_movie_genre ON movies(genre);",
                "CREATE INDEX IF NOT EXISTS idx_movie_rating ON movies(rating);",
                "CREATE INDEX IF NOT EXISTS idx_movie_year ON movies(release_year);",
                "CREATE INDEX IF NOT EXISTS idx_movie_director ON movies(director);",

                # Composite Indizes für häufige Kombinationen
                "CREATE INDEX IF NOT EXISTS idx_movie_genre_rating ON movies(genre, rating);",
                "CREATE INDEX IF NOT EXISTS idx_movie_title_genre ON movies(title, genre);",

                # Indizes für andere Tabellen
                "CREATE INDEX IF NOT EXISTS idx_review_movie_id ON reviews(movie_id);",
                "CREATE INDEX IF NOT EXISTS idx_review_user_id ON reviews(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_movie_user_id ON user_movies(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_movie_movie_id ON user_movies(movie_id);",
                "CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON watchlist_items(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_watchlist_movie_id ON watchlist_items(movie_id);",
            ]

            for index_sql in indexes:
                session.execute(text(index_sql))
                print(f"✅ Index erstellt: {index_sql}")

            session.commit()
            print("🚀 Alle Performance-Indizes erfolgreich hinzugefügt!")

        except Exception as e:
            session.rollback()
            print(f"❌ Fehler beim Erstellen der Indizes: {e}")

if __name__ == "__main__":
    add_database_indexes()
