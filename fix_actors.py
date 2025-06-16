from sqlalchemy import create_engine, text
from data_models import Base, Actor, MovieActor, Movie
from sqlalchemy.orm import sessionmaker
from movie_api import OMDBClient
import time

# Verbindung zur Datenbank herstellen
engine = create_engine('sqlite:///movie_app.db')
Session = sessionmaker(bind=engine)
session = Session()

# Lösche alte, fehlerhafte Einträge
session.execute(text('DELETE FROM movie_actors'))
session.execute(text('DELETE FROM actors'))
session.commit()

# OMDB Client initialisieren
omdb_client = OMDBClient()

def get_actor_info(name):
    """Hole zusätzliche Informationen über den Schauspieler"""
    try:
        # Suche nach dem Schauspieler
        actor_data = omdb_client.search_person(name)
        if actor_data:
            return {
                'birth_year': actor_data.get('birth_year'),
                'bio': actor_data.get('bio')
            }
    except Exception as e:
        print(f"Fehler beim Abrufen der Informationen für {name}: {e}")
    return {'birth_year': None, 'bio': None}

def add_actor(name, birth_year=None, bio=None):
    """Füge einen Schauspieler zur Datenbank hinzu"""
    existing_actor = session.query(Actor).filter_by(name=name).first()
    if existing_actor:
        return existing_actor

    actor = Actor(name=name, birth_year=birth_year, bio=bio)
    session.add(actor)
    return actor

# Hole alle Filme und ihre Schauspieler
movies = session.query(Movie).all()
print(f"Verarbeite {len(movies)} Filme...")

for movie in movies:
    print(f"\nVerarbeite Film: {movie.title}")

    # Hole detaillierte Filminformationen von OMDB
    try:
        # Füge Jahr zum Filmtitel hinzu, um genauere Ergebnisse zu erhalten
        search_title = f"{movie.title}"
        if movie.release_year:
            search_title = f"{movie.title} ({movie.release_year})"

        movie_data = omdb_client.get_movie(search_title)

        if movie_data and 'actors' in movie_data:
            print(f"Gefundene Schauspieler für {movie.title}:")
            actor_names = [name.strip() for name in movie_data['actors'].split(',')]

            for actor_name in actor_names:
                print(f"- {actor_name}")

                # Hole zusätzliche Informationen über den Schauspieler
                actor_info = get_actor_info(actor_name)

                # Füge den Schauspieler hinzu oder hole existierenden
                actor = add_actor(
                    name=actor_name,
                    birth_year=actor_info.get('birth_year'),
                    bio=actor_info.get('bio')
                )

                # Verknüpfe Schauspieler mit Film
                existing_relation = session.query(MovieActor).filter_by(
                    movie_id=movie.id,
                    actor_id=actor.id
                ).first()

                if not existing_relation:
                    movie_actor = MovieActor(
                        movie_id=movie.id,
                        actor_id=actor.id,
                        role_name=None
                    )
                    session.add(movie_actor)
        else:
            print(f"Keine Schauspieler gefunden für: {movie.title}")

        # Commit nach jedem Film und warte kurz um API-Limits zu respektieren
        session.commit()
        time.sleep(1)  # Warte 1 Sekunde zwischen API-Aufrufen

    except Exception as e:
        print(f"Fehler beim Verarbeiten von {movie.title}: {e}")
        session.rollback()
        continue

print("\nFertig! Alle Schauspieler wurden aktualisiert.")
