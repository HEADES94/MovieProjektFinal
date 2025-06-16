from data_models import Movie, init_db
from movie_api import OMDBClient
from datamanager.sqlite_data_manager import SQliteDataManager
import time


IMDB_TOP_100 = [
    "The Good, the Bad and the Ugly", "Inglourious Basterds", "Memento", "Requiem for a Dream",
    "Apocalypse Now Redux", "Indiana Jones and the Last Crusade", "Die Hard", "The Green Mile",
    "The Thing", "Full Metal Jacket", "Good Will Hunting", "Heat", "Casino", "The Sixth Sense",
    "The Big Lebowski", "No Country for Old Men", "Mad Max: Fury Road", "Jurassic Park",
    "Kill Bill: Vol. 1", "Finding Nemo", "Raging Bull", "The Deer Hunter", "Lawrence of Arabia",
    "Gone with the Wind", "Gran Torino", "V for Vendetta", "Batman Begins", "Snatch",
    "A Beautiful Mind", "Blade Runner", "Paper Moon", "The Bridge on the River Kwai",
    "Lock, Stock and Two Smoking Barrels", "Ben-Hur", "Casino Royale", "The Elephant Man",
    "The Wolf of Wall Street", "Pan's Labyrinth", "Reservoir Dogs", "The Third Man",
    "Eternal Sunshine of the Spotless Mind", "L.A. Confidential", "Mr. Smith Goes to Washington",
    "Double Indemnity", "North by Northwest", "Das Boot", "Taxi Driver", "Vertigo",
    "M", "Touch of Evil", "The Secret in Their Eyes", "The Sting", "The Seventh Seal",
    "3 Idiots", "2001: A Space Odyssey"
]  # Gekürzte Liste, um API-Limits nicht zu überschreiten

def add_imdb_top_movies():
    """Fügt die IMDB Top Filme zur Datenbank hinzu"""
    print("Initialisiere Dienste...")
    data_manager = SQliteDataManager("sqlite:///movie_app.db")
    omdb_client = OMDBClient()

    print("\nBeginne mit dem Hinzufügen der Filme...")
    added_count = 0

    with data_manager.SessionFactory() as session:
        for title in IMDB_TOP_100:
            try:
                # Prüfe ob der Film bereits existiert
                existing_movie = session.query(Movie).filter(Movie.title.ilike(f"%{title}%")).first()
                if existing_movie:
                    print(f"Film '{title}' existiert bereits.")
                    continue

                # Hole Filminformationen von OMDB
                movie_data = omdb_client.get_movie(title)
                if movie_data:
                    # Erstelle neuen Film
                    movie = Movie(
                        title=movie_data['title'],
                        description=movie_data['plot'],
                        release_year=movie_data['year'],
                        genre=movie_data['genre'],
                        poster_url=movie_data['poster'],
                        director=movie_data['director'],
                        rating=movie_data['rating'],
                        country=movie_data['country']
                    )

                    session.add(movie)
                    session.commit()
                    added_count += 1
                    print(f"✅ Film '{title}' erfolgreich hinzugefügt!")
                else:
                    print(f"❌ Keine Daten gefunden für '{title}'")

                # Kleine Pause um die API nicht zu überlasten
                time.sleep(1)

            except Exception as e:
                print(f"❌ Fehler beim Hinzufügen von '{title}': {str(e)}")
                session.rollback()
                continue

    print(f"\nFertig! {added_count} neue Filme wurden hinzugefügt.")

if __name__ == "__main__":
    add_imdb_top_movies()
