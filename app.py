"""
Flask application for the MovieProjekt.
Main module for the Flask application where central services, routes and configurations are initialized.
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from sqlalchemy.orm import joinedload
from sqlalchemy import func, case
import random
import os
from datetime import datetime, UTC
from dotenv import load_dotenv

load_dotenv()

from utils.logging_config import setup_logging

from ai_request import AIRequest
from datamanager.sqlite_data_manager import SQliteDataManager
from data_models import User, Movie, UserMovie, SuggestedQuestion, Review, QuizAttempt, UserAchievement, Achievement
from services.quiz_service import QuizService
from services.auth_service import AuthService, init_login_manager
from services.watchlist_service import WatchlistService
from services.achievement_service import AchievementService
from services.movie_update_service import MovieUpdateService

app = Flask(__name__)
app.config.update(
    ENV=os.getenv('FLASK_ENV', 'development'),
    DEBUG=os.getenv('DEBUG', 'True').lower() == 'true',
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-change-in-production'),
    WTF_CSRF_ENABLED=True,
    DATABASE_URL=os.getenv('DATABASE_URL', 'postgresql://localhost/movie_app_postgres'),
    GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY'),
    TMDB_API_KEY=os.getenv('TMDB_API_KEY'),
    OMDB_API_KEY=os.getenv('OMDB_API_KEY')
)

setup_logging(app)

from utils.security import add_security_headers
app.after_request(add_security_headers)

csrf = CSRFProtect(app)


def jinja2_shuffle(seq):
    """
    Shuffle a sequence for use in Jinja2 templates.

    Args:
        seq: Sequence (e.g. list) to be shuffled

    Returns:
        Shuffled sequence
    """
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq


app.jinja_env.filters['shuffle'] = jinja2_shuffle

data_manager = SQliteDataManager("postgresql://localhost/movie_app_postgres")
ai_client = AIRequest()
login_manager = init_login_manager(app)
movie_update_service = MovieUpdateService(data_manager)

auth_service = AuthService(data_manager)
watchlist_service = WatchlistService(data_manager)


def update_movies():
    """Update the movie database with new movies."""
    return movie_update_service.update_movie_database()


with app.app_context():
    pass


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


@app.route('/')
def home():
    """
    Home page route.

    Returns:
        Rendered home template
    """
    # update_movies()  # Deaktiviert nach Database Reset
    with data_manager.SessionFactory() as session:
        # Hole alle Filme und sortiere sie nach Rating (absteigend)
        movies = session.query(Movie).order_by(Movie.rating.desc()).limit(10).all()
        users = session.query(User).all()

        # Wenn ein Benutzer eingeloggt ist, lade seine Daten
        user_stats = None
        if current_user.is_authenticated:
            user = session.get(User, current_user.id, options=[
                joinedload(User.reviews),
                joinedload(User.watchlist_items),
                joinedload(User.quiz_attempts),
                joinedload(User.achievements)
            ])
            if user:
                user_stats = {
                    'reviews_count': len(user.reviews),
                    'watchlist_count': len(user.watchlist_items),
                    'quiz_attempts': len(user.quiz_attempts),
                    'achievements': len(user.achievements)
                }

        return render_template("home.html", movies=movies, users=users, user_stats=user_stats)


@app.route('/users')
def list_users():
    with data_manager.SessionFactory() as session:
        users = session.query(User).all()
        # Hole für jeden User die Anzahl der Filme (ohne Lazy Loading)
        user_data = []
        for user in users:
            movie_count = session.query(UserMovie).filter_by(user_id=user.id).count()
            user_data.append({
                "id": user.id,
                "username": user.username,
                "movie_count": movie_count
            })
    return render_template("users.html", users=user_data)


@app.route('/users/<user_id>', methods=["GET", "POST"])
def user_movies(user_id):
    with data_manager.SessionFactory() as session:
        if request.method == "GET":
            chosen_user = session.get(User, user_id)
            if not chosen_user:
                return render_template("404.html"), 404

            user_movies_list = session.query(UserMovie).filter_by(user_id=user_id).all()
            return render_template("user_movies.html",
                                user_movies=user_movies_list,
                                user=chosen_user)

        elif request.method == "POST":
            chosen_user = session.get(User, user_id)
            if not chosen_user:
                return render_template("404.html"), 404

            movie_title = request.form["name"]
            movie = session.query(Movie).filter_by(title=movie_title).first()

            if movie is None:
                try:
                    # Verwende den movie_update_service um den Film hinzuzufügen
                    movie = movie_update_service.add_movie(movie_title)
                    if movie is None:
                        raise Exception("Film konnte nicht gefunden werden")

                    new_user_movie = UserMovie(user_id=user_id, movie_id=movie.id)
                    session.add(new_user_movie)
                    session.commit()

                    user_movies_list = session.query(UserMovie).filter_by(user_id=user_id).all()
                    return render_template("user_movies.html",
                                        user_movies=user_movies_list,
                                        user=chosen_user,
                                        success=True)
                except Exception as e:
                    session.rollback()
                    user_movies_list = session.query(UserMovie).filter_by(user_id=user_id).all()
                    return render_template("user_movies.html",
                                        user_movies=user_movies_list,
                                        user=chosen_user,
                                        success=False,
                                        error=str(e))
            else:
                existing_user_movie = session.query(UserMovie).filter_by(
                    user_id=user_id,
                    movie_id=movie.id
                ).first()

                if existing_user_movie:
                    user_movies_list = session.query(UserMovie).filter_by(user_id=user_id).all()
                    return render_template("user_movies.html",
                                        user_movies=user_movies_list,
                                        user=chosen_user,
                                        success=False,
                                        error="Film ist bereits in der Liste")
                try:
                    new_user_movie = UserMovie(user_id=user_id, movie_id=movie.id)
                    session.add(new_user_movie)
                    session.commit()

                    user_movies_list = session.query(UserMovie).filter_by(user_id=user_id).all()
                    return render_template("user_movies.html",
                                        user_movies=user_movies_list,
                                        user=chosen_user,
                                        success=True)
                except Exception as e:
                    session.rollback()
                    user_movies_list = session.query(UserMovie).filter_by(user_id=user_id).all()
                    return render_template("user_movies.html",
                                        user_movies=user_movies_list,
                                        user=chosen_user,
                                        success=False,
                                        error=str(e))


@app.route('/users/<user_id>/<movie_id>', methods=["GET", "POST"])
def update_user_movie(user_id, movie_id):
    if request.method == "GET":
        chosen_user = data_manager.get_user(user_id)
        movie = data_manager.get_movie(movie_id)
        user_movie = data_manager.get_user_movie(user_id, movie_id)
        return render_template("user_movie.html", user_movie=user_movie,
                               user=chosen_user, movie=movie)
    elif request.method == "POST":
        chosen_user = data_manager.get_user(user_id)
        movie = data_manager.get_movie(movie_id)
        user_movie = data_manager.get_user_movie(user_id, movie_id)
        user_rating = request.form.get("user_rating")
        user_comment = request.form.get("user_comment")
        try:
            data_manager.update_user_movie(
                user_id=user_id,
                movie_id=movie_id,
                update_data={"user_rating": user_rating, "user_comment": user_comment}
            )
            new_user_movie = data_manager.get_user_movie(user_id, movie_id)
            return render_template(
                "user_movie.html",
                user_movie=new_user_movie,
                user=chosen_user,
                movie=movie,
                success=True
            )
        except Exception:
            return render_template(
                "user_movie.html",
                user_movie=user_movie,
                user=chosen_user,
                movie=movie,
                success=False
            )


@app.route('/users/new', methods=["GET", "POST"])
def new_user():
    if request.method == "GET":
        return render_template("new_user.html")
    elif request.method == "POST":
        name = request.form.get("name")
        user = User(name=name, username=name)
        with data_manager.SessionFactory() as session:
            try:
                session.add(user)
                session.commit()
                return render_template("new_user.html", success=True)
            except Exception:
                session.rollback()
                return render_template("new_user.html", success=False)


@app.route('/movies/new', methods=["GET", "POST"])
def new_movie():
    if request.method == "POST":
        movie_title = request.form.get('name')
        if not movie_title:
            return render_template('new_movie.html', error='Bitte geben Sie einen Filmtitel ein')

        try:
            # Versuche den Film hinzuzufügen
            movie = movie_update_service.add_movie(movie_title)

            if movie is None:
                return render_template('new_movie.html',
                                    error=f'Film konnte nicht gefunden werden: {movie_title}',
                                    movie_name=movie_title)
            else:
                return render_template('new_movie.html',
                                    success=True,
                                    movie_name=movie.title)

        except Exception as e:
            return render_template('new_movie.html',
                                error=str(e),
                                movie_name=movie_title)

    return render_template('new_movie.html')


@app.route('/movies', methods=["GET", "POST"])
def list_movies():
    if request.method == "GET":
        search_query = request.args.get('search', '')
        sort_by = request.args.get('sort', 'rating')
        genre_filter = request.args.get('genre', '')
        page = int(request.args.get('page', 1))
        per_page = 20  # Pagination: Nur 20 Filme pro Seite laden

        with data_manager.SessionFactory() as session:
            # Optimierte Query mit SELECT nur benötigter Felder
            query = session.query(
                Movie.id,
                Movie.title,
                Movie.genre,
                Movie.rating,
                Movie.release_year,
                Movie.poster_url,
                Movie.director
            )

            # Suche anwenden (optimiert)
            if search_query:
                search_terms = f"%{search_query}%"
                query = query.filter(
                    Movie.title.ilike(search_terms) |
                    Movie.genre.ilike(search_terms) |
                    Movie.director.ilike(search_terms)
                )

            # Genre-Filter anwenden (optimiert für kombinierte Genres)
            if genre_filter:
                query = query.filter(Movie.genre.ilike(f"%{genre_filter}%"))

            # Sortierung anwenden (mit Indizes optimiert)
            if sort_by == 'title':
                query = query.order_by(Movie.title)
            elif sort_by == 'year_desc':
                query = query.order_by(Movie.release_year.desc().nulls_last())
            elif sort_by == 'year_asc':
                query = query.order_by(Movie.release_year.asc().nulls_last())
            else:  # default: rating
                query = query.order_by(Movie.rating.desc().nulls_last())

            # Pagination anwenden
            total_movies = query.count()
            movies = query.offset((page - 1) * per_page).limit(per_page).all()

            # Pagination Info
            total_pages = (total_movies + per_page - 1) // per_page
            has_prev = page > 1
            has_next = page < total_pages

            return render_template("movies.html",
                                movies=movies,
                                sort_by=sort_by,
                                search_query=search_query,
                                selected_genre=genre_filter,
                                pagination={
                                    'page': page,
                                    'per_page': per_page,
                                    'total': total_movies,
                                    'total_pages': total_pages,
                                    'has_prev': has_prev,
                                    'has_next': has_next,
                                    'prev_num': page - 1 if has_prev else None,
                                    'next_num': page + 1 if has_next else None
                                })

    elif request.method == "POST":
        movie_id = request.form["movie_id"]
        with data_manager.SessionFactory() as session:
            deleted = data_manager.delete_movie(int(movie_id))
            movies = session.query(Movie).order_by(Movie.rating.desc()).all()
            return render_template("movies.html",
                                movies=movies,
                                success=deleted)


@app.route('/movies/<movie_id>', methods=["GET", "POST"])
@login_required
def movie_details(movie_id):
    with data_manager.SessionFactory() as session:
        movie = session.get(Movie, movie_id, options=[
            joinedload(Movie.actors),
            joinedload(Movie.reviews).joinedload(Review.user)
        ])

        if not movie:
            return render_template('404.html'), 404

        # POST-Methode für neue Bewertungen
        if request.method == "POST":
            try:
                # Hole die Bewertungsdaten aus dem Formular
                rating = int(request.form.get('rating'))
                comment = request.form.get('comment')

                # Überprüfe ob der Benutzer bereits eine Bewertung abgegeben hat
                existing_review = session.query(Review).filter_by(
                    user_id=current_user.id,
                    movie_id=movie_id
                ).first()

                if existing_review:
                    # Aktualisiere bestehende Bewertung
                    existing_review.rating = rating
                    existing_review.comment = comment
                    existing_review.updated_at = datetime.now(UTC)
                else:
                    # Erstelle neue Bewertung
                    review = Review(
                        user_id=current_user.id,
                        movie_id=movie_id,
                        rating=rating,
                        comment=comment,
                        created_at=datetime.now(UTC)
                    )
                    session.add(review)

                session.commit()

                # Achievement für 10 Reviews prüfen und ggf. vergeben (mindestens 10 und noch nicht erhalten)
                from services.achievement_service import AchievementService
                achievement_service = AchievementService(data_manager)

                # Prüfe Review-Achievements (inkl. erste Review und Meilensteine)
                new_achievements = achievement_service.check_review_achievements(current_user.id)

                # Zeige Achievement-Benachrichtigungen an
                if new_achievements:
                    for achievement in new_achievements:
                        flash(f"🏆 Achievement freigeschaltet: {achievement['title']} - {achievement['description']}", 'success')
            except Exception as e:
                session.rollback()
                flash('Fehler beim Speichern der Bewertung.', 'error')
                app.logger.error(f"Fehler bei Bewertung: {str(e)}")

        # Prüfe Watchlist-Status wenn Benutzer eingeloggt ist
        if current_user.is_authenticated:
            movie.in_watchlist = watchlist_service.is_in_watchlist(current_user.id, int(movie_id))

        # Berechne die Quiz-Statistiken für den aktuellen Film (korrigierte Version)
        stats = {
            'quiz_attempts': 0,
            'avg_score': 0,
            'completion_rate': 0
        }

        if current_user.is_authenticated:
            # Hole nur Quiz-Versuche für den aktuellen Film
            movie_quiz_attempts = session.query(QuizAttempt).filter_by(
                user_id=current_user.id,
                movie_id=movie_id
            ).all()

            print(f"DEBUG: Found {len(movie_quiz_attempts)} quiz attempts for user {current_user.id} and movie {movie_id}")

            if movie_quiz_attempts:
                stats['quiz_attempts'] = len(movie_quiz_attempts)

                # Debug: Zeige alle Quiz-Versuche für diesen Film
                for i, attempt in enumerate(movie_quiz_attempts):
                    print(f"DEBUG: Movie {movie_id} Attempt {i+1}: Score={attempt.score}, Total={attempt.total_questions}, Difficulty={attempt.difficulty}")

                # Berechne korrekte Anzahl richtiger Antworten basierend auf Punktzahl und Schwierigkeit
                total_correct_answers = 0
                for attempt in movie_quiz_attempts:
                    # Berechne die Anzahl richtiger Antworten basierend auf Punktzahl und Schwierigkeit
                    max_points_per_question = 200 if attempt.difficulty == 'schwer' else 100
                    bonus_threshold = attempt.total_questions * max_points_per_question

                    if attempt.score > bonus_threshold:
                        # Perfekte Punktzahl mit Bonus - alle Antworten richtig
                        correct_answers = attempt.total_questions
                    else:
                        # Berechne Anzahl richtiger Antworten ohne Bonus
                        correct_answers = attempt.score // max_points_per_question

                    total_correct_answers += correct_answers

                # Berechne Durchschnittspunktzahl (Anzahl richtige Antworten pro Quiz)
                stats['avg_score'] = round(total_correct_answers / len(movie_quiz_attempts), 1)

                # Berechne Abschlussrate korrekt (Prozentsatz der richtig beantworteten Fragen)
                total_questions = sum(attempt.total_questions for attempt in movie_quiz_attempts)

                if total_questions > 0:
                    stats['completion_rate'] = round((total_correct_answers / total_questions) * 100, 1)
                else:
                    stats['completion_rate'] = 0

                print(f"DEBUG: Movie {movie_id} Stats - Attempts: {stats['quiz_attempts']}, Avg: {stats['avg_score']}, Rate: {stats['completion_rate']}%")
                print(f"DEBUG: Movie {movie_id} Total correct: {total_correct_answers}, Total questions: {total_questions}")
            else:
                print(f"DEBUG: No quiz attempts found for user {current_user.id} and movie {movie_id}")

        # Hole die Reviews
        reviews = session.query(Review).filter_by(movie_id=movie_id).order_by(Review.created_at.desc()).all()

        # Hole ähnliche Filme basierend auf Genre und Jahr
        similar_movies = session.query(Movie).filter(
            Movie.id != movie_id,
            Movie.genre.like(f'%{movie.genre}%'),
            Movie.release_year.between(movie.release_year - 5, movie.release_year + 5)
        ).order_by(Movie.rating.desc()).limit(4).all()

        # Hole KI-Empfehlungen basierend auf dem aktuellen Film
        try:
            # Erstelle einen String mit den Filminformationen
            movie_info = f"Title: {movie.title}, Genre: {movie.genre}, Year: {movie.release_year}, Rating: {movie.rating}"
            # Hole Empfehlungen von der KI
            ai_recommendation = ai_client.ai_request(movie_info)
            if ai_recommendation:
                # Prüfe ob die KI-Antwort das erwartete Format hat
                if 'movie' in ai_recommendation:
                    # Altes Format mit 'movie' Schlüssel
                    movie_data = ai_recommendation['movie']
                    reason = ai_recommendation.get('reason', 'KI-Empfehlung')
                elif 'title' in ai_recommendation:
                    # Neues Format ohne 'movie' Schlüssel
                    movie_data = {
                        'title': ai_recommendation.get('title'),
                        'year': ai_recommendation.get('year'),
                        'director': ai_recommendation.get('director'),
                        'genre': ai_recommendation.get('genre'),
                        'plot': ai_recommendation.get('plot') or ai_recommendation.get('description'),
                        'poster': ai_recommendation.get('poster'),
                        'imdb': ai_recommendation.get('imdb') or ai_recommendation.get('rating', 0)
                    }
                    reason = ai_recommendation.get('explanation', 'KI-Empfehlung')
                else:
                    ai_recommendations = []
                    movie_data = None

                if movie_data and movie_data.get('title'):
                    # Prüfe ob der empfohlene Film bereits in der Datenbank ist
                    ai_movie = session.query(Movie).filter(Movie.title.ilike(movie_data['title'])).first()
                    if not ai_movie:
                        # Korrigiere das Rating bevor der Film hinzugefügt wird
                        raw_rating = float(movie_data.get('imdb', 0)) if movie_data.get('imdb') else 0

                        # Rating-Korrektur-Logik
                        if raw_rating > 1000000:  # Extrem hohe Werte wie 94897
                            corrected_rating = 7.5  # Setze auf vernünftigen Wert
                        elif raw_rating > 100:
                            corrected_rating = min(raw_rating / 10, 10.0)  # Teile durch 10
                        elif raw_rating > 10:
                            corrected_rating = min(raw_rating / 10, 10.0)  # Teile durch 10
                        elif raw_rating < 1:
                            corrected_rating = 6.5  # Standard-Rating für unbekannte Filme
                        else:
                            corrected_rating = min(raw_rating, 10.0)  # Maximal 10.0

                        # Füge den Film zur Datenbank hinzu
                        ai_movie = Movie(
                            title=movie_data['title'],
                            release_year=int(movie_data['year']) if movie_data.get('year') else None,
                            director=movie_data.get('director', 'Unknown'),
                            genre=movie_data.get('genre', 'Drama'),
                            plot=movie_data.get('plot', f"Ein Film aus dem Jahr {movie_data.get('year', 'unbekannt')}."),
                            poster_url=movie_data.get('poster'),
                            rating=corrected_rating,  # Verwende das korrigierte Rating
                            country=movie_data.get('country')
                        )
                        session.add(ai_movie)
                        session.commit()

                        app.logger.info(f"KI-Film hinzugefügt: {movie_data['title']} mit korrigiertem Rating {corrected_rating} (original: {raw_rating})")

                    ai_recommendations = [{'movie': ai_movie, 'reason': reason}]
                else:
                    ai_recommendations = []
        except Exception as e:
            app.logger.error(f"Fehler bei KI-Empfehlung: {str(e)}")
            ai_recommendations = []

        # Füge Quiz-Historie für den aktuellen Film hinzu (korrigiert)
        quiz_history = None
        if current_user.is_authenticated:
            # Zeige die letzten Quiz-Versuche für diesen speziellen Film
            quiz_history = session.query(QuizAttempt).filter_by(
                user_id=current_user.id,
                movie_id=movie_id
            ).order_by(QuizAttempt.completed_at.desc()).limit(5).all()

            quiz_history = [{
                'date': attempt.completed_at.strftime('%d.%m.%Y'),
                'score': attempt.score,
                'progress': (attempt.score / attempt.total_questions * 100) if attempt.total_questions > 0 else 0
            } for attempt in quiz_history]

        return render_template('movie_details.html',
                            movie=movie,
                            reviews=reviews,
                            stats=stats,
                            quiz_history=quiz_history,
                            similar_movies=similar_movies,
                            ai_recommendations=ai_recommendations)


@app.route('/users/<user_id>/delete/<movie_id>', methods=["GET", "POST"])
def delete_user_movie(user_id, movie_id):
    if request.method == "GET":
        chosen_user = data_manager.get_user(user_id)
        movie = data_manager.get_movie(movie_id)
        user_movie = data_manager.get_user_movie(user_id, movie_id)
        return render_template("user_movie.html", user_movie=user_movie,
                               user=chosen_user, movie=movie)
    elif request.method == "POST":
        deleted = data_manager.delete_user_movie(user_id, movie_id)
        chosen_user = data_manager.get_user(user_id)
        movie = data_manager.get_movie(movie_id)
        user_movies_list = data_manager.get_user_movies(user_id)
        return render_template("user_movies.html", user_movies=user_movies_list,
                               user=chosen_user, movie=movie, movie_deleted=deleted)


@app.route('/users/<user_id>/recommend_movie', methods=['GET', 'POST'])
def recommendation(user_id):
    with data_manager.SessionFactory() as session:
        user = session.get(User, user_id)
        if not user:
            flash('Benutzer nicht gefunden', 'error')
            return redirect(url_for('home'))

        if request.method == "POST":
            if not request.form.get('genre_preference'):
                flash('Bitte wählen Sie ein Genre aus', 'error')
                return render_template('recommend.html', user=user)

            genre_preference = request.form.get('genre_preference')
            query = session.query(Movie)

            if 'Action & Spannung' in genre_preference:
                query = query.filter(
                    Movie.genre.ilike('%action%') |
                    Movie.genre.ilike('%thriller%') |
                    Movie.genre.ilike('%adventure%') |
                    Movie.genre.ilike('%sci-fi%')
                ).order_by(func.random())
            elif 'Drama & Gefühl' in genre_preference:
                query = query.filter(
                    Movie.genre.ilike('%drama%') |
                    Movie.genre.ilike('%romance%')
                ).order_by(func.random())
            elif 'Comedy & Humor' in genre_preference:
                query = query.filter(
                    Movie.genre.ilike('%comedy%')
                ).order_by(func.random())
            elif 'Horror & Mystery' in genre_preference:
                query = query.filter(
                    Movie.genre.ilike('%horror%') |
                    Movie.genre.ilike('%mystery%') |
                    (Movie.genre.ilike('%thriller%') &
                     ~Movie.genre.ilike('%action%') &
                     ~Movie.genre.ilike('%comedy%')) |
                    Movie.genre.ilike('%suspense%')
                ).order_by(func.random())

            movies = query.limit(5).all()

            if not movies:
                flash('Leider wurden keine passenden Filme gefunden.', 'warning')
                return render_template('recommend.html', user=user)

            return render_template('recommend.html',
                                user=user,
                                recommended_movies=movies)

        # GET request
        return render_template('recommend.html', user=user)


@app.route('/quiz')
@login_required
def quiz_home():
    """Zeigt die Quiz-Startseite mit verfügbaren und gespielten Quizzen."""
    try:
        with data_manager.SessionFactory() as session:
            # Lade alle Filme
            all_movies = session.query(Movie).all()

            # Da QuizAttempt keine movie_id mehr hat, können wir keine gespielten Quizze nach Filmen filtern
            # Alle Filme sind verfügbar für Quizze
            available_movies = all_movies
            played_quizzes = []  # Leere Liste, da wir keine Film-spezifischen Quiz-Versuche mehr haben

            # Statistiken des Benutzers laden
            user_stats = {}
            if current_user.is_authenticated:
                total_attempts = session.query(func.count(QuizAttempt.id)).filter(
                    QuizAttempt.user_id == current_user.id
                ).scalar()

                best_score = session.query(func.max(QuizAttempt.score)).filter(
                    QuizAttempt.user_id == current_user.id
                ).scalar() or 0

                avg_score = session.query(func.avg(QuizAttempt.score)).filter(
                    QuizAttempt.user_id == current_user.id
                ).scalar() or 0

                user_stats = {
                    'total_attempts': total_attempts,
                    'best_score': best_score,
                    'avg_score': avg_score
                }

            return render_template('quiz_home.html',
                                 available_movies=available_movies,
                                 played_movies=played_quizzes,
                                 user_stats=user_stats)
    except Exception as e:
        app.logger.error(f"Fehler bei der Anzeige der Quiz-Startseite: {str(e)}")
        flash('Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.', 'error')
        return redirect(url_for('home'))


@app.route('/quiz/<movie_id>')
@login_required
def movie_quiz(movie_id):
    """Startet ein Quiz für einen bestimmten Film."""
    try:
        with data_manager.SessionFactory() as session:
            movie = session.get(Movie, movie_id)
            if not movie:
                flash('Film nicht gefunden.', 'error')
                return redirect(url_for('quiz_home'))

            difficulty = request.args.get('difficulty', None)

            # Wenn keine Schwierigkeit ausgewählt wurde, zeige die Schwierigkeitsauswahl
            if not difficulty:
                return render_template('quiz.html',
                                   movie=movie,
                                   questions=None,
                                   show_difficulty_selection=True)

            quiz_service = QuizService(data_manager)
            questions = quiz_service.get_questions_for_movie(movie_id, difficulty=difficulty)

            if not questions:
                flash('Keine Fragen für diesen Film verfügbar.', 'warning')
                return redirect(url_for('quiz_home'))

            return render_template('quiz.html',
                               movie=movie,
                               questions=questions,
                               show_difficulty_selection=False,
                               difficulty=difficulty)
    except Exception as e:
        app.logger.error(f"Fehler beim Laden des Quiz: {str(e)}")
        flash('Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.', 'error')
        return redirect(url_for('quiz_home'))


@app.route('/quiz/<int:movie_id>/submit', methods=['POST'])
@login_required
@csrf.exempt
def submit_quiz(movie_id):
    """Verarbeitet die Quiz-Antworten und speichert das Ergebnis."""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type muss application/json sein'}), 400

        data = request.get_json()

        if not data or not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'Ungültige Daten'}), 400

        if 'answers' not in data or 'difficulty' not in data:
            return jsonify({'success': False, 'error': 'Antworten oder Schwierigkeitsgrad fehlen'}), 400

        with data_manager.SessionFactory() as session:
            # Berechne die Punktzahl und hole die detaillierten Ergebnisse
            quiz_service = QuizService(data_manager)
            result = quiz_service.calculate_score(
                movie_id=movie_id,
                answers=data['answers'],
                difficulty=data['difficulty']
            )

            # Speichere den Quiz-Versuch mit movie_id
            quiz_attempt = QuizAttempt(
                user_id=current_user.id,
                movie_id=movie_id,  # Füge movie_id hinzu für film-spezifische Statistiken
                score=result['score'],
                total_questions=result['total_questions'],
                difficulty=data['difficulty'],
                completed_at=datetime.now(UTC)
            )
            session.add(quiz_attempt)
            session.commit()

            # Achievement Service initialisieren und Achievements prüfen
            achievement_service = AchievementService(data_manager)
            new_achievements = achievement_service.check_quiz_achievements(current_user.id, result['score'], data['difficulty'])
            achievements_list = new_achievements  # Direkt übernehmen, da schon Dicts

            # Stelle sicher, dass alle Änderungen gespeichert sind
            session.commit()

            # Gib die vollständigen Ergebnisse zurück
            return jsonify({
                'success': True,
                'score': result['score'],
                'correct_count': result['correct_count'],
                'total_questions': result['total_questions'],
                'question_results': result.get('question_results', []),
                'answered_questions': result.get('answered_questions', []),
                'achievements': achievements_list,
                'difficulty': data['difficulty']
            })

    except Exception as e:
        app.logger.error(f"Fehler beim Quiz-Submit: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/quiz/suggest', methods=['GET', 'POST'])
@login_required
def suggest_question():
    """Ermöglicht Benutzern, neue Quizfragen vorzuschlagen."""
    if request.method == 'POST':
        movie_id = request.form.get('movie_id')
        question_text = request.form.get('question')
        correct_answer = request.form.get('correct_answer')
        wrong_answers = [
            request.form.get('wrong_answer1'),
            request.form.get('wrong_answer2'),
            request.form.get('wrong_answer3')
        ]

        if not all([movie_id, question_text, correct_answer] + wrong_answers):
            flash('Bitte fülle alle Felder aus.', 'error')
            return redirect(url_for('suggest_question'))

        with data_manager.SessionFactory() as session:
            suggestion = SuggestedQuestion(
                user_id=current_user.id,
                movie_id=movie_id,
                question_text=question_text,
                correct_answer=correct_answer,
                wrong_answer_1=wrong_answers[0],
                wrong_answer_2=wrong_answers[1],
                wrong_answer_3=wrong_answers[2],
                status='pending'
            )
            session.add(suggestion)
            session.commit()

            flash('Vielen Dank für deinen Vorschlag! Er wird ��berprüft.', 'success')
            return redirect(url_for('quiz_home'))

    with data_manager.SessionFactory() as session:
        movies = session.query(Movie).order_by(Movie.title).all()
        return render_template('suggest_question.html', movies=movies)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Bitte geben Sie E-Mail und Passwort ein.', 'error')
            return render_template('auth/login.html')

        try:
            user = auth_service.authenticate_user(email, password)
            if user:
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                flash('Erfolgreich angemeldet!', 'success')
                return redirect(next_page or url_for('home'))
            else:
                app.logger.warning(f'Fehlgeschlagener Login-Versuch für E-Mail: {email}')
                flash('Ungültige E-Mail oder Passwort.', 'error')
        except Exception as e:
            app.logger.error(f'Fehler beim Login: {str(e)}')
            flash('Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.', 'error')

    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validiere die Eingaben
        if not all([username, email, password, confirm_password]):
            flash('Bitte fülle alle Felder aus.', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwörter stimmen nicht überein.', 'error')
            return render_template('auth/register.html')

        try:
            user = auth_service.register_user(username, email, password)
            if user:
                login_user(user)
                flash('Registrierung erfolgreich!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Benutzername oder E-Mail bereits vergeben.', 'error')
                return render_template('auth/register.html')
        except Exception as e:
            flash(f'Fehler bei der Registrierung: {str(e)}', 'error')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/profile')
@login_required
def profile():
    with data_manager.SessionFactory() as session:
        user = session.get(User, current_user.id, options=[
            joinedload(User.reviews),
            joinedload(User.watchlist_items),
            joinedload(User.quiz_attempts),
            joinedload(User.achievements)
        ])

        # Berechne Benutzerstatistiken
        if not user:
            flash('Benutzer nicht gefunden.', 'error')
            return redirect(url_for('home'))

        # Hole die Anzahl der Reviews, Watchlist-Items, Quiz-Versuche und Achievements
        if not user.reviews:
            user.reviews = []

        if not user.watchlist_items:
            user.watchlist_items = []

        if not user.quiz_attempts:
            user.quiz_attempts = []

        if not user.achievements:
            user.achievements = []

        # Berechne die Statistiken
        with data_manager.SessionFactory() as session:
            user.reviews_count = len(user.reviews)
            user.watchlist_count = len(user.watchlist_items)
            user.quiz_attempts_count = len(user.quiz_attempts)
            user.achievements_count = len(user.achievements)
        user_stats = {
            'reviews_count': len(user.reviews),
            'watchlist_count': len(user.watchlist_items),
            'quiz_attempts': len(user.quiz_attempts),
            'achievements_count': len(user.achievements),
            'avg_rating': session.query(func.avg(Review.rating)).filter_by(user_id=user.id).scalar() or 0
        }

        return render_template('profile.html',
                            user=user,
                            user_stats=user_stats)


@app.route('/profile/settings', methods=['POST'])
@login_required
def update_settings():
    theme = request.form.get('theme', 'system')
    notifications = request.form.get('notifications') == 'on'

    with data_manager.SessionFactory() as session:
        user = session.get(User, current_user.id)
        if user:
            user.theme = theme
            user.email_notifications = notifications
            session.commit()
            flash('Einstellungen wurden aktualisiert.', 'success')

    return redirect(url_for('profile'))


@app.route('/watchlist/add/<int:movie_id>', methods=['POST'])
@login_required
def add_to_watchlist(movie_id):
    """Fügt einen Film zur Watchlist hinzu."""
    try:
        item = watchlist_service.add_to_watchlist(current_user.id, movie_id)
        # Film wurde erfolgreich hinzugefügt oder war bereits in der Watchlist
        if not item:
            flash('Film ist bereits in deiner Watchlist.', 'info')
        else:
            flash('Film wurde zur Watchlist hinzugefügt.', 'success')

            # Achievement Service für Watchlist-Achievements
            achievement_service = AchievementService(data_manager)
            new_achievements = achievement_service.check_watchlist_achievements(current_user.id)

            # Zeige Achievement-Benachrichtigungen an
            if new_achievements:
                for achievement in new_achievements:
                    flash(f"🏆 Achievement freigeschaltet: {achievement['title']} - {achievement['description']}", 'success')

    except Exception as e:
        # Nur für echte Fehler eine Fehlermeldung anzeigen
        app.logger.error(f"Watchlist-Fehler: {str(e)}")
        flash(str(e), 'error')

    # Zurück zur vorherigen Seite oder zur Watchlist
    return redirect(request.referrer or url_for('watchlist'))


@app.route('/watchlist', methods=['GET'])
@login_required
def watchlist():
    """Zeigt die Watchlist des eingeloggten Benutzers."""
    try:
        items = watchlist_service.get_watchlist(current_user.id)
        return render_template('watchlist.html', watchlist=items)
    except Exception as e:
        flash('Fehler beim Laden der Watchlist.', 'error')
        app.logger.error(f"Watchlist-Fehler: {str(e)}")
        return redirect(url_for('home'))


@app.route('/watchlist/remove/<int:movie_id>', methods=['POST'])
@login_required
def remove_from_watchlist(movie_id):
    """Entfernt einen Film von der Watchlist."""
    try:
        if watchlist_service.remove_from_watchlist(current_user.id, movie_id):
            flash('Film wurde von der Watchlist entfernt.', 'success')
        else:
            flash('Film konnte nicht gefunden werden.', 'error')
    except Exception as e:
        flash('Fehler beim Entfernen von der Watchlist.', 'error')
        app.logger.error(f"Watchlist-Fehler: {str(e)}")

    return redirect(request.referrer or url_for('watchlist'))


@app.route('/achievements')
@login_required
def achievements():
    """Zeigt die Achievements des eingeloggten Benutzers."""
    with data_manager.SessionFactory() as session:
        user = session.get(User, current_user.id, options=[
            joinedload(User.achievements)
        ])

        # Hole alle verfügbaren Achievements
        all_achievements = session.query(Achievement).all()
        unlocked_ids = {a.id for a in user.achievements}
        locked_achievements = [a for a in all_achievements if a.id not in unlocked_ids]

        return render_template('achievements.html',
                           unlocked=user.achievements,
                           locked=locked_achievements)


@app.route('/movies/<int:movie_id>/recommendation/generate', methods=['POST'])
def generate_ai_recommendation(movie_id):
    """Generiert eine KI-Empfehlung für einen bestimmten Film"""
    try:
        with data_manager.SessionFactory() as session:
            movie = session.get(Movie, movie_id)
            if not movie:
                return jsonify({'error': 'Film nicht gefunden'}), 404

            # Erstelle einen detaillierten Kontext für die KI
            context = f"{movie.title}"

            # Hole die Filminformationen und Bewertungen zur Verbesserung der Empfehlung
            movie_details = {
                'title': movie.title,
                'director': movie.director,
                'genre': movie.genre,
                'year': movie.release_year,
                'plot': movie.description
            }

            # Hole Empfehlung von der KI mit verbessertem Kontext
            ai_response = ai_client.ai_request(context)

            if ai_response and 'movie' in ai_response:
                return jsonify({
                    'recommendation': {
                        'movie': {
                            'title': ai_response['movie']['title'],
                            'director': ai_response['movie']['director'],
                            'year': ai_response['movie']['year'],
                            'poster': ai_response['movie']['poster'],
                            'genre': ai_response['movie']['genre'],
                            'plot': ai_response['movie']['plot']
                        },
                        'reasoning': ai_response['reasoning']
                    }
                })
            else:
                return jsonify({'error': 'Keine Empfehlung verfügbar'}), 404

    except Exception as e:
        print(f"Fehler bei der KI-Empfehlung: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/movies/<int:movie_id>/similar', methods=['GET'])
def get_similar_movies(movie_id):
    """Gibt ähnliche Filme zurück"""
    with data_manager.SessionFactory() as session:
        movie = session.get(Movie, movie_id)
        if not movie:
            return jsonify({'error': 'Film nicht gefunden'}), 404

        # Hole ähnliche Filme basierend auf Genre und Jahr
        similar_movies = session.query(Movie).filter(
            Movie.id != movie_id,
            Movie.genre.like(f'%{movie.genre}%'),
            Movie.release_year.between(movie.release_year - 5, movie.release_year + 5)
        ).order_by(Movie.rating.desc()).limit(4).all()

        # Konvertiere die Filme in ein JSON-Format
        similar_movies_data = [{
            'id': m.id,
            'title': m.title,
            'genre': m.genre,
            'release_year': m.release_year,
            'rating': m.rating,
            'poster_url': m.poster_url
        } for m in similar_movies]

        return jsonify({'similar_movies': similar_movies_data})


@app.route('/movies/<int:movie_id>/recommendation', methods=['GET'])
def get_movie_recommendation(movie_id):
    """Gibt eine vorhandene KI-Empfehlung zurück"""
    with data_manager.SessionFactory() as session:
        movie = session.get(Movie, movie_id)
        if not movie:
            return jsonify({'error': 'Film nicht gefunden'}), 404

        # Hier könnte man gespeicherte KI-Empfehlungen abrufen
        # Für jetzt geben wir einfach einen leeren Response zurück
        return jsonify({'recommendation': None})


@app.route('/static/<path:filename>')
def serve_static(filename):
    if filename == 'default_poster.jpg':
        response = send_from_directory('static', filename)
        # Setze Cache-Control Header für das Default-Poster (1 Stunde)
        response.headers['Cache-Control'] = 'public, max-age=3600'
        return response
    return send_from_directory('static', filename)


class MovieRecommendForm(FlaskForm):
    pass


@app.route('/recommend', methods=['GET', 'POST'], endpoint='recommend')
def recommend_movies():
    form = MovieRecommendForm()  # Erstelle ein echtes FlaskForm-Objekt
    if request.method == 'POST' and form.validate():
        genre_preference = request.form.get('genre_preference', '')

        with data_manager.SessionFactory() as session:
            query = session.query(Movie)

            if 'Action & Spannung' in genre_preference:
                query = query.filter(
                    Movie.genre.ilike('%action%') |
                    Movie.genre.ilike('%thriller%') |
                    Movie.genre.ilike('%adventure%') |
                    Movie.genre.ilike('%sci-fi%')
                )
            elif 'Drama & Gefühl' in genre_preference:
                query = query.filter(
                    Movie.genre.ilike('%drama%') |
                    Movie.genre.ilike('%romance%')
                )
            elif 'Comedy & Humor' in genre_preference:
                query = query.filter(
                    Movie.genre.ilike('%comedy%') |
                    Movie.genre.ilike('%romance comedy%')
                )
            elif 'Horror & Mystery' in genre_preference:
                query = query.filter(
                    Movie.genre.ilike('%horror%') |
                    Movie.genre.ilike('%mystery%') |
                    (Movie.genre.ilike('%thriller%') & ~Movie.genre.ilike('%action%')) |
                    Movie.genre.ilike('%suspense%')
                )

            # Hole mehr Filme und mische sie für Vielfalt
            movies = query.order_by(
                Movie.rating.desc(),
                Movie.release_year.desc()
            ).limit(20).all()

            if not movies:
                flash('Leider wurden keine passenden Filme gefunden.', 'warning')
                return render_template('movie_recommend.html', form=form)

            # Mische die Filme und nimm die ersten 5
            random.shuffle(movies)
            recommended_movies = movies[:5]

            reason = f"Diese Filme wurden basierend auf Ihrer Vorliebe für {genre_preference} ausgewählt."

            return render_template('movie_recommend.html',
                                 recommended_movies=recommended_movies,
                                 reason=reason,
                                 genre_preference=genre_preference,
                                 form=form)

    return render_template('movie_recommend.html', form=form)


@app.route('/api/movies', methods=['GET'])
def api_movies():
    """
    API Endpoint für React Frontend - Optimiert mit Pagination
    """
    try:
        search_query = request.args.get('search', '').strip()
        genre_filter = request.args.get('genre', '').strip()
        sort_by = request.args.get('sort', 'rating')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))  # React kann mehr laden

        # Optimierte Query mit SELECT nur benötigter Felder
        query = data_manager.session.query(
            Movie.id,
            Movie.title,
            Movie.genre,
            Movie.rating,
            Movie.release_year,
            Movie.poster_url,
            Movie.director,
            Movie.summary
        )

        # Search filter (optimiert)
        if search_query:
            query = query.filter(
                func.lower(Movie.title).contains(search_query.lower()) |
                func.lower(Movie.genre).contains(search_query.lower())
            )

        # Genre filter (optimiert)
        if genre_filter:
            query = query.filter(Movie.genre == genre_filter)

        # Sorting (mit Indizes optimiert)
        if sort_by == 'title':
            query = query.order_by(Movie.title)
        elif sort_by == 'year_desc':
            query = query.order_by(Movie.release_year.desc().nulls_last())
        elif sort_by == 'year_asc':
            query = query.order_by(Movie.release_year.asc().nulls_last())
        else:  # rating (default)
            query = query.order_by(Movie.rating.desc().nulls_last())

        # Pagination
        total_movies = query.count()
        movies = query.offset((page - 1) * per_page).limit(per_page).all()

        # Convert to JSON-serializable format
        movies_data = []
        for movie in movies:
            movies_data.append({
                'id': movie.id,
                'title': movie.title,
                'genre': movie.genre,
                'year': movie.release_year,
                'rating': float(movie.rating) if movie.rating else None,
                'poster_url': movie.poster_url or '/static/default_poster.jpg',
                'director': movie.director,
                'summary': movie.summary
            })

        return jsonify({
            'success': True,
            'movies': movies_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_movies,
                'total_pages': (total_movies + per_page - 1) // per_page
            },
            'filters': {
                'search': search_query,
                'genre': genre_filter,
                'sort': sort_by
            }
        })

    except Exception as e:
        app.logger.error(f"API Movies Error: {e}")
        return jsonify({
            'success': False,
            'error': 'Fehler beim Laden der Filme',
            'movies': []
        }), 500


@app.route('/api/genres', methods=['GET'])
def api_genres():
    """
    API Endpoint für verfügbare Genres
    """
    try:
        genres = data_manager.session.query(Movie.genre).distinct().filter(Movie.genre.isnot(None)).all()
        genre_list = [genre[0] for genre in genres if genre[0]]

        return jsonify({
            'success': True,
            'genres': sorted(genre_list)
        })

    except Exception as e:
        app.logger.error(f"API Genres Error: {e}")
        return jsonify({
            'success': False,
            'error': 'Fehler beim Laden der Genres',
            'genres': []
        }), 500


@app.route('/api/movie/<int:movie_id>', methods=['GET'])
def api_movie_detail(movie_id):
    """
    API Endpoint für einzelne Filmdetails
    """
    try:
        movie = data_manager.session.query(Movie).filter_by(id=movie_id).first()

        if not movie:
            return jsonify({
                'success': False,
                'error': 'Film nicht gefunden'
            }), 404

        # Get user rating if logged in
        user_rating = None
        if current_user.is_authenticated:
            user_movie = data_manager.session.query(UserMovie).filter_by(
                user_id=current_user.id,
                movie_id=movie_id
            ).first()
            if user_movie:
                user_rating = user_movie.user_rating

        movie_data = {
            'id': movie.id,
            'title': movie.title,
            'genre': movie.genre,
            'year': movie.year,
            'rating': float(movie.rating) if movie.rating else None,
            'poster_url': movie.poster_url or '/static/default_poster.jpg',
            'director': movie.director,
            'summary': movie.summary,
            'user_rating': user_rating
        }

        return jsonify({
            'success': True,
            'movie': movie_data
        })

    except Exception as e:
        app.logger.error(f"API Movie Detail Error: {e}")
        return jsonify({
            'success': False,
            'error': 'Fehler beim Laden der Filmdetails'
        }), 500


@app.route('/movies/react')
def react_movies():
    """React-basierte Movie-App mit moderner Frontend-Technologie"""
    return render_template('react_movies.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)
