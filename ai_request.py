"""
ai_request.py - Schnittstelle zur Google Gemini AI für Filmempfehlungen
"""
import os
import json
from typing import Optional, Dict
from dotenv import load_dotenv
from google import genai

# Lade Umgebungsvariablen
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

class AIRequest:
    """
    Schnittstelle zur Google Gemini AI, um Filmempfehlungen zu generieren.
    """
    def __init__(self):
        self.genai_client = client

    def ai_request(self, data_string: str) -> Dict:
        """
        Fordere eine Filmempfehlung von der AI an (ohne Ausschluss).
        Args:
            data_string (str): Die Nutzerdaten als String.
        Returns:
            dict: Die empfohlene Filmstruktur und Begründung.
        """
        response = self.genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                """Can you recommend a movie for me based on my ratings of the given dataset,
                with personal ratings form 0 to 10 as float values, please?:
                \"dataset\":""" + data_string + """
                Please answer in the python dictionary format , so I can load the request into python.
                Here an example: 
                {\"movie\":
                    {\"title\": \"some title\",
                    \"director\": \"some director\",
                    \"year\": \"some year\",
                    \"poster\": \"movies's poster\" as a string to load as link in html img tag,
                    \"imdb\": \"some imdb id with only numbers please\",
                    \"country\": \"the country of the movie,\n\"genre\": \"the genre of the movie\",
                    \"plot\": \"the plot of the movie\",},
                \"reasoning\": \"your reasoning text\"} 
                Please only answer with the above format and nothing else.
                """
            )
        )
        json_string = response.text.replace("```python", "").replace("```", "")
        movie_recommendation = json.loads(json_string)
        return movie_recommendation

    def ai_excluded_movie_request(self, data_string: str, excluded_movie: str) -> Dict:
        """
        Fordere eine Filmempfehlung von der AI an, wobei ein bestimmter Film ausgeschlossen wird.
        Args:
            data_string (str): Die Nutzerdaten als String.
            excluded_movie (str): Titel des auszuschließenden Films.
        Returns:
            dict: Die empfohlene Filmstruktur und Begründung.
        """
        response = self.genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                """Can you recommend a movie for me based on my ratings of the given dataset,
                with personal ratings form 0 to 10 as float values, please?:
                \"dataset\":""" + data_string + """ and excluding the movie: """ + excluded_movie + """
                Please answer in the python dictionary format , so I can load the request into python.
                Here an example: 
                {\"movie\":
                    {\"title\": \"some title\",
                    \"director\": \"some director\",
                    \"year\": \"some year\",
                    \"poster\": \"movies's poster\" as a string to load as link in html img tag,
                    \"imdb\": \"some imdb id with only numbers please\",
                    \"country\": \"the country of the movie,\n\"genre\": \"the genre of the movie\",
                    \"plot\": \"the plot of the movie\",},
                \"reasoning\": \"your reasoning text\"} 
                Please only answer with the above format and nothing else.
                """
            )
        )
        json_string = response.text.replace("```python", "").replace("```", "")
        movie_recommendation = json.loads(json_string)
        return movie_recommendation
