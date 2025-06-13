"""
MovieProjekt Flask App
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import joinedload
import random
from datetime import datetime, timedelta

from ai_request import AIRequest
from datamanager.sqlite_data_manager import SQliteDataManager
from data_models import User, Movie, UserMovie, SuggestedQuestion, Review, WatchlistItem, QuizAttempt, UserAchievement
from movie_api import OMDBClient
from services.quiz_service import QuizService
from services.auth_service import AuthService, init_login_manager
from services.watchlist_service import WatchlistService
from services.achievement_service import AchievementService
from services.movie_update_service import MovieUpdateService

app = Flask(__name__)
app.config.update(
    ENV='development',
    DEBUG=True,
    SECRET_KEY='dein-geheimer-schluessel'
)

# Füge den shuffle-Filter zu Jinja2 hinzu
def jinja2_shuffle(seq):
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq
app.jinja_env.filters['shuffle'] = jinja2_shuffle

data_manager = SQliteDataManager("sqlite:///movie_app.db")
ai_client = AIRequest()
login_manager = init_login_manager(app)
movie_update_service = MovieUpdateService(data_manager)

def update_movies():
    """Aktualisiert die Filmdatenbank mit neuen Filmen"""
    return movie_update_service.update_movie_database()

# Initialisiere die Datenbank beim Start
with app.app_context():
    update_movies()

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


# Home Route with simple navigation
@app.route('/')
def home():
    """
    Render the home page with movie and user statistics.
    """
    update_movies()
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


# Users in a list view
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


# User movies in a list view
@app.route('/users/<user_id>', methods=["GET", "POST"])
def user_movies(user_id):
    if request.method == "GET":
        chosen_user = data_manager.get_user(user_id)
        user_movies_list = data_manager.get_user_movies(user_id)
        return render_template("user_movies.html", user_movies=user_movies_list,
                    user=chosen_user)
    elif request.method == "POST":
        chosen_user = data_manager.get_user(user_id)
        movie_title = request.form["name"]
        with data_manager.SessionFactory() as session:
            movie = session.query(Movie).filter_by(name=movie_title).first()
            if movie is None:
                try:
                    movie = data_manager.set_movie(movie_title)
                    if movie is None:
                        raise Exception("Movie not found")
                    data_manager.set_user_movies(user_id=user_id, movie_id=movie.id)
                    user_movies_list = data_manager.get_user_movies(user_id)
                    return render_template("user_movies.html",
                                           user_movies=user_movies_list,
                                           user=chosen_user, success=True)
                except Exception as e:
                    session.rollback()
                    user_movies_list = data_manager.get_user_movies(user_id)
                    return render_template("user_movies.html",
                                           user_movies=user_movies_list,
                                           user=chosen_user, success=False, error=e)
            else:
                if data_manager.get_user_movie(user_id, movie.id):
                    return render_template("user_movies.html",
                                           user_movies=data_manager.get_user_movies(user_id),
                                           user=chosen_user, success=False,
                                           error="Movie already exists")
                try:
                    data_manager.set_user_movies(user_id=user_id, movie_id=movie.id)
                    user_movies_list = data_manager.get_user_movies(user_id)
                    return render_template("user_movies.html",
                                           user_movies=user_movies_list,
                                           user=chosen_user, success=True)
                except Exception as e:
                    session.rollback()
                    return render_template("user_movies.html",
                                           user_movies=data_manager.get_user_movies(user_id),
                                           user=chosen_user, success=False, error=e)


# single user movie view for updating
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
        user_rating = request.form["user_rating"]
        user_comment = request.form["user_comment"] if "user_comment" in request.form else None
        try:
            data_manager.update_user_movie(user_id=user_id, movie_id=movie_id,
                                           update_data={"user_rating": user_rating,
                                                        "user_comment": user_comment})
            new_user_movie = data_manager.get_user_movie(user_id, movie_id)
            return render_template("user_movie.html", user_movie=new_user_movie,
                                   user=chosen_user, movie=movie, success=True)
        except Exception as e:
            return render_template("user_movie.html", user_movie=user_movie,
                                   user=chosen_user, movie=movie, success=False, error=e)


# Adding new users
@app.route('/users/new', methods=["GET", "POST"])
def new_user():
    if request.method == "GET":
        return render_template("new_user.html")
    elif request.method == "POST":
        name = request.form["name"]
        user = User(name=name)
        with data_manager.SessionFactory() as session:
            try:
                session.add(user)
                session.commit()
                return render_template("new_user.html", success=True)
            except Exception as e:
                session.rollback()
                return render_template("new_user.html", success=False, error=e)


# Adding new movies
@app.route('/movies/new', methods=["GET", "POST"])
def new_movie():
    if request.method == "GET":
        return render_template("new_movie.html")
    elif request.method == "POST":
        title = request.form["name"]
        try:
            with data_manager.SessionFactory() as session:
                movie = data_manager.set_movie(title)
                if movie is None:
                    flash('Film konnte nicht gefunden werden: ' + title, 'error')
                    return render_template("new_movie.html", success=False)

                # Binde das Movie-Objekt an die aktuelle Session
                movie = session.merge(movie)
                session.refresh(movie)
                flash(f'Film "{movie.title}" wurde erfolgreich hinzugefügt!', 'success')
                return render_template("new_movie.html", success=True)

        except Exception as e:
            flash('Ein Fehler ist aufgetreten beim Hinzufügen des Films. Bitte versuchen Sie es erneut.', 'error')
            return render_template("new_movie.html", success=False)


# see list of all movies in database
@app.route('/movies', methods=["GET", "POST"])
def list_movies():
    if request.method == "GET":
        with data_manager.SessionFactory() as session:
            # Sortiere die Filme nach Rating (absteigend)
            movies = session.query(Movie).order_by(Movie.rating.desc()).all()
            return render_template("movies.html", movies=movies)
    elif request.method == "POST":
        movie_id = request.form["movie_id"]
        with data_manager.SessionFactory() as session:
            deleted = data_manager.delete_movie(int(movie_id))
            # Nach Löschen auch sortiert zurückgeben
            movies = session.query(Movie).order_by(Movie.rating.desc()).all()
            return render_template("movies.html", movies=movies, success=deleted)


# get details of a single movie
@app.route('/movies/<movie_id>', methods=["GET", "POST"])
def movie_details(movie_id):
    if request.method == "GET":
        with data_manager.SessionFactory() as session:
            movie = session.query(Movie).get(movie_id)
            if not movie:
                return render_template("404.html"), 404

            # Basis-Statistiken initialisieren
            stats = {
                'quiz_attempts': 0,
                'avg_score': 0,
                'completion_rate': 0
            }

            # Quiz-Historie initialisieren
            quiz_history = []

            if current_user.is_authenticated:
                # Prüfe, ob Film in der Watchlist ist
                watchlist_item = session.query(WatchlistItem).filter_by(
                    user_id=current_user.id,
                    movie_id=movie_id
                ).first()
                movie.in_watchlist = watchlist_item is not None

                # Quiz-Statistiken laden
                quiz_attempts = session.query(QuizAttempt).filter_by(
                    movie_id=movie_id
                ).all()

                if quiz_attempts:
                    stats['quiz_attempts'] = len(quiz_attempts)
                    total_score = sum(attempt.score for attempt in quiz_attempts)
                    stats['avg_score'] = round(total_score / len(quiz_attempts), 1)
                    completed = sum(1 for attempt in quiz_attempts if attempt.score >= 70)
                    stats['completion_rate'] = round((completed / len(quiz_attempts)) * 100)

                # Persönliche Quiz-Historie
                user_attempts = session.query(QuizAttempt).filter_by(
                    user_id=current_user.id,
                    movie_id=movie_id
                ).order_by(QuizAttempt.created_at.desc()).all()

                quiz_history = [{
                    'date': attempt.created_at.strftime('%d.%m.%Y'),
                    'score': attempt.score,
                    'progress': attempt.score
                } for attempt in user_attempts]

            return render_template(
                "movie_details.html",
                movie=movie,
                stats=stats,
                quiz_history=quiz_history
            )
    elif request.method == "POST":
        movie_id = request.form["movie_id"]
        with data_manager.SessionFactory() as session:
            deleted = data_manager.delete_movie(int(movie_id))
            movies = session.query(Movie).order_by(Movie.rating.desc()).all()
            return render_template("movies.html", movies=movies, success=deleted)

# delete user movie from database
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


# movie recommendation from AI
@app.route('/users/<user_id>/recommend_movie', methods=["GET", "POST"])
def recommendation(user_id):
    if request.method == "GET":
        chosen = data_manager.get_user(user_id)
        return render_template("recommend.html", user=chosen)
    elif request.method == "POST":
        chosen = data_manager.get_user(user_id)
        data_string = ""
        for movie in data_manager.get_user_movies(user_id):
            data_string += f"Title: {movie['name']} User Rating: {movie['user_rating']},"

        if "name" in request.form:
            # Wenn ein Film ausgeschlossen werden soll
            excluded_movie = request.form["name"]
            recommendation = ai_client.ai_excluded_movie_request(data_string, excluded_movie)
        else:
            # Normale Empfehlung ohne Ausschluss
            recommendation = ai_client.ai_request(data_string)

        if recommendation:
            movie = data_manager.set_movie(recommendation["movie"]["title"])
            if movie:
                data_manager.set_user_movies(user_id, movie.id)
                return render_template("recommend.html", user=chosen,
                                    recommendation=recommendation["movie"],
                                    reasoning=recommendation["reasoning"])

        # Wenn keine Empfehlung gefunden wurde oder der Film nicht hinzugefügt werden konnte
        return render_template("recommend.html", user=chosen, error="Keine passende Filmempfehlung gefunden")


# API Route für Film-Empfehlungen
@app.route('/api/recommendations/<movie_id>', methods=['GET'])
def get_movie_recommendations(movie_id):
    try:
        # Hole den Film aus der Datenbank
        movie = data_manager.get_movie(movie_id)
        if not movie:
            return jsonify({'error': 'Film nicht gefunden'}), 404

        # Erstelle einen String mit den Film-Daten für die AI
        data_string = f"Title: {movie.name}, Genre: {movie.genre}, Year: {movie.year}, Rating: {movie.rating},"
        
        # Hole eine Empfehlung von der AI
        recommendation = AIRequest().ai_excluded_movie_request(data_string, movie.name)
        
        # Hole zusätzliche Informationen (Poster und IMDB-Rating) für den empfohlenen Film
        poster = OMDBClient().get_movie(recommendation["movie"]["title"])
        recommendation["movie"]["poster"] = poster["poster"]
        recommendation["movie"]["imdb"] = poster["rating"]
        
        # Sende die Empfehlung als JSON zurück
        return jsonify(recommendation)
    except Exception as e:
        # Bei einem Fehler sende eine Fehlermeldung zurück
        return jsonify({'error': str(e)}), 500


# Quiz Routes
@app.route('/quiz')
def quiz_home():
    """Zeigt die Quiz-Übersichtsseite mit verfügbaren Quizzen."""
    with data_manager.SessionFactory() as session:
        quiz_service = QuizService(session)
        available_quizzes = quiz_service.get_available_quizzes()
        recent_highscores = quiz_service.get_recent_highscores(limit=5)
        user_stats = None
        if current_user.is_authenticated:
            user_stats = quiz_service.get_user_quiz_stats(current_user.id)

    return render_template(
        "quiz_home.html",
        quizzes=available_quizzes,
        highscores=recent_highscores,
        user_stats=user_stats
    )

@app.route('/movies/<movie_id>/quiz', methods=['GET'])
def movie_quiz(movie_id):
    """Zeigt ein Quiz für einen bestimmten Film an."""
    with data_manager.SessionFactory() as session:
        movie = session.get(Movie, movie_id)
        if not movie:
            return render_template("404.html"), 404

        quiz_service = QuizService(session)
        if current_user.is_authenticated:
            quiz_service.current_user = current_user
        questions = quiz_service.get_movie_questions(movie_id)
        if not questions:
            questions = quiz_service.generate_questions(movie_id)

        highscores = quiz_service.get_highscores(movie_id)
        user_achievements = []
        if current_user.is_authenticated:
            user_achievements = quiz_service.get_user_achievements(current_user.id)

        return render_template(
            "quiz.html",
            movie=movie,
            questions=questions,
            highscores=highscores,
            achievements=user_achievements
        )

@app.route('/movies/<movie_id>/quiz/submit', methods=['POST'])
@login_required
def submit_quiz(movie_id):
    """Verarbeitet die Antworten eines Quiz-Versuchs."""
    if not request.is_json:
        return jsonify({"error": "Content-Type muss application/json sein"}), 400

    data = request.get_json()
    user_id = current_user.id
    answers = data.get('answers', {})
    score = data.get('score', 0)

    with data_manager.SessionFactory() as session:
        quiz_service = QuizService(session)
        attempt, earned_achievements = quiz_service.submit_quiz_attempt(
            user_id=user_id,
            movie_id=movie_id,
            answers=answers,
            score=score
        )

        # Formatiere die Achievements für die JSON-Antwort
        achievement_data = [{
            'title': a.title,
            'description': a.description,
            'icon_url': a.icon_url
        } for a in earned_achievements]

        return jsonify({
            'success': True,
            'score': attempt.score,
            'correct_count': attempt.correct_count,
            'earned_achievements': achievement_data
        })

@app.route('/movies/<movie_id>/quiz/suggest', methods=['GET', 'POST'])
def suggest_question(movie_id):
    """Erlaubt Benutzern, eigene Quiz-Fragen vorzuschlagen."""
    movie = data_manager.get_movie(movie_id)
    if not movie:
        return render_template("404.html"), 404

    if request.method == 'POST':
        data = request.form.to_dict()
        user_id = data.get('user_id')

        # Validiere die vorgeschlagene Frage mit KI
        validation = AIRequest().validate_user_question(data)

        if validation['is_valid']:
            with data_manager.SessionFactory() as session:
                question = SuggestedQuestion(
                    user_id=user_id,
                    movie_id=movie_id,
                    question_text=data['question_text'],
                    correct_answer=data['correct_answer'],
                    wrong_answer_1=data['wrong_answer_1'],
                    wrong_answer_2=data['wrong_answer_2'],
                    wrong_answer_3=data['wrong_answer_3']
                )
                session.add(question)
                session.commit()

            return render_template(
                "suggest_question.html",
                movie=movie,
                success=True,
                message="Danke für deinen Vorschlag!"
            )
        else:
            return render_template(
                "suggest_question.html",
                movie=movie,
                error=True,
                feedback=validation['feedback']
            )

    return render_template("suggest_question.html", movie=movie)

# Auth Routes
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        with data_manager.SessionFactory() as session:
            auth_service = AuthService(session)
            user = auth_service.authenticate_user(email, password)

            if user:
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))
            else:
                flash('Ungültige Email oder Passwort', 'error')

    return render_template('auth/login.html')

@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        with data_manager.SessionFactory() as session:
            auth_service = AuthService(session)
            user = auth_service.register_user(username, email, password)

            if user:
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('Registrierung fehlgeschlagen. Email oder Benutzername bereits vergeben.', 'error')

    return render_template('auth/register.html')

@app.route('/auth/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Geschützte Routen with @login_required
@app.route('/profile')
@login_required
def profile():
    """Zeigt die Profilseite des eingeloggten Benutzers an."""
    with data_manager.SessionFactory() as session:
        # Binde den aktuellen Benutzer an die Session und lade alle Beziehungen
        user = session.merge(current_user)
        session.refresh(user)  # Aktualisiere den User-Objekt mit allen Beziehungen

        # Lade die Statistiken mit expliziten Abfragen
        achievements = session.query(UserAchievement).filter_by(user_id=user.id).all()
        user_stats = {
            'reviews_count': session.query(Review).filter_by(user_id=user.id).count(),
            'watchlist_count': session.query(WatchlistItem).filter_by(user_id=user.id).count(),
            'quiz_attempts_count': session.query(QuizAttempt).filter_by(user_id=user.id).count(),
            'achievements': achievements,
            'achievements_count': len(achievements)
        }

        return render_template('profile.html',
                            user=user,
                            user_stats=user_stats,
                            password_error=request.args.get('password_error'),
                            password_success=request.args.get('password_success'))

@app.route('/profile/password', methods=['POST'])
@login_required
def change_password():
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not all([current_password, new_password, confirm_password]):
            flash('Bitte füllen Sie alle Passwortfelder aus.', 'error')
            return redirect(url_for('profile'))

        if new_password != confirm_password:
            flash('Die Passwörter stimmen nicht überein.', 'error')
            return redirect(url_for('profile'))

        with data_manager.SessionFactory() as session:
            auth_service = AuthService(session)
            if auth_service.change_password(current_user.id, current_password, new_password):
                flash('Passwort wurde erfolgreich geändert.', 'success')
            else:
                flash('Das aktuelle Passwort ist nicht korrekt.', 'error')

        return redirect(url_for('profile'))
    except Exception as e:
        app.logger.error(f"Fehler beim Ändern des Passworts: {str(e)}")
        flash('Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.', 'error')
        return redirect(url_for('profile'))

@app.route('/profile/preferences', methods=['POST'])
@login_required
def update_preferences():
    email_notifications = request.form.get('email_notifications') == 'on'
    theme = request.form.get('theme', 'system')

    with data_manager.SessionFactory() as session:
        user = session.get(User, current_user.id)
        if user:
            user.email_notifications = email_notifications
            user.theme = theme
            session.commit()
            flash('Einstellungen wurden gespeichert.', 'success')
        else:
            flash('Benutzer nicht gefunden.', 'error')

    return redirect(url_for('profile'))

# Watchlist Routes
@app.route('/watchlist', methods=['GET'])
@login_required
def view_watchlist():
    """Zeigt die Watchlist des eingeloggten Benutzers an."""
    with data_manager.SessionFactory() as session:
        watchlist_service = WatchlistService(session)
        watchlist = watchlist_service.get_watchlist(current_user.id)
    return render_template('watchlist.html', watchlist=watchlist)

@app.route('/watchlist/add/<int:movie_id>', methods=['POST'])
@login_required
def add_to_watchlist(movie_id):
    """Fügt einen Film zur Watchlist hinzu."""
    with data_manager.SessionFactory() as session:
        watchlist_service = WatchlistService(session)
        item = watchlist_service.add_to_watchlist(current_user.id, movie_id)
        if item:
            flash('Film wurde zur Watchlist hinzugefügt!', 'success')
        else:
            flash('Film ist bereits in deiner Watchlist!', 'error')
    return redirect(request.referrer or url_for('view_watchlist'))

@app.route('/watchlist/remove/<int:movie_id>', methods=['POST'])
@login_required
def remove_from_watchlist(movie_id):
    """Entfernt einen Film aus der Watchlist."""
    with data_manager.SessionFactory() as session:
        watchlist_service = WatchlistService(session)
        if watchlist_service.remove_from_watchlist(current_user.id, movie_id):
            flash('Film wurde aus der Watchlist entfernt!', 'success')
        else:
            flash('Film konnte nicht gefunden werden!', 'error')
    return redirect(url_for('view_watchlist'))

# Achievement Routes
@app.route('/achievements')
@login_required
def view_achievements():
    """Zeigt die Achievements des eingeloggten Benutzers an."""
    with data_manager.SessionFactory() as session:
        achievement_service = AchievementService(session)
        user_achievements = achievement_service.get_user_achievements(current_user.id)
        all_achievements = achievement_service.get_available_achievements()
    return render_template(
        'achievements.html',
        user_achievements=user_achievements,
        all_achievements=all_achievements
    )


# Automatische Film-Updates
@app.route('/admin/update-movies', methods=['POST'])
@login_required
def update_movies():
    """Aktualisiert die Filmdatenbank mit neuen Filmen"""
    movie_service = MovieUpdateService(data_manager)
    try:
        movies_added = movie_service.update_movie_database()
        return jsonify({
            'success': True,
            'message': f'{movies_added} neue Filme wurden hinzugefügt'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler beim Aktualisieren: {str(e)}'
        }), 500

# Plane tägliche Updates
def schedule_movie_updates():
    """Führt tägliche Film-Updates durch"""
    with app.app_context():
        movie_service = MovieUpdateService(data_manager)
        movie_service.update_movie_database()

if __name__ == '__main__':
    # Erstelle einen Hintergrund-Thread für Updates
    import threading
    import time

    def run_scheduled_updates():
        while True:
            schedule_movie_updates()
            # Warte 24 Stunden bis zum nächsten Update
            time.sleep(24 * 60 * 60)

    update_thread = threading.Thread(target=run_scheduled_updates)
    update_thread.daemon = True
    update_thread.start()

    app.run(host='0.0.0.0', port=5002, debug=True)
