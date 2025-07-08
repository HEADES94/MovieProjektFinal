"""
Service for quiz functionality.
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from flask_login import current_user
from data_models import (QuizQuestion, QuizAttempt, Highscore, Movie, User,
                        Achievement, UserAchievement, QuizAttemptQuestion)
from ai_request import AIRequest
import random


class QuizService:
    """Service for managing quiz functionality."""

    def __init__(self, data_manager):
        """Initialize the quiz service with a DataManager."""
        self.data_manager = data_manager
        self.ai_client = AIRequest()

    def get_questions_for_movie(self, movie_id: int, difficulty: str = 'mittel') -> List[Dict]:
        """Get or generate new quiz questions for a specific movie."""
        with self.data_manager.SessionFactory() as session:
            try:
                movie = session.query(Movie).get(movie_id)
                if not movie:
                    return []

                recent_questions = set()
                if current_user.is_authenticated:
                    recent_attempts = session.query(QuizAttempt).filter_by(
                        user_id=current_user.id
                    ).order_by(QuizAttempt.completed_at.desc()).limit(5).all()

                    for attempt in recent_attempts:
                        attempt_questions = session.query(QuizAttemptQuestion).filter_by(
                            attempt_id=attempt.id
                        ).all()
                        for aq in attempt_questions:
                            question = session.query(QuizQuestion).get(aq.question_id)
                            if question and question.movie_id == movie_id:
                                recent_questions.add(aq.question_id)

                new_questions = self._generate_questions(movie, difficulty)

                for q in new_questions:
                    session.add(q)
                session.commit()

                questions_data = []
                for i, q in enumerate(new_questions[:5], 1):
                    questions_data.append({
                        'id': q.id,
                        'question_text': q.question_text,
                        'correct_answer': q.correct_answer,
                        'wrong_answer_1': q.wrong_answer_1,
                        'wrong_answer_2': q.wrong_answer_2,
                        'wrong_answer_3': q.wrong_answer_3
                    })

                return questions_data

            except Exception as e:
                session.rollback()
                print(f"Error loading/generating quiz questions: {str(e)}")
                return []

    def _generate_questions(self, movie: Movie, difficulty: str) -> List[QuizQuestion]:
        """Generate new quiz questions for a movie."""
        try:
            movie_context = {
                'title': movie.title,
                'plot': movie.plot,
                'genre': movie.genre,
                'director': movie.director,
                'year': movie.release_year
            }

            questions_data = self.ai_client.generate_quiz_questions(movie_context, difficulty)

            quiz_questions = []
            if questions_data:
                for q_data in questions_data:
                    question = QuizQuestion(
                        movie_id=movie.id,
                        question_text=q_data['question'],
                        correct_answer=q_data['correct_answer'],
                        wrong_answer_1=q_data['wrong_answers'][0],
                        wrong_answer_2=q_data['wrong_answers'][1],
                        wrong_answer_3=q_data['wrong_answers'][2],
                        difficulty=difficulty
                    )
                    quiz_questions.append(question)

            return quiz_questions

        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            return []

    def save_quiz_attempt(self, movie_id: int, user_id: int, score: int, difficulty: str) -> Optional[QuizAttempt]:
        """Save a quiz attempt to the database."""
        try:
            with self.data_manager.SessionFactory() as session:
                quiz_attempt = QuizAttempt(
                    user_id=user_id,
                    score=score,
                    total_questions=5,
                    difficulty=difficulty,
                    completed_at=datetime.now()
                )
                session.add(quiz_attempt)
                session.commit()
                return quiz_attempt
        except Exception as e:
            print(f"Error saving quiz attempt: {str(e)}")
            return None

    def calculate_score(self, movie_id: int, answers: dict, difficulty: str) -> dict:
        """Calculate the score for a quiz attempt."""
        with self.data_manager.SessionFactory() as session:
            try:
                question_ids = list(answers.keys())
                questions = session.query(QuizQuestion).filter(
                    QuizQuestion.id.in_(question_ids)
                ).all()

                if not questions:
                    return {
                        'score': 0,
                        'correct_count': 0,
                        'total_questions': 0,
                        'question_results': []
                    }

                correct_count = 0
                question_results = []

                for question in questions:
                    user_answer = answers.get(str(question.id), '')
                    is_correct = user_answer.strip() == question.correct_answer.strip()

                    if is_correct:
                        correct_count += 1

                    question_results.append({
                        'question_id': question.id,
                        'question_text': question.question_text,
                        'user_answer': user_answer,
                        'correct_answer': question.correct_answer,
                        'is_correct': is_correct
                    })

                total_questions = len(questions)
                base_score = correct_count * 100

                if difficulty == 'schwer':
                    base_score = correct_count * 200

                bonus = 0
                if correct_count == total_questions:
                    bonus = 100

                final_score = base_score + bonus

                return {
                    'score': final_score,
                    'correct_count': correct_count,
                    'total_questions': total_questions,
                    'question_results': question_results
                }

            except Exception as e:
                print(f"Error calculating score: {str(e)}")
                return {
                    'score': 0,
                    'correct_count': 0,
                    'total_questions': 0,
                    'question_results': []
                }

    def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics for quizzes."""
        with self.data_manager.SessionFactory() as session:
            try:
                total_attempts = session.query(QuizAttempt).filter_by(
                    user_id=user_id
                ).count()

                if total_attempts == 0:
                    return {
                        'total_attempts': 0,
                        'best_score': 0,
                        'avg_score': 0,
                        'total_correct': 0,
                        'total_questions': 0,
                        'accuracy': 0
                    }

                best_score = session.query(func.max(QuizAttempt.score)).filter_by(
                    user_id=user_id
                ).scalar() or 0

                avg_score = session.query(func.avg(QuizAttempt.score)).filter_by(
                    user_id=user_id
                ).scalar() or 0

                attempts = session.query(QuizAttempt).filter_by(
                    user_id=user_id
                ).all()

                total_correct = sum(
                    attempt.score // 100 for attempt in attempts
                )
                total_questions = sum(
                    attempt.total_questions for attempt in attempts
                )

                accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0

                return {
                    'total_attempts': total_attempts,
                    'best_score': best_score,
                    'avg_score': round(avg_score, 1),
                    'total_correct': total_correct,
                    'total_questions': total_questions,
                    'accuracy': round(accuracy, 1)
                }

            except Exception as e:
                print(f"Error getting user stats: {str(e)}")
                return {
                    'total_attempts': 0,
                    'best_score': 0,
                    'avg_score': 0,
                    'total_correct': 0,
                    'total_questions': 0,
                    'accuracy': 0
                }

    def get_highscores(self, limit: int = 10) -> List[Dict]:
        """Get the top highscores."""
        with self.data_manager.SessionFactory() as session:
            try:
                highscores = session.query(Highscore).order_by(
                    Highscore.score.desc()
                ).limit(limit).all()

                return [{
                    'username': hs.user.username,
                    'score': hs.score,
                    'movie_title': hs.movie.title if hs.movie else 'Unknown',
                    'achieved_at': hs.achieved_at.strftime('%d.%m.%Y')
                } for hs in highscores]

            except Exception as e:
                print(f"Error getting highscores: {str(e)}")
                return []

    def update_highscore(self, user_id: int, score: int, movie_id: int = None) -> bool:
        """Update or create a highscore entry."""
        with self.data_manager.SessionFactory() as session:
            try:
                existing_highscore = session.query(Highscore).filter_by(
                    user_id=user_id,
                    movie_id=movie_id
                ).first()

                if existing_highscore:
                    if score > existing_highscore.score:
                        existing_highscore.score = score
                        existing_highscore.achieved_at = datetime.now()
                        session.commit()
                        return True
                    return False
                else:
                    new_highscore = Highscore(
                        user_id=user_id,
                        movie_id=movie_id,
                        score=score,
                        achieved_at=datetime.now()
                    )
                    session.add(new_highscore)
                    session.commit()
                    return True

            except Exception as e:
                session.rollback()
                print(f"Error updating highscore: {str(e)}")
                return False

