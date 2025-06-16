"""
ai_request.py - Schnittstelle zur Google Gemini AI für Filmempfehlungen und Quiz-Fragen
"""
import os
import json
import requests
from typing import Optional, Dict, List
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

# Lade Umgebungsvariablen
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# TMDB API Basis-URL
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Konfiguriere die Google AI
generation_config = GenerationConfig(
    temperature=0.9,
    top_p=1,
    top_k=1,
    max_output_tokens=2048,
)

genai.configure(api_key=API_KEY)

# Liste verfügbare Modelle und wähle das richtige aus
available_models = [m.name for m in genai.list_models()]
print("Verfügbare Modelle:", available_models)

def get_movie_details(title: str, year: str = None) -> Optional[Dict]:
    """
    Hole detaillierte Filminformationen von der OMDB API.
    """
    omdb_url = "http://www.omdbapi.com/"

    try:
        # OMDB API Abfrage
        omdb_params = {
            "apikey": OMDB_API_KEY,
            "t": title,
            "y": year,
            "plot": "full"
        }
        omdb_response = requests.get(omdb_url, params=omdb_params)
        omdb_data = omdb_response.json()

        if omdb_data.get("Response") == "True":
            return {
                "title": omdb_data.get("Title", title),
                "director": omdb_data.get("Director", "Unknown"),
                "year": omdb_data.get("Year", "")[:4],
                "poster": omdb_data.get("Poster", ""),
                "imdb": omdb_data.get("imdbID", "").replace("tt", ""),
                "country": omdb_data.get("Country", "Unknown"),
                "genre": omdb_data.get("Genre", "Unknown"),
                "plot": omdb_data.get("Plot", "Keine Beschreibung verfügbar.")
            }

        return {"error": "Film nicht gefunden"}

    except Exception as e:
        print(f"Fehler beim Abrufen der Film-Daten: {str(e)}")
        return {"error": f"API-Fehler: {str(e)}"}

