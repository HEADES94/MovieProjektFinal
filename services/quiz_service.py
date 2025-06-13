"""
quiz_service.py - Service für die Quiz-Funktionalität
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from data_models import (QuizQuestion, QuizAttempt, Highscore, Movie, User,
                        Achievement, UserAchievement)
from ai_request import AIRequest

class QuizService:
    def __init__(self, session: Session):
        self.session = session
        self.ai_client = AIRequest()
        self._init_achievements()

    def _init_achievements(self):
        """Initialisiert die Standard-Achievements falls sie noch nicht existieren."""
        default_achievements = [
            {
                'title': '🎯 Perfect Quiz',
                'description': 'Erreiche die perfekte Punktzahl in einem Quiz!',
                'icon_url': '/static/img/trophy_perfect.png'
            },
            {
                'title': '🏆 First Highscore',
                'description': 'Erreiche deinen ersten Highscore!',
                'icon_url': '/static/img/trophy_first.png'
            },
            {
                'title': '👑 Quiz Master',
                'description': 'Erreiche in 5 verschiedenen Quizzen mindestens 400 Punkte!',
                'icon_url': '/static/img/trophy_master.png'
            },
            {
                'title': '🎓 Quiz Profi',
                'description': 'Schließe ein schweres Quiz mit mindestens 1000 Punkten ab!',
                'icon_url': '/static/img/trophy_expert.png'
            },
            {
                'title': '📚 Wissensdurst',
                'description': 'Beantworte 100 Fragen korrekt!',
                'icon_url': '/static/img/trophy_knowledge.png'
            },
            {
                'title': '🎬 Film Enthusiast',
                'description': 'Schließe Quizze zu 10 verschiedenen Filmen ab!',
                'icon_url': '/static/img/trophy_movie.png'
            },
            {
                'title': '🌟 Perfektionist',
                'description': 'Erreiche 3 perfekte Quizze in Folge!',
                'icon_url': '/static/img/trophy_perfectionist.png'
            },
            {
                'title': '🔥 Streak Master',
                'description': 'Beantworte 20 Fragen in Folge richtig!',
                'icon_url': '/static/img/trophy_streak.png'
            }
        ]

        for achievement in default_achievements:
            existing = self.session.query(Achievement)\
                .filter_by(title=achievement['title'])\
                .first()
            if not existing:
                new_achievement = Achievement(**achievement)
                self.session.add(new_achievement)

        try:
            self.session.commit()
        except:
            self.session.rollback()

    def generate_questions(self, movie_id: int, count: int = 5) -> List[Dict]:
        """Generiert neue Quizfragen für einen Film mit KI-Unterstützung."""
        movie = self.session.query(Movie).get(movie_id)
        if not movie:
            raise ValueError("Film nicht gefunden")

        # Erstelle einen Kontext für die KI
        context = f"Title: {movie.title}\nPlot: {movie.plot}\nYear: {movie.release_year}\nDirector: {movie.director}"

        questions = []
        for _ in range(count):
            # KI-generierte Frage (Implementation in ai_request.py erforderlich)
            question_data = self.ai_client.generate_quiz_question(context)

            # Erstelle neue Quizfrage
            question = QuizQuestion(
                movie_id=movie_id,
                question_text=question_data["question"],
                correct_answer=question_data["correct_answer"],
                wrong_answer_1=question_data["wrong_answers"][0],
                wrong_answer_2=question_data["wrong_answers"][1],
                wrong_answer_3=question_data["wrong_answers"][2],
                source="ai"
            )
            self.session.add(question)
            questions.append(question)

        self.session.commit()
        return questions

    def get_movie_questions(self, movie_id: int, limit: int = 5) -> List[QuizQuestion]:
        """Holt existierende Quizfragen für einen Film, vermeidet Wiederholungen."""
        # Hole bereits beantwortete Fragen für den aktuellen Benutzer
        answered_questions = set()
        if hasattr(self, 'current_user') and self.current_user:
            attempts = self.session.query(QuizAttempt)\
                .filter_by(user_id=self.current_user.id, movie_id=movie_id)\
                .all()
            for attempt in attempts:
                if hasattr(attempt, 'question_ids'):
                    answered_questions.update(attempt.question_ids)

        # Hole zufällige, noch nicht beantwortete Fragen
        questions = self.session.query(QuizQuestion)\
            .filter_by(movie_id=movie_id)\
            .filter(~QuizQuestion.id.in_(answered_questions) if answered_questions else True)\
            .order_by(func.random())\
            .limit(limit)\
            .all()

        # Wenn nicht genug neue Fragen verfügbar sind, generiere weitere
        if len(questions) < limit:
            new_questions = self.generate_questions(movie_id, count=limit-len(questions))
            questions.extend(new_questions)

        return questions[:limit]

    def get_available_quizzes(self) -> List[Dict]:
        """Holt alle verfügbaren Quiz-Filme mit Statistiken."""
        movies_with_questions = self.session.query(Movie)\
            .join(QuizQuestion)\
            .group_by(Movie.id)\
            .having(func.count(QuizQuestion.id) > 0)\
            .all()

        quizzes = []
        for movie in movies_with_questions:
            question_count = self.session.query(func.count(QuizQuestion.id))\
                .filter_by(movie_id=movie.id)\
                .scalar()

            highscore = self.session.query(func.max(QuizAttempt.score))\
                .filter_by(movie_id=movie.id)\
                .scalar() or 0

            quizzes.append({
                'movie': movie,
                'question_count': question_count,
                'highscore': highscore
            })

        return quizzes

    def get_highscores(self, movie_id: int, limit: int = 5) -> List[Dict]:
        """Holt die Highscores für einen bestimmten Film."""
        return self.session.query(Highscore)\
            .join(User)\
            .filter(Highscore.movie_id == movie_id)\
            .order_by(Highscore.best_score.desc())\
            .limit(limit)\
            .all()

    def submit_quiz_attempt(self, user_id: int, movie_id: int,
                          answers: List[Dict], score: int) -> QuizAttempt:
        """Speichert einen Quiz-Versuch und vergibt ggf. Trophäen."""
        attempt = QuizAttempt(
            user_id=user_id,
            movie_id=movie_id,
            score=score,
            correct_count=len([a for a in answers if a.get('isCorrect')])
        )
        self.session.add(attempt)

        # Aktualisiere Highscore
        highscore = self.session.query(Highscore)\
            .filter_by(user_id=user_id, movie_id=movie_id)\
            .first()

        is_new_highscore = False
        if not highscore or score > highscore.best_score:
            is_new_highscore = True
            if highscore:
                highscore.best_score = score
            else:
                highscore = Highscore(
                    user_id=user_id,
                    movie_id=movie_id,
                    best_score=score
                )
                self.session.add(highscore)

        # Überprüfe und vergebe Trophäen
        earned_achievements = self.check_and_award_achievements(user_id, score, is_new_highscore)

        self.session.commit()
        return attempt, earned_achievements

    def check_and_award_achievements(self, user_id: int, score: int, is_new_highscore: bool) -> List[Achievement]:
        """Überprüft und vergibt Trophäen basierend auf der Quiz-Leistung."""
        earned_achievements = []

        # Perfektes Quiz (500 Punkte)
        if score == 500:
            perfect = self.session.query(Achievement).filter_by(title='perfect_quiz').first()
            if perfect:
                earned_achievements.append(perfect)

        # Erster Highscore
        if is_new_highscore:
            first = self.session.query(Achievement).filter_by(title='first_highscore').first()
            if first:
                earned_achievements.append(first)

        # Quiz-Master (5 Quizze mit mind. 400 Punkten)
        high_score_count = self.session.query(func.count(Highscore.id))\
            .filter(Highscore.user_id == user_id, Highscore.best_score >= 400)\
            .scalar()
        if high_score_count >= 5:
            master = self.session.query(Achievement).filter_by(title='quiz_master').first()
            if master:
                earned_achievements.append(master)

        # Vergebe die Trophäen
        for achievement in earned_achievements:
            existing = self.session.query(UserAchievement)\
                .filter_by(user_id=user_id, achievement_id=achievement.id)\
                .first()

            if not existing:
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    earned_at=datetime.utcnow()
                )
                self.session.add(user_achievement)

        return earned_achievements

    def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Holt alle Achievements eines Benutzers."""
        return self.session.query(Achievement)\
            .join(UserAchievement)\
            .filter(UserAchievement.user_id == user_id)\
            .all()

    def get_user_quiz_stats(self, user_id: int) -> Dict:
        """Holt Quiz-Statistiken für einen Benutzer."""
        total_attempts = self.session.query(func.count(QuizAttempt.id))\
            .filter_by(user_id=user_id)\
            .scalar() or 0

        avg_score = self.session.query(func.avg(QuizAttempt.score))\
            .filter_by(user_id=user_id)\
            .scalar() or 0

        highscores = self.session.query(Highscore)\
            .filter_by(user_id=user_id)\
            .all()

        return {
            'total_attempts': total_attempts,
            'average_score': round(float(avg_score), 2),
            'highscores': highscores
        }

    def get_recent_highscores(self, limit: int = 5) -> List[Dict]:
        """Holt die neuesten Highscores."""
        return self.session.query(Highscore)\
            .join(User)\
            .join(Movie)\
            .order_by(Highscore.updated_at.desc())\
            .limit(limit)\
            .all()
