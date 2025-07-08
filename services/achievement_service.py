"""
achievement_service.py - Service for managing user achievements
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from data_models import Achievement, UserAchievement, User, QuizAttempt, Review, WatchlistItem


class AchievementService:
    """Service for managing achievements and their assignment."""

    def __init__(self, data_manager):
        self.data_manager = data_manager

    def _init_achievements(self, session):
        """Initialize quiz, watchlist, and review-related achievements."""
        default_achievements = [
            {
                'code': 'quiz_beginner',
                'name': '🎉 Quiz Beginner',
                'description': 'Complete your first quiz!'
            },
            {
                'code': 'perfect_quiz',
                'name': '🎯 Perfect Quiz',
                'description': 'Achieve perfect score in a quiz!'
            },
            {
                'code': 'quiz_expert',
                'name': '🎓 Quiz Expert',
                'description': 'Complete a hard quiz with at least 8 correct answers!'
            },
            {
                'code': 'first_highscore',
                'name': '🏆 First Highscore',
                'description': 'Achieve your first highscore!'
            },
            {
                'code': 'quiz_master',
                'name': '👑 Quiz Master',
                'description': 'Achieve at least 400 points in 5 different quizzes!'
            },
            {
                'code': 'knowledge_seeker',
                'name': '📚 Knowledge Seeker',
                'description': 'Answer 100 questions correctly!'
            },
            {
                'code': 'movie_enthusiast',
                'name': '🎬 Movie Enthusiast',
                'description': 'Complete 10 different movie quizzes!'
            },
            {
                'code': 'perfectionist',
                'name': '🌟 Perfectionist',
                'description': 'Achieve 3 perfect quizzes in a row!'
            },
            {
                'code': 'streak_master',
                'name': '🔥 Streak Master',
                'description': 'Answer 20 questions in a row correctly!'
            },
            {
                'code': 'streak_5',
                'name': '🔥 5 Streak',
                'description': 'Answer 5 questions in a row correctly!'
            },
            {
                'code': 'streak_10',
                'name': '🔥 10 Streak',
                'description': 'Answer 10 questions in a row correctly!'
            },
            {
                'code': 'quiz_100',
                'name': '💯 Quiz Veteran',
                'description': 'Complete 100 quizzes!'
            },
            {
                'code': 'first_watchlist',
                'name': '📺 First Collector',
                'description': 'Add your first movie to watchlist!'
            },
            {
                'code': 'collector_10',
                'name': '📺 Collector',
                'description': 'Add 10 movies to watchlist!'
            },
            {
                'code': 'collector_50',
                'name': '📺 Mega Collector',
                'description': 'Add 50 movies to watchlist!'
            },
            {
                'code': 'first_review',
                'name': '📝 First Critic',
                'description': 'Write your first review!'
            },
            {
                'code': 'critic_10',
                'name': '📝 Critic',
                'description': 'Write 10 reviews!'
            },
            {
                'code': 'prolific_critic',
                'name': '📝 Prolific Critic',
                'description': 'Write 25 reviews!'
            },
            {
                'code': 'mega_critic',
                'name': '📝 Mega Critic',
                'description': 'Write 50 reviews!'
            }
        ]

        for achievement_data in default_achievements:
            # Check by both code AND name to avoid unique constraint violations
            existing = session.query(Achievement).filter(
                (Achievement.code == achievement_data['code']) |
                (Achievement.name == achievement_data['name'])
            ).first()

            if not existing:
                try:
                    achievement = Achievement(
                        code=achievement_data['code'],
                        name=achievement_data['name'],
                        description=achievement_data['description']
                    )
                    session.add(achievement)
                    session.flush()  # Flush to catch any constraint violations immediately
                except Exception as e:
                    # If there's a constraint violation, just continue
                    session.rollback()
                    print(f"Achievement {achievement_data['code']} already exists or has constraint violation: {e}")

    def _grant_achievement(self, user_id: int, achievement_code: str, session) -> Optional[Achievement]:
        """Grant an achievement to a user."""
        try:
            with session.no_autoflush:
                achievement = session.query(Achievement).filter_by(code=achievement_code).first()
                if not achievement:
                    achievement_data = self._get_achievement_data(achievement_code)
                    if achievement_data:
                        # Check if achievement with this name already exists
                        existing_by_name = session.query(Achievement).filter_by(
                            name=achievement_data['name']
                        ).first()

                        if existing_by_name:
                            # Use the existing achievement
                            achievement = existing_by_name
                        else:
                            try:
                                achievement = Achievement(
                                    code=achievement_data['code'],
                                    name=achievement_data['name'],
                                    description=achievement_data['description']
                                )
                                session.add(achievement)
                                session.flush()
                            except Exception as e:
                                # If constraint violation, try to find existing achievement by name
                                session.rollback()
                                achievement = session.query(Achievement).filter_by(
                                    name=achievement_data['name']
                                ).first()
                                if not achievement:
                                    print(f"Failed to create or find achievement {achievement_code}: {e}")
                                    return None
                    else:
                        return None

                if not achievement:
                    return None

                # Double-check if user already has this achievement
                existing = session.query(UserAchievement).filter_by(
                    user_id=user_id,
                    achievement_id=achievement.id
                ).first()

                if existing:
                    print(f"DEBUG: User {user_id} already has achievement {achievement_code}")
                    return None

                # Create the user achievement
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    earned_at=datetime.now()
                )
                session.add(user_achievement)

                # Try to flush immediately to catch constraint violations
                try:
                    session.flush()
                    print(f"DEBUG: Successfully granted {achievement_code} to user {user_id}")
                    return achievement
                except Exception as flush_error:
                    print(f"DEBUG: Constraint violation for {achievement_code} - user {user_id} already has it")
                    session.rollback()
                    return None

        except Exception as e:
            print(f"Error granting achievement {achievement_code}: {e}")
            session.rollback()
            return None

    def _get_achievement_data(self, code: str) -> Optional[dict]:
        """Get achievement data based on code."""
        achievements = {
            'quiz_beginner': {
                'code': 'quiz_beginner',
                'name': '🎉 Quiz Beginner',
                'description': 'Complete your first quiz!'
            },
            'perfect_quiz': {
                'code': 'perfect_quiz',
                'name': '🎯 Perfect Quiz',
                'description': 'Achieve perfect score in a quiz!'
            },
            'quiz_expert': {
                'code': 'quiz_expert',
                'name': '🎓 Quiz Expert',
                'description': 'Complete a hard quiz with at least 8 correct answers!'
            },
            'first_highscore': {
                'code': 'first_highscore',
                'name': '🏆 First Highscore',
                'description': 'Achieve your first highscore!'
            },
            'quiz_master': {
                'code': 'quiz_master',
                'name': '👑 Quiz Master',
                'description': 'Achieve at least 400 points in 5 different quizzes!'
            },
            'knowledge_seeker': {
                'code': 'knowledge_seeker',
                'name': '📚 Knowledge Seeker',
                'description': 'Answer 100 questions correctly!'
            },
            'movie_enthusiast': {
                'code': 'movie_enthusiast',
                'name': '🎬 Movie Enthusiast',
                'description': 'Complete 10 different movie quizzes!'
            },
            'perfectionist': {
                'code': 'perfectionist',
                'name': '🌟 Perfectionist',
                'description': 'Achieve 3 perfect quizzes in a row!'
            },
            'streak_master': {
                'code': 'streak_master',
                'name': '🔥 Streak Master',
                'description': 'Answer 20 questions in a row correctly!'
            },
            'streak_5': {
                'code': 'streak_5',
                'name': '🔥 5 Streak',
                'description': 'Answer 5 questions in a row correctly!'
            },
            'streak_10': {
                'code': 'streak_10',
                'name': '🔥 10 Streak',
                'description': 'Answer 10 questions in a row correctly!'
            },
            'quiz_100': {
                'code': 'quiz_100',
                'name': '💯 Quiz Veteran',
                'description': 'Complete 100 quizzes!'
            },
            'first_watchlist': {
                'code': 'first_watchlist',
                'name': '📺 First Collector',
                'description': 'Add your first movie to watchlist!'
            },
            'collector_10': {
                'code': 'collector_10',
                'name': '📺 Collector',
                'description': 'Add 10 movies to watchlist!'
            },
            'collector_50': {
                'code': 'collector_50',
                'name': '📺 Mega Collector',
                'description': 'Add 50 movies to watchlist!'
            },
            'first_review': {
                'code': 'first_review',
                'name': '📝 First Critic',
                'description': 'Write your first review!'
            },
            'critic_10': {
                'code': 'critic_10',
                'name': '📝 Critic',
                'description': 'Write 10 reviews!'
            },
            'prolific_critic': {
                'code': 'prolific_critic',
                'name': '📝 Prolific Critic',
                'description': 'Write 25 reviews!'
            },
            'mega_critic': {
                'code': 'mega_critic',
                'name': '📝 Mega Critic',
                'description': 'Write 50 reviews!'
            }
        }
        return achievements.get(code)

    def check_quiz_achievements(self, user_id: int, score: int, difficulty: str) -> List[dict]:
        """Check and award quiz-related achievements."""
        with self.data_manager.SessionFactory() as session:
            try:
                self._init_achievements(session)
                earned_achievements = []

                # Get all quiz attempts for this user
                user_attempts = session.query(QuizAttempt).filter_by(user_id=user_id).all()
                quiz_attempts_count = len(user_attempts)

                print(f"DEBUG: User {user_id} has {quiz_attempts_count} quiz attempts, latest score: {score}")

                # Use no_autoflush to prevent premature commits
                with session.no_autoflush:
                    # Quiz Beginner - First quiz completed
                    if quiz_attempts_count == 1:
                        achievement = self._grant_achievement(user_id, 'quiz_beginner', session)
                        if achievement:
                            earned_achievements.append({'title': achievement.name, 'description': achievement.description})
                            print(f"DEBUG: Awarded Quiz Beginner to user {user_id}")

                    # Perfect Quiz - Get perfect score (all questions correct)
                    # Calculate correct answers based on score and difficulty
                    if difficulty == 'schwer':
                        max_points_per_question = 200
                        bonus_threshold = 5 * max_points_per_question  # 5 questions * 200 points
                    else:
                        max_points_per_question = 100
                        bonus_threshold = 5 * max_points_per_question  # 5 questions * 100 points

                    # Perfect score means all 5 questions correct (with or without bonus)
                    if score >= bonus_threshold:
                        achievement = self._grant_achievement(user_id, 'perfect_quiz', session)
                        if achievement:
                            earned_achievements.append({'title': achievement.name, 'description': achievement.description})
                            print(f"DEBUG: Awarded Perfect Quiz to user {user_id}")

                    # Quiz Expert - Hard quiz with high score (at least 4 out of 5 correct)
                    if difficulty == 'schwer' and score >= (4 * 200):  # At least 4 correct in hard mode
                        achievement = self._grant_achievement(user_id, 'quiz_expert', session)
                        if achievement:
                            earned_achievements.append({'title': achievement.name, 'description': achievement.description})
                            print(f"DEBUG: Awarded Quiz Expert to user {user_id}")

                    # First Highscore - Check if this is a new personal best
                    if user_attempts:
                        previous_best = max(attempt.score for attempt in user_attempts[:-1]) if len(user_attempts) > 1 else 0
                        current_attempt = user_attempts[-1]  # Latest attempt
                        if current_attempt.score > previous_best and previous_best > 0:
                            achievement = self._grant_achievement(user_id, 'first_highscore', session)
                            if achievement:
                                earned_achievements.append({'title': achievement.name, 'description': achievement.description})
                                print(f"DEBUG: Awarded First Highscore to user {user_id} (new score: {current_attempt.score}, previous best: {previous_best})")
                        elif len(user_attempts) == 1 and current_attempt.score > 0:
                            # First quiz ever is also a first highscore
                            achievement = self._grant_achievement(user_id, 'first_highscore', session)
                            if achievement:
                                earned_achievements.append({'title': achievement.name, 'description': achievement.description})
                                print(f"DEBUG: Awarded First Highscore to user {user_id} (first quiz)")

                    # Streak Achievements - Check consecutive correct answers
                    # Calculate streaks across all quiz attempts
                    all_correct_answers = []
                    for attempt in sorted(user_attempts, key=lambda x: x.completed_at):
                        # Calculate correct answers for this attempt
                        if attempt.difficulty == 'schwer':
                            correct_count = min(attempt.score // 200, attempt.total_questions or 5)
                        else:
                            correct_count = min(attempt.score // 100, attempt.total_questions or 5)

                        total_questions = attempt.total_questions or 5
                        # Add individual question results (True for correct, False for incorrect)
                        for i in range(total_questions):
                            all_correct_answers.append(i < correct_count)

                    # Find longest streak of correct answers
                    current_streak = 0
                    max_streak = 0
                    for is_correct in all_correct_answers:
                        if is_correct:
                            current_streak += 1
                            max_streak = max(max_streak, current_streak)
                        else:
                            current_streak = 0

                    print(f"DEBUG: User {user_id} max streak: {max_streak}")

                    # Award streak achievements
                    if max_streak >= 5:
                        achievement = self._grant_achievement(user_id, 'streak_5', session)
                        if achievement:
                            earned_achievements.append({'title': achievement.name, 'description': achievement.description})
                            print(f"DEBUG: Awarded 5 Streak to user {user_id}")

                    if max_streak >= 10:
                        achievement = self._grant_achievement(user_id, 'streak_10', session)
                        if achievement:
                            earned_achievements.append({'title': achievement.name, 'description': achievement.description})
                            print(f"DEBUG: Awarded 10 Streak to user {user_id}")

                    if max_streak >= 20:
                        achievement = self._grant_achievement(user_id, 'streak_master', session)
                        if achievement:
                            earned_achievements.append({'title': achievement.name, 'description': achievement.description})
                            print(f"DEBUG: Awarded Streak Master to user {user_id}")

                    # Quiz Veteran - 100 quizzes completed
                    if quiz_attempts_count >= 100:
                        achievement = self._grant_achievement(user_id, 'quiz_100', session)
                        if achievement:
                            earned_achievements.append({'title': achievement.name, 'description': achievement.description})
                            print(f"DEBUG: Awarded Quiz Veteran to user {user_id}")

                # Commit all changes at once
                session.commit()
                print(f"DEBUG: Total achievements earned: {len(earned_achievements)}")
                return earned_achievements

            except Exception as e:
                print(f"ERROR in check_quiz_achievements: {e}")
                session.rollback()
                return []

    def check_watchlist_achievements(self, user_id: int) -> List[dict]:
        """Check and award watchlist-related achievements."""
        with self.data_manager.SessionFactory() as session:
            self._init_achievements(session)
            new_achievements = []

            watchlist_count = session.query(WatchlistItem).filter_by(user_id=user_id).count()

            milestones = [
                (1, 'first_watchlist'),
                (10, 'collector_10'),
                (50, 'collector_50')
            ]

            for count, code in milestones:
                if watchlist_count >= count:
                    achievement = self._grant_achievement(user_id, code, session)
                    if achievement:
                        new_achievements.append({
                            'title': achievement.name,
                            'description': achievement.description
                        })

            session.commit()
            return new_achievements

    def check_review_achievements(self, user_id: int) -> List[dict]:
        """Check and award review-related achievements."""
        with self.data_manager.SessionFactory() as session:
            self._init_achievements(session)
            new_achievements = []

            review_count = session.query(Review).filter_by(user_id=user_id).count()

            milestones = [
                (1, 'first_review'),
                (10, 'critic_10'),
                (25, 'prolific_critic'),
                (50, 'mega_critic')
            ]

            for count, code in milestones:
                if review_count >= count:
                    achievement = self._grant_achievement(user_id, code, session)
                    if achievement:
                        new_achievements.append({
                            'title': achievement.name,
                            'description': achievement.description
                        })

            session.commit()
            return new_achievements

    def _award_achievement(self, session, user_id: int, code: str) -> Optional[dict]:
        """Award an achievement to a user."""
        achievement = session.query(Achievement).filter_by(code=code).first()
        if not achievement:
            return None

        existing = session.query(UserAchievement).filter_by(
            user_id=user_id,
            achievement_id=achievement.id
        ).first()

        if existing:
            return None

        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement.id,
            earned_at=datetime.now()
        )
        session.add(user_achievement)
        return {
            'title': achievement.name,
            'description': achievement.description
        }