class AIRequest:
    """
    Schnittstelle zur Google Gemini AI für Filmempfehlungen und Quiz-Generierung.
    """
    def __init__(self):
        try:
            # Verwende das verfügbare Modell "models/gemini-2.0-flash"
            self.model = genai.GenerativeModel(
                "models/gemini-2.0-flash",
                generation_config=generation_config
            )
            print("AI-Modell erfolgreich initialisiert")
        except Exception as e:
            print(f"Fehler bei der Modell-Initialisierung: {str(e)}")
            raise

    def ai_request(self, data_string: str) -> Dict:
        """
        Fordere eine Filmempfehlung von der AI an (ohne Ausschluss).
        """
        try:
            # Extrahiere den aktuellen Filmtitel und weitere Informationen aus dem Kontext
            current_movie = {}
            for line in data_string.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    current_movie[key.strip().lower()] = value.strip()

            prompt = f"""You are a movie recommendation system. Based on this movie:
Title: {current_movie.get('title', '')}
Genre: {current_movie.get('genre', '')}
Year: {current_movie.get('year', '')}
Description: {current_movie.get('description', '')}

Recommend a DIFFERENT movie that matches the genre and style. Consider these rules:
1. The movie MUST be different from "{current_movie.get('title', '')}"
2. The movie should be from a similar genre: {current_movie.get('genre', '')}
3. The movie should be either from a similar time period or thematically related
4. Focus on the main genre when making recommendations

RESPOND ONLY WITH A JSON OBJECT IN THIS EXACT FORMAT:
{{
    "title": "Name of the recommended movie",
    "year": "YYYY",
    "explanation": "A brief explanation why this movie is similar"
}}

NO additional text, ONLY the JSON object."""

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Entferne mögliche Markdown-Code-Block-Formatierung
            response_text = response_text.replace('```json', '').replace('```', '').strip()

            print(f"Erhaltene KI-Antwort: {response_text}")  # Debug-Ausgabe

            try:
                # Validiere und verarbeite die Antwort
                result = json.loads(response_text)

                if not isinstance(result, dict):
                    raise ValueError("Antwort ist kein JSON-Objekt")
                if not all(key in result for key in ['title', 'year', 'explanation']):
                    raise ValueError("Fehlende erforderliche Felder im JSON")

                # Stelle sicher, dass nicht der gleiche Film empfohlen wird
                if result["title"].lower() == current_movie.get('title', '').lower():
                    raise ValueError("KI hat den gleichen Film empfohlen")

                # Hole detaillierte Informationen von OMDB
                movie_details = get_movie_details(result["title"], result.get("year"))

                if movie_details:
                    return {
                        "movie": movie_details,
                        "reasoning": result["explanation"]
                    }
                else:
                    raise ValueError("Keine Filminformationen gefunden")

            except json.JSONDecodeError as e:
                print(f"JSON Parsing Fehler: {e}")
                print(f"Erhaltene Antwort: {response_text}")
                # Versuche alternative Parsing-Methode
                try:
                    # Entferne mögliche Escape-Zeichen und doppelte Anführungszeichen
                    cleaned_text = response_text.encode().decode('unicode_escape').strip('"')
                    result = json.loads(cleaned_text)
                    return {
                        "movie": get_movie_details(result["title"], result.get("year")),
                        "reasoning": result["explanation"]
                    }
                except:
                    raise ValueError(f"Ungültige AI-Antwort: {str(e)}")

        except Exception as e:
            print(f"Fehler in ai_request: {str(e)}")
            raise

    def ai_excluded_movie_request(self, data_string: str, excluded_movie: str) -> Dict:
        """
        Fordere eine Filmempfehlung von der AI an, wobei ein bestimmter Film ausgeschlossen wird.
        """
        try:
            prompt = f"""Based on these movie ratings, recommend a specific movie title and year:
            Dataset: {data_string}
            Please exclude the movie: {excluded_movie}
            Please answer with only the movie title and year in this format:
            {{"title": "Movie Title", "year": "YYYY"}}"""

            response = self.model.generate_content(prompt)
            json_string = response.text.replace("```", "").strip()

            try:
                result = json.loads(json_string)
                # Hole detaillierte Informationen von OMDB
                movie_details = get_movie_details(result["title"], result.get("year"))

                if movie_details:
                    return {
                        "movie": {
                            "title": movie_details["title"],
                            "director": movie_details["director"],
                            "year": movie_details["year"],
                            "poster": movie_details["poster"],
                            "genre": movie_details["genre"],
                            "country": movie_details["country"],
                            "plot": movie_details["plot"]
                        },
                        "reasoning": f"Basierend auf Ihren Bewertungen denke ich, dass Sie '{movie_details['title']}' mögen könnten. " +
                                   f"Der Film ist aus dem Jahr {movie_details['year']} und gehört zum Genre {movie_details['genre']}. " +
                                   f"Regie führte {movie_details['director']}."
                    }
                else:
                    raise ValueError("Keine Filminformationen gefunden")

            except json.JSONDecodeError:
                raise ValueError("Ungültige AI-Antwort")

        except Exception as e:
            print(f"Fehler in ai_excluded_movie_request: {str(e)}")
            raise

    def validate_user_question(self, question_data: Dict) -> Dict:
        """
        Überprüft eine von Benutzern vorgeschlagene Frage auf Qualität und Korrektheit.
        """
        prompt = f"""Überprüfe diese Quiz-Frage auf Qualität und Korrektheit:
        Frage: {question_data['question_text']}
        Richtige Antwort: {question_data['correct_answer']}
        Falsche Antworten:
        1. {question_data['wrong_answer_1']}
        2. {question_data['wrong_answer_2']}
        3. {question_data['wrong_answer_3']}

        Antworte im JSON-Format:
        {{
            "is_valid": true/false,
            "feedback": "Begründung für die Bewertung",
            "improved_question": null oder verbesserte Frage im gleichen Format
        }}"""

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result
        except Exception as e:
            print(f"Fehler bei der Fragen-Validierung: {str(e)}")
            return {
                "is_valid": False,
                "feedback": f"Fehler bei der Validierung: {str(e)}",
                "improved_question": None
            }

    def generate_single_quiz_question(self, context: str) -> Dict:
        """
        Generiert eine einzelne Quiz-Frage basierend auf dem Filmkontext.

        Args:
            context (str): Kontext über den Film (Titel, Plot, Jahr, etc.)

        Returns:
            Dict: Frage mit korrekter Antwort und falschen Antworten
        """
        prompt = f"""
        Basierend auf diesen Filminformationen, erstelle eine Quiz-Frage:
        {context}
        
        Erstelle eine interessante Frage mit einer korrekten Antwort und drei falschen Antworten.
        Formatiere die Antwort als JSON mit diesem Format:
        {{
            "question": "Die Frage hier",
            "correct_answer": "Die richtige Antwort",
            "wrong_answers": ["Falsche Antwort 1", "Falsche Antwort 2", "Falsche Antwort 3"]
        }}
        
        Die Frage sollte spezifisch für diesen Film sein und sich auf wichtige Details beziehen.
        Vermeide zu einfache oder zu schwierige Fragen.
        """

        try:
            response = self.model.generate_content(prompt)
            # Extrahiere JSON aus der Antwort
            response_text = response.text
            # Finde den JSON-Teil in der Antwort
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                # Fallback für den Fall, dass kein valides JSON gefunden wurde
                return {
                    "question": "In welchem Jahr wurde der Film veröffentlicht?",
                    "correct_answer": str(context.split("Year: ")[1].split("\n")[0]),
                    "wrong_answers": [
                        str(int(context.split("Year: ")[1].split("\n")[0]) - 1),
                        str(int(context.split("Year: ")[1].split("\n")[0]) - 2),
                        str(int(context.split("Year: ")[1].split("\n")[0]) + 1)
                    ]
                }
        except Exception as e:
            print(f"Fehler bei der Fragengenerierung: {e}")
            # Fallback-Frage
            return {
                "question": "Wer führte bei diesem Film Regie?",
                "correct_answer": context.split("Director: ")[1].split("\n")[0],
                "wrong_answers": ["Steven Spielberg", "Christopher Nolan", "Martin Scorsese"]
            }

    def get_similar_movie_recommendation(self, movie_data: Dict) -> Dict:
        """
        Generiert eine Filmempfehlung basierend auf einem ähnlichen Film.

        Args:
            movie_data (Dict): Daten des aktuellen Films (Titel, Genre, Beschreibung, etc.)

        Returns:
            Dict: Empfohlener Film mit Begründung
        """
        prompt = f"""
        Basierend auf diesem Film, empfehle einen ähnlichen Film:
        Titel: {movie_data.get('title', '')}
        Genre: {movie_data.get('genre', '')}
        Beschreibung: {movie_data.get('description', '')}
        Jahr: {movie_data.get('release_year', '')}
        Regisseur: {movie_data.get('director', '')}
        
        Formatiere die Antwort als JSON mit diesem Format:
        {{
            "recommendation": {{
                "title": "Titel des empfohlenen Films",
                "year": "Erscheinungsjahr",
                "director": "Regisseur",
                "reasoning": "Detaillierte Erklärung, warum dieser Film ähnlich ist",
                "similarity_aspects": [
                    "Aspekt 1, warum die Filme ähnlich sind",
                    "Aspekt 2, warum die Filme ähnlich sind",
                    "Aspekt 3, warum die Filme ähnlich sind"
                ]
            }}
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            if not isinstance(result, dict) or "recommendation" not in result:
                return {
                    "error": "Ungültiges Antwortformat",
                    "recommendation": {
                        "title": "Keine Empfehlung verfügbar",
                        "year": "",
                        "director": "",
                        "reasoning": "Es konnte keine passende Empfehlung generiert werden.",
                        "similarity_aspects": []
                    }
                }
            return result
        except Exception as e:
            print(f"Fehler bei der Filmempfehlung: {e}")
            return {
                "error": str(e),
                "recommendation": {
                    "title": "Keine Empfehlung verfügbar",
                    "year": "",
                    "director": "",
                    "reasoning": "Es trat ein Fehler bei der Empfehlungsgenerierung auf.",
                    "similarity_aspects": []
                }
            }

    def get_personalized_recommendation(self, preferences: Dict) -> Dict:
        """
        Generiert eine personalisierte Filmempfehlung basierend auf Benutzervorlieben.

        Args:
            preferences (Dict): Benutzervorlieben (Genre, Stimmung, etc.)

        Returns:
            Dict: Empfohlener Film mit Begründung
        """
        prompt = f"""
        Basierend auf diesen Vorlieben, empfehle einen passenden Film:
        Bevorzugte Genres: {preferences.get('genres', [])}
        Gewünschte Stimmung: {preferences.get('mood', '')}
        Lieblingsschauspieler: {preferences.get('actors', [])}
        Bevorzugte Jahrzehnte: {preferences.get('decades', [])}
        Zusätzliche Wünsche: {preferences.get('additional', '')}
        
        Formatiere die Antwort als JSON mit diesem Format:
        {{
            "recommendation": {{
                "title": "Titel des empfohlenen Films",
                "year": "Erscheinungsjahr",
                "genre": "Genre des Films",
                "director": "Regisseur",
                "description": "Kurze Beschreibung des Films",
                "reasoning": "Detaillierte Erklärung, warum dieser Film zu den Vorlieben passt",
                "matching_criteria": [
                    "Kriterium 1, das zu den Vorlieben passt",
                    "Kriterium 2, das zu den Vorlieben passt",
                    "Kriterium 3, das zu den Vorlieben passt"
                ]
            }}
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            if not isinstance(result, dict) or "recommendation" not in result:
                return {
                    "error": "Ungültiges Antwortformat",
                    "recommendation": {
                        "title": "Keine Empfehlung verfügbar",
                        "year": "",
                        "genre": "",
                        "director": "",
                        "description": "",
                        "reasoning": "Es konnte keine passende Empfehlung generiert werden.",
                        "matching_criteria": []
                    }
                }
            return result
        except Exception as e:
            print(f"Fehler bei der personalisierten Empfehlung: {e}")
            return {
                "error": str(e),
                "recommendation": {
                    "title": "Keine Empfehlung verfügbar",
                    "year": "",
                    "genre": "",
                    "director": "",
                    "description": "",
                    "reasoning": "Es trat ein Fehler bei der Empfehlungsgenerierung auf.",
                    "matching_criteria": []
                }
            }

    def get_movie_recommendation(self, movie_context: dict) -> Optional[Dict]:
        """
        Generiert eine Filmempfehlung basierend auf dem aktuellen Film und ähnlichen Filmen.

        Args:
            movie_context (dict): Kontext des aktuellen Films mit Titel, Genre, Beschreibung, etc.

        Returns:
            Optional[Dict]: Ein Dictionary mit der Empfehlung oder None bei Fehler
        """
        try:
            # Erstelle einen einfacheren Prompt für die KI
            prompt = f"""Du bist ein Filmexperte. Basierend auf diesem Film:
Titel: {movie_context.get('title', '')}
Genre: {movie_context.get('genre', '')}
Jahr: {movie_context.get('year', '')}
Beschreibung: {movie_context.get('description', '')}

Empfehle einen ähnlichen Film. Antworte NUR mit einem JSON-Objekt in genau diesem Format:
{{
    "title": "Name des empfohlenen Films",
    "genre": "Genre des Films",
    "year": "Jahr (nur die Zahl)",
    "explanation": "Kurze Erkl��rung, warum dieser Film eine gute Empfehlung ist"
}}"""

            # Generiere die Empfehlung
            response = self.model.generate_content(prompt)

            if not response or not response.text:
                print("Keine Antwort von der KI erhalten")
                return None

            # Versuche das JSON zu parsen
            try:
                # Bereinige die Antwort
                json_str = response.text.strip()
                if '```json' in json_str:
                    json_str = json_str.split('```json')[1].split('```')[0].strip()
                elif '```' in json_str:
                    json_str = json_str.split('```')[1].strip()

                result = json.loads(json_str)

                # Gebe ein standardisiertes Format zurück
                return {
                    'title': result.get('title', 'Kein Titel verfügbar'),
                    'genre': result.get('genre', 'Genre nicht verfügbar'),
                    'year': result.get('year', 'Jahr nicht verfügbar'),
                    'explanation': result.get('explanation', 'Keine Erklärung verfügbar')
                }
            except json.JSONDecodeError as e:
                print(f"JSON Parsing Fehler: {e}")
                print(f"Erhaltene Antwort: {response.text}")
                return None
        except Exception as e:
            print(f"Fehler bei der KI-Anfrage: {str(e)}")
            return None

    def generate_quiz_questions(self, movie_context: dict, difficulty: str) -> List[Dict]:
        """
        Generiert Quiz-Fragen basierend auf dem Filmkontext und dem gewünschten Schwierigkeitsgrad.
        """
        difficulty_guidelines = {
            'leicht': """
                - Fokus auf offensichtliche Fakten wie Hauptdarsteller, Genre, Jahr
                - Einfach zu beantwortende Fragen für Gelegenheitszuschauer
                - Keine Details aus der Handlung, die man leicht vergessen könnte
                - Falsche Antworten sollten deutlich unterscheidbar sein
            """,
            'mittel': """
                - Wichtige Handlungspunkte und zentrale Charaktere
                - Beziehungen zwischen den Charakteren
                - Bedeutende Szenen und Wendepunkte
                - Produktionsdetails wie Regisseur, Drehbuch, Musik
                - Falsche Antworten sollten plausibel aber unterscheidbar sein
            """,
            'schwer': """
                - Komplexe Handlungsdetails und Subtexte
                - Versteckte Hinweise und Easter Eggs
                - Technische Aspekte der Filmproduktion
                - Hintergrundinformationen und Trivia
                - Details zu Nebenfiguren und deren Entwicklung
                - Falsche Antworten müssen sehr plausibel sein
            """
        }

        prompt = f"""
        Generiere 10 Film-Quiz-Fragen für "{movie_context['title']}" ({movie_context['year']}).
        
        Schwierigkeitsgrad: {difficulty}
        
        Folgende Richtlinien für {difficulty} Fragen beachten:
        {difficulty_guidelines[difficulty]}
        
        Filmkontext:
        - Handlung: {movie_context['plot']}
        - Genre: {movie_context['genre']}
        - Regie: {movie_context['director']}
        
        Formatiere die Antwort als JSON-Array mit Objekten:
        [{{
            "question": "Die Frage hier",
            "correct_answer": "Die richtige Antwort",
            "wrong_answers": ["Falsche Antwort 1", "Falsche Antwort 2", "Falsche Antwort 3"]
        }}]
        
        WICHTIGE ANFORDERUNGEN:
        1. Keine Wiederholungen von Themen oder ähnlichen Fragen
        2. Alle Antworten müssen faktisch korrekt/plausibel sein
        3. Fragen müssen eindeutig beantwortbar sein
        4. Antworten sollten etwa gleich lang sein
        5. Keine offensichtlich falschen Antworten
        """

        try:
            response = self.model.generate_content(prompt)

            if not response.text:
                raise ValueError("Keine Antwort von der KI erhalten")

            # Bereinige die JSON-Antwort
            response_text = response.text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].strip()

            questions = json.loads(response_text)

            # Validiere jede Frage
            validated_questions = []
            for q in questions:
                if self._validate_question(q):
                    validated_questions.append(q)

            return validated_questions[:10]  # Maximal 10 Fragen zurückgeben

        except Exception as e:
            print(f"Fehler bei der Fragengenerierung: {str(e)}")
            return []

    def _validate_question(self, question: Dict) -> bool:
        """
        Validiert eine einzelne Frage nach verschiedenen Qualitätskriterien.
        """
        try:
            # Prüfe ob alle erforderlichen Felder vorhanden sind
            if not all(key in question for key in ['question', 'correct_answer', 'wrong_answers']):
                return False

            # Prüfe ob genau 3 falsche Antworten vorhanden sind
            if len(question['wrong_answers']) != 3:
                return False

            # Prüfe ob die Frage lang genug ist (mindestens 15 Zeichen)
            if len(question['question']) < 15:
                return False

            # Prüfe ob alle Antworten unique sind
            all_answers = [question['correct_answer']] + question['wrong_answers']
            if len(set(all_answers)) != 4:
                return False

            # Prüfe ob keine Antwort leer ist
            if any(not answer.strip() for answer in all_answers):
                return False

            return True

        except Exception:
            return False

