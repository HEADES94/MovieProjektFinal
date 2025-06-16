"""
update_actors.py - Aktualisiert die Schauspielerinformationen für vorhandene Filme
"""
from sqlalchemy import create_engine
from data_models import Movie, Actor, MovieActor, Base
from sqlalchemy.orm import Session, sessionmaker
from services.movie_update_service import MovieUpdateService
from datamanager.sqlite_data_manager import SQliteDataManager
import os

def update_existing_movies_with_actors():
    # Verwende die lokale SQLite-Datenbankdatei
    db_path = os.path.join(os.path.dirname(__file__), 'movie_app.db')
    db_url = f'sqlite:///{db_path}'

    # Stelle sicher, dass die Datenbank existiert
    if not os.path.exists(db_path):
        print("Datenbank existiert nicht!")
        return

    # Erstelle Engine und Session
    engine = create_engine(db_url)
    Base.metadata.bind = engine

    # Stelle sicher, dass alle Tabellen existieren
    Base.metadata.create_all(engine)

    data_manager = SQliteDataManager(db_url)
    movie_service = MovieUpdateService(data_manager)

    Session = sessionmaker(bind=engine)

    with Session() as session:
        try:
            # Hole alle Filme
            movies = session.query(Movie).all()

            if not movies:
                print("Keine Filme in der Datenbank gefunden!")
                return

            print(f"Gefundene Filme: {len(movies)}")

            for movie in movies:
                print(f"Verarbeite Film: {movie.title}")
                if not movie.actors:  # Nur für Filme ohne Schauspieler
                    print(f"Aktualisiere Schauspieler für: {movie.title}")
                    actors = movie_service.get_actors_from_omdb(movie.title)

                    if actors:
                        for actor_data in actors:
                            # Prüfe ob Schauspieler bereits existiert
                            actor = session.query(Actor).filter_by(
                                name=actor_data['name']
                            ).first()

                            if not actor:
                                actor = Actor(
                                    name=actor_data['name'],
                                )
                                session.add(actor)
                                session.flush()

                            # Verknüpfe Film und Schauspieler, falls noch nicht verknüpft
                            existing_link = session.query(MovieActor).filter_by(
                                movie_id=movie.id,
                                actor_id=actor.id
                            ).first()

                            if not existing_link:
                                movie_actor = MovieActor(
                                    movie_id=movie.id,
                                    actor_id=actor.id,
                                    role_name=actor_data.get('role_name', '')
                                )
                                session.add(movie_actor)
                        print(f"Schauspieler hinzugefügt für: {movie.title}")
                    else:
                        print(f"Keine Schauspieler gefunden für: {movie.title}")
                else:
                    print(f"Film hat bereits Schauspieler: {movie.title}")

            session.commit()
            print("Aktualisierung abgeschlossen!")

        except Exception as e:
            print(f"Fehler während der Aktualisierung: {e}")
            session.rollback()
            raise

if __name__ == '__main__':
    update_existing_movies_with_actors()
