"""
ai_request.py - Schnittstelle zur Google Gemini AI für Filmempfehlungen und Quiz-Fragen
"""
import os
import json
from typing import Optional, Dict, List
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Lade Umgebungsvariablen
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

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

class AIRequest:
    """
    Schnittstelle zur Google Gemini AI für Filmempfehlungen und Quiz-Generierung.
    """
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.0-flash",
                                         generation_config=generation_config,
                                         safety_settings=safety_settings)

    def ai_request(self, data_string: str) -> Dict:
        """
        Fordere eine Filmempfehlung von der AI an (ohne Ausschluss).
        """
        prompt = f"""Can you recommend a movie for me based on my ratings of the given dataset,
        with personal ratings form 0 to 10 as float values, please?:
        "dataset": {data_string}
        Please answer in the python dictionary format , so I can load the request into python.
        Here an example:
        {{"movie":
            {{"title": "some title",
            "director": "some director",
            "year": "some year",
            "poster": "movies's poster" as a string to load as link in html img tag,
            "imdb": "some imdb id with only numbers please",
            "country": "the country of the movie",
            "genre": "the genre of the movie",
            "plot": "the plot of the movie"}},
        "reasoning": "your reasoning text"}}
        Please only answer with the above format and nothing else."""

        response = self.model.generate_content(prompt)
        json_string = response.text.replace("```python", "").replace("```", "")
        return json.loads(json_string)

    def ai_excluded_movie_request(self, data_string: str, excluded_movie: str) -> Dict:
        """
        Fordere eine Filmempfehlung von der AI an, wobei ein bestimmter Film ausgeschlossen wird.
        """
        prompt = f"""Can you recommend a movie for me based on my ratings of the given dataset,
        with personal ratings form 0 to 10 as float values, please?:
        "dataset": {data_string}
        Please exclude the movie: {excluded_movie}
        Please answer in the python dictionary format , so I can load the request into python.
        Here an example:
        {{"movie":
            {{"title": "some title",
            "director": "some director",
            "year": "some year",
            "poster": "movies's poster" as a string to load as link in html img tag,
            "imdb": "some imdb id with only numbers please",
            "country": "the country of the movie",
            "genre": "the genre of the movie",
            "plot": "the plot of the movie"}},
        "reasoning": "your reasoning text"}}
        Please only answer with the above format and nothing else."""

        response = self.model.generate_content(prompt)
        json_string = response.text.replace("```python", "").replace("```", "")
        return json.loads(json_string)

    def generate_quiz_question(self, movie_context: str) -> Dict:
        """
        Generiert eine Quiz-Frage zu einem Film mit der Gemini AI.
        """
        prompt = f"""Basierend auf diesem Film-Kontext, erstelle eine interessante Quiz-Frage:
        {movie_context}

        Generiere eine Multiple-Choice-Frage im folgenden JSON-Format:
        {{
            "question": "Die Frage",
            "correct_answer": "Die richtige Antwort",
            "wrong_answers": ["Falsche Antwort 1", "Falsche Antwort 2", "Falsche Antwort 3"],
            "difficulty": "easy|medium|hard"
        }}

        Wichtige Regeln:
        - Die Frage sollte interessant und nicht zu offensichtlich sein
        - Die falschen Antworten müssen plausibel klingen
        - Schwierigkeit basierend auf wie spezifisch das Wissen sein muss
        - Nur JSON zurückgeben, keinen weiteren Text"""

        response = self.model.generate_content(prompt)
        json_string = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(json_string)

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
