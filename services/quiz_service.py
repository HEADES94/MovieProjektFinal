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
    def __init__(self, data_manager):
        """Initialisiere den Quiz-Service mit einem DataManager."""
        self.data_manager = data_manager
        self.ai_client = AIRequest()
        with self.data_manager.SessionFactory() as session:
            self._init_achievements(session)

    def _init_achievements(self, session):
        """Initialisiert die Standard-Achievements."""
        default_achievements = [
            {
                'title': '🎯 Perfect Quiz',
                'description': 'Erreiche die perfekte Punktzahl in einem Quiz!',
                'code': 'perfect_quiz'
            },
            {
                'title': '🏆 First Highscore',
                'description': 'Erreiche deinen ersten Highscore!',
                'code': 'first_highscore'
            },
            {
                'title': '👑 Quiz Master',
                'description': 'Erreiche in 5 verschiedenen Quizzen mindestens 400 Punkte!',
                'code': 'quiz_master'
            },
            {
                'title': '🎓 Quiz Profi',
                'description': 'Schließe ein schweres Quiz mit mindestens 1000 Punkten ab!',
                'code': 'quiz_expert'
            },
            {
                'title': '📚 Wissensdurst',
                'description': 'Beantworte 100 Fragen korrekt!',
                'code': 'knowledge_seeker'
            },
            {
                'title': '🎬 Film Enthusiast',
                'description': 'Schließe Quizze zu 10 verschiedenen Filmen ab!',
                'code': 'movie_enthusiast'
            },
            {
                'title': '🌟 Perfektionist',
                'description': 'Erreiche 3 perfekte Quizze in Folge!',
                'code': 'perfectionist'
            },
            {
                'title': '🔥 Streak Master',
                'description': 'Beantworte 20 Fragen in Folge richtig!',
                'code': 'streak_master'
            }
        ]

        for achievement in default_achievements:
            existing = session.query(Achievement).filter_by(code=achievement['code']).first()
            if not existing:
                new_achievement = Achievement(**achievement)
                session.add(new_achievement)

        try:
            session.commit()
        except:
            session.rollback()

    def get_questions_for_movie(self, movie_id: int) -> List[Dict]:
        """Generiert Quiz-Fragen für einen bestimmten Film."""
        try:
            with self.data_manager.SessionFactory() as session:
                movie = session.get(Movie, movie_id)
                if not movie:
                    return []

                # Erstelle den Filmkontext für die KI
                movie_context = (
                    f"Title: {movie.title}\n"
                    f"Director: {movie.director}\n"
                    f"Year: {movie.release_year}\n"
                    f"Genre: {movie.genre}\n"
                    f"Plot: {movie.description}"
                )

                # Generiere 5 verschiedene Fragen
                questions = []
                for _ in range(5):
                    try:
                        # Hole eine neue Frage von der KI
                        question_data = self.ai_client.generate_quiz_question(movie_context)
                        print(f"Generated question data: {question_data}")  # Debug-Ausgabe

                        # Prüfe, ob die Frage vollständig ist
                        if question_data and all(key in question_data for key in ['question', 'correct_answer', 'wrong_answers']):
                            if len(question_data['wrong_answers']) >= 3:
                                questions.append({
                                    'question': question_data['question'],
                                    'correct_answer': question_data['correct_answer'],
                                    'wrong_answers': question_data['wrong_answers'][:3]
                                })

                    except Exception as e:
                        print(f"Fehler bei der Fragengenerierung: {str(e)}")
                        continue

                # Wenn keine KI-Fragen generiert werden konnten, erstelle Standard-Fragen
                if not questions:
                    questions = self._create_default_questions(movie)

                print(f"Final questions: {questions}")  # Debug-Ausgabe
                return questions[:5]

        except Exception as e:
            print(f"Fehler beim Abrufen der Filmfragen: {str(e)}")
            return []

    def _create_default_questions(self, movie) -> List[Dict]:
        """Erstellt Standard-Quizfragen, wenn die KI-Generierung fehlschlägt."""
        questions = []

        # Frage nach dem Erscheinungsjahr
        if movie.release_year:
            questions.append({
                'question': f"In welchem Jahr wurde '{movie.title}' veröffentlicht?",
                'correct_answer': str(movie.release_year),
                'wrong_answers': [
                    str(movie.release_year - 1),
                    str(movie.release_year - 2),
                    str(movie.release_year + 1)
                ]
            })

        # Frage nach dem Regisseur
        if movie.director:
            questions.append({
                'question': f"Wer führte Regie bei '{movie.title}'?",
                'correct_answer': movie.director,
                'wrong_answers': [
                    "Steven Spielberg",
                    "Christopher Nolan",
                    "Martin Scorsese"
                ]
            })

        # Frage nach dem Genre
        if movie.genre:
            questions.append({
                'question': f"Welchem Genre gehört '{movie.title}' hauptsächlich an?",
                'correct_answer': movie.genre.split(',')[0].strip(),
                'wrong_answers': [
                    "Action",
                    "Drama",
                    "Comedy"
                ]
            })

        return questions

    def calculate_score(self, movie_id: int, answers: dict, difficulty: str = 'mittel') -> int:
        """Berechnet die Punktzahl basierend auf den Antworten und der Schwierigkeit."""
        with self.data_manager.SessionFactory() as session:
            # Hole die korrekten Antworten aus dem Formular
            correct_answers = {k: v for k, v in answers.items() if k.startswith('correct')}
            user_answers = {k: v for k, v in answers.items() if k.startswith('answer')}

            # Zähle die korrekten Antworten
            correct_count = sum(
                1 for i, answer in user_answers.items()
                if answer == correct_answers.get(f'correct{i[-1]}')
            )

            # Schwierigkeitsmultiplikator
            difficulty_multipliers = {
                'leicht': 1.0,
                'mittel': 1.5,
                'schwer': 2.0
            }

            multiplier = difficulty_multipliers.get(difficulty, 1.0)

            # Berechne die Gesamtpunktzahl
            # Basis: 200 Punkte pro korrekte Antwort
            base_score = correct_count * 200
            final_score = int(base_score * multiplier)

            return final_score

    def _award_achievement(self, session, achievement_code: str, user_id: int):
        """Verleiht ein Achievement an einen Benutzer."""
        try:
            achievement = session.query(Achievement).filter_by(code=achievement_code).first()
            if achievement:
                existing = session.query(UserAchievement).filter_by(
                    user_id=user_id,
                    achievement_id=achievement.id
                ).first()

                if not existing:
                    user_achievement = UserAchievement(
                        user_id=user_id,
                        achievement_id=achievement.id,
                        earned_at=datetime.utcnow()
                    )
                    session.add(user_achievement)
                    session.commit()
                    return True
        except Exception as e:
            print(f"Fehler beim Vergeben des Achievements: {str(e)}")
            session.rollback()
        return False

    def _check_quiz_master_achievement(self, session, user_id: int):
        """Überprüft, ob der Quiz-Master Achievement vergeben werden soll."""
        try:
            high_score_count = session.query(func.count(QuizAttempt.id)).filter(
                QuizAttempt.user_id == user_id,
                QuizAttempt.score >= 400
            ).scalar()

            if high_score_count >= 5:
                self._award_achievement(session, 'quiz_master', user_id)
        except Exception as e:
            print(f"Fehler beim Überprüfen des Quiz-Master Achievements: {str(e)}")

    def _check_knowledge_seeker_achievement(self, session, user_id: int, correct_answers: int):
        """Überprüft, ob das Wissensdurst Achievement vergeben werden soll."""
        try:
            total_correct = session.query(func.sum(QuizAttempt.correct_answers)).filter_by(
                user_id=user_id
            ).scalar() or 0

            if total_correct + correct_answers >= 100:
                self._award_achievement(session, 'knowledge_seeker', user_id)
        except Exception as e:
            print(f"Fehler beim Überprüfen des Wissensdurst Achievements: {str(e)}")

    def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Holt alle Achievements eines Benutzers."""
        with self.data_manager.SessionFactory() as session:
            achievements = session.query(Achievement).join(
                UserAchievement
            ).filter(
                UserAchievement.user_id == user_id
            ).all()

            return [
                {
                    'title': a.title,
                    'description': a.description,
                    'code': a.code,
                    'earned_at': session.query(UserAchievement).filter_by(
                        user_id=user_id,
                        achievement_id=a.id
                    ).first().earned_at
                }
                for a in achievements
            ]
