"""
quiz_service.py - Service für die Quiz-Funktionalität
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
    def __init__(self, data_manager):
        """Initialisiere den Quiz-Service mit einem DataManager."""
        self.data_manager = data_manager
        self.ai_client = AIRequest()
        with self.data_manager.SessionFactory() as session:
            self._init_achievements(session)

    def _init_achievements(self, session):
        """Initialisiert die Standard-Achievements (zentralisiert und vereinheitlicht)."""
        default_achievements = [
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
                'code': 'first_highscore',
                'title': '🏆 First Highscore',
                'description': 'Erreiche deinen ersten Highscore!'
            },
            {
                'code': 'quiz_master',
                'title': '👑 Quiz Master',
                'description': 'Erreiche in 5 verschiedenen Quizzen mindestens 400 Punkte!'
            },
            {
                'code': 'knowledge_seeker',
                'title': '📚 Wissensdurst',
                'description': 'Beantworte 100 Fragen korrekt!'
            },
            {
                'code': 'movie_enthusiast',
                'title': '🎬 Film Enthusiast',
                'description': 'Schließe Quizze zu 10 verschiedenen Filmen ab!'
            },
            {
                'code': 'perfectionist',
                'title': '🌟 Perfektionist',
                'description': 'Erreiche 3 perfekte Quizze in Folge!'
            },
            {
                'code': 'streak_master',
                'title': '🔥 Streak Master',
                'description': 'Beantworte 20 Fragen in Folge richtig!'
            }
        ]

        for achievement in default_achievements:
            if not session.query(Achievement).filter_by(code=achievement['code']).first():
                new_achievement = Achievement(
                    code=achievement['code'],
                    title=achievement['title'],
                    description=achievement['description']
                )
                session.add(new_achievement)
        session.commit()

    def get_questions_for_movie(self, movie_id: int, difficulty: str = 'mittel') -> List[Dict]:
        """Holt oder generiert neue Quizfragen für einen bestimmten Film."""
        with self.data_manager.SessionFactory() as session:
            try:
                movie = session.query(Movie).get(movie_id)
                if not movie:
                    return []

                # Hole die letzten Quiz-Versuche des Benutzers für diesen Film
                recent_questions = set()
                if current_user.is_authenticated:
                    # Hole die IDs der kürzlich beantworteten Fragen
                    recent_attempts = session.query(QuizAttempt).filter_by(
                        user_id=current_user.id,
                        movie_id=movie_id
                    ).order_by(QuizAttempt.created_at.desc()).limit(5).all()

                    for attempt in recent_attempts:
                        attempt_questions = session.query(QuizAttemptQuestion).filter_by(
                            attempt_id=attempt.id
                        ).all()
                        recent_questions.update(q.question_id for q in attempt_questions)

                # Generiere in jedem Fall neue Fragen
                new_questions = self._generate_questions(movie, difficulty)

                # Speichere die neuen Fragen in der Datenbank
                for q in new_questions:
                    session.add(q)
                session.commit()

                # Konvertiere die Fragen in Dictionaries
                questions_data = []
                for i, q in enumerate(new_questions[:5], 1):  # Nimm maximal 5 Fragen
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
                print(f"Fehler beim Laden/Generieren der Quiz-Fragen: {str(e)}")
                return []

    def _generate_questions(self, movie: Movie, difficulty: str) -> List[QuizQuestion]:
        """Generiert neue Quizfragen für einen Film."""
        try:
            # Erstelle einen Kontext für die KI
            movie_context = {
                'title': movie.title,
                'plot': movie.description,
                'genre': movie.genre,
                'director': movie.director,
                'year': movie.release_year
            }

            # Frage die KI nach Quizfragen
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
            print(f"Fehler beim Generieren der Fragen: {str(e)}")
            return []

    def save_quiz_attempt(self, movie_id: int, user_id: int, score: int, difficulty: str) -> Optional[QuizAttempt]:
        """Speichert einen Quiz-Versuch in der Datenbank."""
        try:
            with self.data_manager.SessionFactory() as session:
                # Erstelle einen neuen Quiz-Versuch
                quiz_attempt = QuizAttempt(
                    user_id=user_id,
                    movie_id=movie_id,
                    score=score,
                    difficulty=difficulty,
                    created_at=datetime.now()
                )
                session.add(quiz_attempt)
                session.commit()
                return quiz_attempt
        except Exception as e:
            print(f"Fehler beim Speichern des Quiz-Versuchs: {str(e)}")
            return None

    def calculate_score(self, movie_id: int, answers: Dict[str, str], difficulty: str = 'mittel') -> Dict:
        """Berechnet die Punktzahl für ein Quiz und gibt detaillierte Ergebnisse zurück."""
        with self.data_manager.SessionFactory() as session:
            total_questions = len(answers)
            correct_count = 0
            max_points_per_question = 200 if difficulty == 'schwer' else 100
            question_results = []
            answered_questions = []

            # Hole alle Fragen für diesen Film
            questions = {
                str(q.id): q for q in session.query(QuizQuestion).filter_by(
                    movie_id=movie_id,
                    difficulty=difficulty
                ).all()
            }

            # Verarbeite jede Antwort
            for question_id, user_answer in answers.items():
                if question_id in questions:
                    question = questions[question_id]
                    is_correct = user_answer == question.correct_answer
                    if is_correct:
                        correct_count += 1

                    # Füge detaillierte Ergebnisse für jede Frage hinzu
                    question_results.append({
                        'question_id': question_id,
                        'question_text': question.question_text,
                        'user_answer': user_answer,
                        'correct_answer': question.correct_answer,
                        'is_correct': is_correct
                    })

                    answered_questions.append({
                        'question': question.question_text,
                        'user_answer': user_answer,
                        'correct_answer': question.correct_answer,
                        'is_correct': is_correct
                    })

            # Berechne die Gesamtpunkte
            score = correct_count * max_points_per_question

            # Bonus für alle richtigen Antworten
            if correct_count == total_questions:
                score += 100

            return {
                'score': score,
                'correct_count': correct_count,
                'total_questions': total_questions,
                'question_results': question_results,
                'answered_questions': answered_questions,
                'difficulty': difficulty
            }
