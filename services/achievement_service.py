"""
achievement_service.py - Service für das Achievement-System
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from data_models import Achievement, UserAchievement, User, QuizAttempt, Review, WatchlistItem

class AchievementService:
    """Service zur Verwaltung von Achievements und deren Vergabe."""

    def __init__(self, session: Session):
        self.session = session

    def check_achievements(self, user_id: int) -> List[Achievement]:
        """
        Überprüft alle möglichen Achievements für einen Benutzer und vergibt neue.
        """
        user = self.session.query(User).get(user_id)
        if not user:
            return []

        earned_achievements = []

        # Überprüfe Quiz-basierte Achievements
        quiz_attempts = self.session.query(QuizAttempt).filter_by(user_id=user_id).all()

        # Perfect Quiz Achievement (100% bei einem Quiz)
        perfect_quiz = any(
            attempt.score == attempt.max_possible_score
            for attempt in quiz_attempts
        )
        if perfect_quiz and self._check_achievement_eligibility(user_id, "perfect_quiz"):
            earned_achievements.append(self._grant_achievement(user_id, "perfect_quiz"))

        # First Highscore Achievement
        has_highscore = any(attempt.is_highscore for attempt in quiz_attempts)
        if has_highscore and self._check_achievement_eligibility(user_id, "first_highscore"):
            earned_achievements.append(self._grant_achievement(user_id, "first_highscore"))

        # Quiz Master Achievement (5 verschiedene Quizze mit mind. 400 Punkten)
        high_scoring_quizzes = set(
            attempt.quiz_id
            for attempt in quiz_attempts
            if attempt.score >= 400
        )
        if len(high_scoring_quizzes) >= 5 and self._check_achievement_eligibility(user_id, "quiz_master"):
            earned_achievements.append(self._grant_achievement(user_id, "quiz_master"))

        # Überprüfe Review-basierte Achievements
        review_count = self.session.query(Review).filter_by(user_id=user_id).count()
        if review_count >= 1 and self._check_achievement_eligibility(user_id, "first_review"):
            earned_achievements.append(self._grant_achievement(user_id, "first_review"))
        if review_count >= 10 and self._check_achievement_eligibility(user_id, "review_master"):
            earned_achievements.append(self._grant_achievement(user_id, "review_master"))

        # Überprüfe Watchlist-basierte Achievements
        watchlist_count = self.session.query(WatchlistItem).filter_by(user_id=user_id).count()
        if watchlist_count >= 5 and self._check_achievement_eligibility(user_id, "watchlist_collector"):
            earned_achievements.append(self._grant_achievement(user_id, "watchlist_collector"))

        return [achievement for achievement in earned_achievements if achievement]

    def _check_achievement_eligibility(self, user_id: int, achievement_id: str) -> bool:
        """Prüft, ob ein Benutzer für ein Achievement berechtigt ist."""
        achievement = self.session.query(Achievement).filter_by(id=achievement_id).first()
        if not achievement:
            return False

        existing = self.session.query(UserAchievement).filter_by(
            user_id=user_id,
            achievement_id=achievement.id
        ).first()

        return not existing

    def _grant_achievement(self, user_id: int, achievement_id: str) -> Optional[Achievement]:
        """Vergibt ein Achievement an einen Benutzer."""
        achievement = self.session.query(Achievement).filter_by(id=achievement_id).first()
        if not achievement:
            return None

        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement.id,
            earned_at=datetime.utcnow()
        )

        self.session.add(user_achievement)
        self.session.commit()

        return achievement

    def get_available_achievements(self) -> List[Achievement]:
        """Gibt alle verfügbaren Achievements zurück."""
        return self.session.query(Achievement).all()

    def get_user_achievements(self, user_id: int) -> List[Achievement]:
        """Gibt alle Achievements eines Benutzers zurück."""
        user = self.session.query(User).get(user_id)
        if not user:
            return []
        return user.achievements

def init_achievements(session: Session) -> None:
    """Initialisiert die Standard-Achievements in der Datenbank."""
    achievements = [
        {
            "id": "perfect_quiz",
            "title": "Perfect Quiz",
            "description": "Erreiche die perfekte Punktzahl in einem Quiz!",
            "icon_url": "/static/achievements/perfect_quiz.png"
        },
        {
            "id": "first_highscore",
            "title": "Erster Highscore",
            "description": "Erreiche deinen ersten Highscore!",
            "icon_url": "/static/achievements/first_highscore.png"
        },
        {
            "id": "quiz_master",
            "title": "Quiz Master",
            "description": "Erreiche in 5 verschiedenen Quizzen mindestens 400 Punkte!",
            "icon_url": "/static/achievements/quiz_master.png"
        },
        {
            "id": "first_review",
            "title": "Erster Eindruck",
            "description": "Schreibe deine erste Filmbewertung",
            "icon_url": "/static/achievements/first_review.png"
        },
        {
            "id": "review_master",
            "title": "Kritiker-Profi",
            "description": "Bewerte 10 verschiedene Filme",
            "icon_url": "/static/achievements/review_master.png"
        },
        {
            "id": "watchlist_collector",
            "title": "Film-Sammler",
            "description": "Füge 5 Filme zu deiner Watchlist hinzu",
            "icon_url": "/static/achievements/watchlist_collector.png"
        }
    ]

    for achievement_data in achievements:
        existing = session.query(Achievement).filter_by(id=achievement_data["id"]).first()
        if not existing:
            achievement = Achievement(**achievement_data)
            session.add(achievement)

    session.commit()
