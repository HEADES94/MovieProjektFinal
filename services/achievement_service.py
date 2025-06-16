"""
achievement_service.py - Service für die Achievement-Vergabe
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from data_models import Achievement, UserAchievement, User, QuizAttempt, Review, WatchlistItem

class AchievementService:
    """Service zur Verwaltung von Achievements und deren Vergabe."""

    def __init__(self, data_manager):
        self.data_manager = data_manager
        with self.data_manager.SessionFactory() as session:
            self._init_achievements(session)

    def _init_achievements(self, session):
        """Initialisiert Quiz-, Watchlist- und Kommentar-bezogene Achievements."""
        default_achievements = [
            # Quiz-bezogene Achievements
            {
                'code': 'quiz_beginner',
                'title': '🎉 Quiz-Neuling',
                'description': 'Beende dein erstes Quiz!'
            },
            {
                'code': 'perfect_quiz',
                'title': '🎯 Perfect Quiz',
                'description': 'Erreiche die perfekte Punktzahl in einem Quiz!'
            },
            {
                'code': 'quiz_expert',
                'title': '🎓 Quiz Profi',
                'description': 'Schließe ein schweres Quiz mit mindestens 1000 Punkten ab!'
            },
            {
                'code': 'quiz_master',
                'title': '👑 Quiz Master',
                'description': 'Erreiche in 5 verschiedenen Quizzen mindestens 400 Punkte!'
            },
            {
                'code': 'streak_5',
                'title': '🔥 5er Streak',
                'description': 'Beantworte 5 Fragen in Folge richtig!'
            },
            {
                'code': 'streak_10',
                'title': '🔥 10er Streak',
                'description': 'Beantworte 10 Fragen in Folge richtig!'
            },
            {
                'code': 'quiz_100',
                'title': '💯 Quiz-Veteran',
                'description': 'Beende 100 Quizze!'
            },
            {
                'code': 'all_correct_3',
                'title': '🌟 Perfektionist',
                'description': 'Erreiche 3 perfekte Quizze in Folge!'
            },
            # Watchlist-Achievements
            {
                'code': 'watchlist_add_10',
                'title': '📺 Watchlist-Fan',
                'description': 'Füge 10 Filme zur Watchlist hinzu!'
            },
            # Kommentar-Achievements
            {
                'code': 'reviewer_10',
                'title': '📝 Kritiker',
                'description': 'Schreibe 10 Kommentare!'
            },
            {
                'code': 'comment_like_10',
                'title': '👍 Beliebter Kommentator',
                'description': 'Erhalte 10 Likes auf deine Kommentare!'
            },
        ]

        for achievement in default_achievements:
            existing = session.query(Achievement).filter_by(code=achievement['code']).first()
            if not existing:
                new_achievement = Achievement(
                    code=achievement['code'],
                    title=achievement['title'],
                    description=achievement['description']
                )
                session.add(new_achievement)
        try:
            session.commit()
        except:
            session.rollback()

    def check_quiz_achievements(self, user_id: int, score: int, difficulty: str) -> List[dict]:
        """Überprüft und vergibt Quiz-bezogene Achievements und gibt sie als Dicts zurück."""
        with self.data_manager.SessionFactory() as session:
            earned_achievements = []

            # Quiz-Neuling Achievement
            quiz_attempts = session.query(QuizAttempt).filter_by(user_id=user_id).count()
            if quiz_attempts == 1:  # Erstes Quiz
                achievement = self._grant_achievement(user_id, 'quiz_beginner', session)
                if achievement:
                    earned_achievements.append({'title': achievement.title, 'description': achievement.description})

            # Perfect Quiz Achievement (alle Fragen richtig)
            quiz_attempt = session.query(QuizAttempt).filter_by(
                user_id=user_id
            ).order_by(QuizAttempt.created_at.desc()).first()

            if quiz_attempt and hasattr(quiz_attempt, 'max_possible_score') and quiz_attempt.score == quiz_attempt.max_possible_score:
                achievement = self._grant_achievement(user_id, 'perfect_quiz', session)
                if achievement:
                    earned_achievements.append({'title': achievement.title, 'description': achievement.description})

            # Quiz Expert Achievement (1000+ Punkte in schwerem Quiz)
            if difficulty == 'schwer' and score >= 1000:
                achievement = self._grant_achievement(user_id, 'quiz_expert', session)
                if achievement:
                    earned_achievements.append({'title': achievement.title, 'description': achievement.description})

            # Alle Achievements als Dicts zurückgeben (falls versehentlich noch SQLAlchemy-Objekte enthalten sind)
            result = []
            for ach in earned_achievements:
                if isinstance(ach, dict):
                    result.append(ach)
                else:
                    # Fallback, falls doch ein Objekt durchrutscht
                    result.append({'title': getattr(ach, 'title', ''), 'description': getattr(ach, 'description', '')})
            return result

    def _grant_achievement(self, user_id: int, achievement_code: str, session) -> Optional[Achievement]:
        """Vergibt ein Achievement an einen Benutzer."""
        # Prüfe, ob der Benutzer das Achievement bereits hat
        achievement = session.query(Achievement).filter_by(code=achievement_code).first()
        if not achievement:
            return None

        existing = session.query(UserAchievement).filter_by(
            user_id=user_id,
            achievement_id=achievement.id
        ).first()

        if existing:
            return None

        # Erstelle einen neuen UserAchievement-Eintrag
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement.id,
            earned_at=datetime.now()
        )
        session.add(user_achievement)
        return achievement
