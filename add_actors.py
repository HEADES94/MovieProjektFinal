import os
import requests
from data_models import Movie, Actor, MovieActor
from datamanager.sqlite_data_manager import SQliteDataManager
import time
from dotenv import load_dotenv

load_dotenv()

def get_movie_credits(movie_title):
    """Hole die Besetzungsinformationen von TMDb API"""
    api_key = os.getenv("TMDB_API_KEY")

    # Erst nach dem Film suchen
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": api_key,
        "query": movie_title,
        "language": "de-DE"
    }

    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        search_data = response.json()

        if search_data["results"]:
            movie_id = search_data["results"][0]["id"]

            # Dann die Credits für den Film holen
            credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
            params = {
                "api_key": api_key,
                "language": "de-DE"
            }

            response = requests.get(credits_url, params=params)
            response.raise_for_status()
            credits_data = response.json()

            return credits_data.get("cast", [])

    except Exception as e:
        print(f"Fehler beim API-Aufruf für '{movie_title}': {str(e)}")

    return None

def add_actors_to_movies():
    """Fügt Schauspieler zu den vorhandenen Filmen hinzu"""
    print("Initialisiere Dienste...")
    data_manager = SQliteDataManager("sqlite:///movie_app.db")

    print("\nBeginne mit dem Hinzufügen der Schauspieler...")
    added_actors = 0
    added_relations = 0

    with data_manager.SessionFactory() as session:
        movies = session.query(Movie).all()

        for movie in movies:
            try:
                print(f"\nVerarbeite Film: {movie.title}")
                cast = get_movie_credits(movie.title)

                if cast:
                    # Verarbeite die ersten 10 Hauptdarsteller
                    for actor_data in cast[:10]:
                        actor_name = actor_data["name"]
                        character = actor_data.get("character", "")

                        # Prüfe ob der Schauspieler bereits existiert
                        actor = session.query(Actor).filter(Actor.name == actor_name).first()

                        if not actor:
                            # Erstelle neuen Schauspieler
                            actor = Actor(
                                name=actor_name,
                                # Weitere Informationen könnten hier hinzugefügt werden
                            )
                            session.add(actor)
                            session.flush()
                            added_actors += 1
                            print(f"✅ Schauspieler '{actor_name}' hinzugefügt")

                        # Erstelle Verbindung zwischen Film und Schauspieler
                        existing_relation = session.query(MovieActor).filter_by(
                            movie_id=movie.id,
                            actor_id=actor.id
                        ).first()

                        if not existing_relation:
                            movie_actor = MovieActor(
                                movie_id=movie.id,
                                actor_id=actor.id,
                                role_name=character
                            )
                            session.add(movie_actor)
                            added_relations += 1
                            print(f"✅ Rolle '{character}' für '{actor_name}' in '{movie.title}' hinzugefügt")

                    session.commit()

                # Kleine Pause zwischen API-Aufrufen
                time.sleep(0.5)

            except Exception as e:
                print(f"❌ Fehler bei Film '{movie.title}': {str(e)}")
                session.rollback()
                continue

    print(f"\n=== Zusammenfassung ===")
    print(f"✅ {added_actors} neue Schauspieler hinzugefügt")
    print(f"✅ {added_relations} neue Film-Schauspieler-Verbindungen erstellt")

if __name__ == "__main__":
    add_actors_to_movies()
