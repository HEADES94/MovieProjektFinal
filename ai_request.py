"""
ai_request.py - Schnittstelle zur Google Gemini AI für Filmempfehlungen und Quiz-Fragen
"""
import os
import json
import requests
from typing import Optional, Dict, List
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Lade Umgebungsvariablen
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# TMDB API Basis-URL
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Konfiguriere die Google AI
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

genai.configure(api_key=API_KEY)

# Liste verfügbare Modelle
print("Verfügbare Modelle:")
for m in genai.list_models():
    print(f"- {m.name}")

def get_movie_details(title: str, year: str = None) -> Dict:
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

        return None

    except Exception as e:
        print(f"Fehler beim Abrufen der Film-Daten: {str(e)}")
        return None

class AIRequest:
    """
    Schnittstelle zur Google Gemini AI für Filmempfehlungen und Quiz-Generierung.
    """
    def __init__(self):
        self.model = genai.GenerativeModel("models/gemini-2.0-flash-lite",
                                         generation_config=generation_config,
                                         safety_settings=safety_settings)

    def ai_request(self, data_string: str) -> Dict:
        """
        Fordere eine Filmempfehlung von der AI an (ohne Ausschluss).
        """
        try:
            # Extrahiere den aktuellen Filmtitel aus dem Kontext
            current_title = data_string.split(":")[0].strip() if ":" in data_string else data_string

            prompt = f"""Based on this movie, recommend a DIFFERENT movie that is similar in style or theme:
            Current Movie: {current_title}
            Important: DO NOT recommend the same movie ({current_title}). Choose a different but similar movie.
            Please answer with only the movie title and year in this format:
            {{"title": "Movie Title", "year": "YYYY"}}"""

            response = self.model.generate_content(prompt)
            json_string = response.text.replace("```", "").strip()

            try:
                result = json.loads(json_string)
                # Stelle sicher, dass nicht der gleiche Film empfohlen wird
                if result["title"].lower() == current_title.lower():
                    raise ValueError("KI hat den gleichen Film empfohlen")

                # Hole detaillierte Informationen von OMDB
                movie_details = get_movie_details(result["title"], result.get("year"))

                if movie_details:
                    # Generiere eine spezifische Begründung
                    reasoning_prompt = f"""Given these two movies:
                    1. {current_title}
                    2. {movie_details['title']} ({movie_details['year']})
                    
                    Write a SHORT explanation (1-2 sentences) why someone who likes the first movie would enjoy the second movie."""

                    reasoning_response = self.model.generate_content(reasoning_prompt)
                    custom_reasoning = reasoning_response.text.strip()

                    return {
                        "movie": movie_details,
                        "reasoning": custom_reasoning
                    }
                else:
                    raise ValueError("Keine Filminformationen gefunden")

            except json.JSONDecodeError:
                raise ValueError("Ungültige AI-Antwort")

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

    def generate_quiz_question(self, movie_context: str) -> Dict:
        """
        Generiert eine Quiz-Frage basierend auf dem Filmkontext.
        """
        try:
            prompt = f"""Based on this movie information, create one interesting quiz question:
            {movie_context}

            Create a challenging but fair multiple choice question about this specific movie.
            Focus on important details from the plot, characters, or production.

            Return EXACTLY this JSON format:
            {{
                "question": "Write the actual question here",
                "correct_answer": "Write the correct answer here",
                "wrong_answers": [
                    "First wrong but plausible answer",
                    "Second wrong but plausible answer",
                    "Third wrong but plausible answer"
                ]
            }}
            """

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Extrahiere JSON aus der Antwort
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1]

            print(f"AI Response: {response_text}")  # Debug-Ausgabe

            try:
                quiz_data = json.loads(response_text.strip())
                # Validiere die Struktur
                if not all(key in quiz_data for key in ['question', 'correct_answer', 'wrong_answers']):
                    raise ValueError("Ungültiges Fragen-Format")

                if len(quiz_data['wrong_answers']) < 3:
                    raise ValueError("Nicht genug falsche Antworten")

                return {
                    "question": quiz_data["question"],
                    "correct_answer": quiz_data["correct_answer"],
                    "wrong_answers": quiz_data["wrong_answers"][:3]  # Nimm maximal 3 falsche Antworten
                }
            except json.JSONDecodeError:
                print(f"JSON Parse Error. Raw response: {response_text}")
                raise ValueError("Ungültiges JSON-Format in der AI-Antwort")

        except Exception as e:
            print(f"Fehler bei der Quiz-Fragen-Generierung: {str(e)}")
            # Erstelle eine Standard-Frage als Fallback
            movie_title = movie_context.split("Title: ")[1].split("\n")[0] if "Title: " in movie_context else "der Film"
            movie_year = movie_context.split("Year: ")[1].split("\n")[0] if "Year: " in movie_context else "2000"
            movie_director = movie_context.split("Director: ")[1].split("\n")[0] if "Director: " in movie_context else "unbekannt"

            return {
                "question": f"Wer führte bei {movie_title} Regie?",
                "correct_answer": movie_director,
                "wrong_answers": [
                    "Steven Spielberg",
                    "Christopher Nolan",
                    "Martin Scorsese"
                ]
            }

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

        response = self.model.generate_content(prompt)
        return json.loads(response.text)

    def generate_quiz_question(self, context: str) -> Dict:
        """
        Generiert eine Quiz-Frage basierend auf dem Filmkontext.

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
                "reasoning": "Detaillierte Erklärung, warum dieser Film ähnlich ist und empfohlen wird",
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
            return json.loads(response.text)
        except Exception as e:
            print(f"Fehler bei der Filmempfehlung: {e}")
            return None

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
            return json.loads(response.text)
        except Exception as e:
            print(f"Fehler bei der personalisierten Empfehlung: {e}")
            return None

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
    "explanation": "Kurze Erklärung, warum dieser Film eine gute Empfehlung ist"
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
                    'explanation': result.get('explanation', 'Keine Erklärung verf��gbar')
                }
            except json.JSONDecodeError as e:
                print(f"JSON Parsing Fehler: {e}")
                print(f"Erhaltene Antwort: {response.text}")
                return None
        except Exception as e:
            print(f"Fehler bei der KI-Anfrage: {str(e)}")
            return None
