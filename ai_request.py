"""
Interface to Google Gemini AI for movie recommendations and quiz questions.
"""
import os
import json
import requests
from typing import Optional, Dict, List
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# TMDB API base URL
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Configure Google AI
generation_config = GenerationConfig(
    temperature=0.9,
    top_p=1,
    top_k=1,
    max_output_tokens=2048,
)

genai.configure(api_key=API_KEY)

# List available models and select the correct one
available_models = [m.name for m in genai.list_models()]
print("Available models:", available_models)

def get_movie_details(title: str, year: str = None) -> Optional[Dict]:
    """
    Get detailed movie information from OMDB API.
    """
    omdb_url = "http://www.omdbapi.com/"

    try:
        # OMDB API query
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
                "plot": omdb_data.get("Plot", "No description available.")
            }

        return {"error": "Movie not found"}

    except Exception as e:
        print(f"Error fetching movie data: {str(e)}")
        return {"error": f"API error: {str(e)}"}

class AIRequest:
    """
    Interface to Google Gemini AI for movie recommendations and quiz generation.
    """
    def __init__(self):
        try:
            # Use the available model "models/gemini-2.0-flash"
            self.model = genai.GenerativeModel(
                "models/gemini-2.0-flash",
                generation_config=generation_config
            )
            print("AI model successfully initialized")
        except Exception as e:
            print(f"Error initializing model: {str(e)}")
            raise

    def ai_request(self, data_string: str) -> Dict:
        """
        Request a movie recommendation from the AI (without exclusion).
        """
        try:
            # Extract the current movie title and other information from the context
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

            # Remove possible Markdown code block formatting
            response_text = response_text.replace('```json', '').replace('```', '').strip()

            print(f"Received AI response: {response_text}")  # Debug output

            try:
                # Validate and process the response
                result = json.loads(response_text)

                if not isinstance(result, dict):
                    raise ValueError("Response is not a JSON object")
                if not all(key in result for key in ['title', 'year', 'explanation']):
                    raise ValueError("Missing required fields in JSON")

                # Ensure that the same movie is not recommended
                if result["title"].lower() == current_movie.get('title', '').lower():
                    raise ValueError("AI recommended the same movie")

                # Get detailed information from OMDB
                movie_details = get_movie_details(result["title"], result.get("year"))

                if movie_details:
                    return {
                        "movie": movie_details,
                        "reasoning": result["explanation"]
                    }
                else:
                    raise ValueError("No movie information found")

            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Received response: {response_text}")
                # Try alternative parsing method
                try:
                    # Remove possible escape characters and double quotes
                    cleaned_text = response_text.encode().decode('unicode_escape').strip('"')
                    result = json.loads(cleaned_text)
                    return {
                        "movie": get_movie_details(result["title"], result.get("year")),
                        "reasoning": result["explanation"]
                    }
                except:
                    raise ValueError(f"Invalid AI response: {str(e)}")

        except Exception as e:
            print(f"Error in ai_request: {str(e)}")
            raise

    def ai_excluded_movie_request(self, data_string: str, excluded_movie: str) -> Dict:
        """
        Request a movie recommendation from the AI, excluding a specific movie.
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
                # Get detailed information from OMDB
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
                        "reasoning": f"Based on your ratings, I think you might like '{movie_details['title']}'. " +
                                   f"The movie is from {movie_details['year']} and belongs to the genre {movie_details['genre']}. " +
                                   f"It was directed by {movie_details['director']}."
                    }
                else:
                    raise ValueError("No movie information found")

            except json.JSONDecodeError:
                raise ValueError("Invalid AI response")

        except Exception as e:
            print(f"Error in ai_excluded_movie_request: {str(e)}")
            raise

    def validate_user_question(self, question_data: Dict) -> Dict:
        """
        Checks a user-suggested question for quality and correctness.
        """
        prompt = f"""Check this quiz question for quality and correctness:
        Question: {question_data['question_text']}
        Correct Answer: {question_data['correct_answer']}
        Wrong Answers:
        1. {question_data['wrong_answer_1']}
        2. {question_data['wrong_answer_2']}
        3. {question_data['wrong_answer_3']}

        Respond in JSON format:
        {{
            "is_valid": true/false,
            "feedback": "Reason for the evaluation",
            "improved_question": null or improved question in the same format
        }}"""

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result
        except Exception as e:
            print(f"Error validating question: {str(e)}")
            return {
                "is_valid": False,
                "feedback": f"Validation error: {str(e)}",
                "improved_question": None
            }

    def generate_single_quiz_question(self, context: str) -> Dict:
        """
        Generates a single quiz question based on the movie context.

        Args:
            context (str): Context about the movie (title, plot, year, etc.)

        Returns:
            Dict: Question with correct answer and wrong answers
        """
        prompt = f"""
        Based on this movie information, create a quiz question:
        {context}
        
        Create an interesting question with a correct answer and three wrong answers.
        Format the answer as JSON with this structure:
        {{
            "question": "The question here",
            "correct_answer": "The correct answer",
            "wrong_answers": ["Wrong answer 1", "Wrong answer 2", "Wrong answer 3"]
        }}
        
        The question should be specific to this movie and relate to important details.
        Avoid too easy or too difficult questions.
        """

        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from the response
            response_text = response.text
            # Find the JSON part in the response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                # Fallback in case no valid JSON was found
                return {
                    "question": "In which year was the movie released?",
                    "correct_answer": str(context.split("Year: ")[1].split("\n")[0]),
                    "wrong_answers": [
                        str(int(context.split("Year: ")[1].split("\n")[0]) - 1),
                        str(int(context.split("Year: ")[1].split("\n")[0]) - 2),
                        str(int(context.split("Year: ")[1].split("\n")[0]) + 1)
                    ]
                }
        except Exception as e:
            print(f"Error generating question: {e}")
            # Fallback question
            return {
                "question": "Who directed this movie?",
                "correct_answer": context.split("Director: ")[1].split("\n")[0],
                "wrong_answers": ["Steven Spielberg", "Christopher Nolan", "Martin Scorsese"]
            }

    def get_similar_movie_recommendation(self, movie_data: Dict) -> Dict:
        """
        Generates a movie recommendation based on a similar movie.

        Args:
            movie_data (Dict): Data of the current movie (title, genre, description, etc.)

        Returns:
            Dict: Recommended movie with reasoning
        """
        prompt = f"""
        Based on this movie, recommend a similar movie:
        Title: {movie_data.get('title', '')}
        Genre: {movie_data.get('genre', '')}
        Description: {movie_data.get('description', '')}
        Year: {movie_data.get('release_year', '')}
        Director: {movie_data.get('director', '')}
        
        Format the response as JSON with this structure:
        {{
            "recommendation": {{
                "title": "Title of the recommended movie",
                "year": "Release year",
                "director": "Director",
                "reasoning": "Detailed explanation why this movie is similar",
                "similarity_aspects": [
                    "Aspect 1, why the movies are similar",
                    "Aspect 2, why the movies are similar",
                    "Aspect 3, why the movies are similar"
                ]
            }}
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            if not isinstance(result, dict) or "recommendation" not in result:
                return {
                    "error": "Invalid response format",
                    "recommendation": {
                        "title": "No recommendation available",
                        "year": "",
                        "director": "",
                        "reasoning": "No suitable recommendation could be generated.",
                        "similarity_aspects": []
                    }
                }
            return result
        except Exception as e:
            print(f"Error in movie recommendation: {e}")
            return {
                "error": str(e),
                "recommendation": {
                    "title": "No recommendation available",
                    "year": "",
                    "director": "",
                    "reasoning": "An error occurred while generating the recommendation.",
                    "similarity_aspects": []
                }
            }

    def get_personalized_recommendation(self, preferences: Dict) -> Dict:
        """
        Generates a personalized movie recommendation based on user preferences.

        Args:
            preferences (Dict): User preferences (genre, mood, etc.)

        Returns:
            Dict: Recommended movie with reasoning
        """
        prompt = f"""
        Based on these preferences, recommend a suitable movie:
        Preferred Genres: {preferences.get('genres', [])}
        Desired Mood: {preferences.get('mood', '')}
        Favorite Actors: {preferences.get('actors', [])}
        Preferred Decades: {preferences.get('decades', [])}
        Additional Requests: {preferences.get('additional', '')}
        
        Format the response as JSON with this structure:
        {{
            "recommendation": {{
                "title": "Title of the recommended movie",
                "year": "Release year",
                "genre": "Genre of the movie",
                "director": "Director",
                "description": "Short description of the movie",
                "reasoning": "Detailed explanation why this movie fits the preferences",
                "matching_criteria": [
                    "Criterion 1, that matches the preferences",
                    "Criterion 2, that matches the preferences",
                    "Criterion 3, that matches the preferences"
                ]
            }}
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            if not isinstance(result, dict) or "recommendation" not in result:
                return {
                    "error": "Invalid response format",
                    "recommendation": {
                        "title": "No recommendation available",
                        "year": "",
                        "genre": "",
                        "director": "",
                        "description": "",
                        "reasoning": "No suitable recommendation could be generated.",
                        "matching_criteria": []
                    }
                }
            return result
        except Exception as e:
            print(f"Error in personalized recommendation: {e}")
            return {
                "error": str(e),
                "recommendation": {
                    "title": "No recommendation available",
                    "year": "",
                    "genre": "",
                    "director": "",
                    "description": "",
                    "reasoning": "An error occurred while generating the recommendation.",
                    "matching_criteria": []
                }
            }

    def get_movie_recommendation(self, movie_context: dict) -> Optional[Dict]:
        """
        Generates a movie recommendation based on the current movie and similar movies.

        Args:
            movie_context (dict): Context of the current movie with title, genre, description, etc.

        Returns:
            Optional[Dict]: A dictionary with the recommendation or None if failed
        """
        try:
            # Create a simpler prompt for the AI
            prompt = f"""You are a movie expert. Based on this movie:
Title: {movie_context.get('title', '')}
Genre: {movie_context.get('genre', '')}
Year: {movie_context.get('year', '')}
Description: {movie_context.get('description', '')}

Recommend a similar movie. Respond ONLY with a JSON object in exactly this format:
{{
    "title": "Name of the recommended movie",
    "genre": "Genre of the movie",
    "year": "Year (only the number)",
    "explanation": "Short explanation why this movie is a good recommendation"
}}"""

            # Generate the recommendation
            response = self.model.generate_content(prompt)

            if not response or not response.text:
                print("No response received from the AI")
                return None

            # Try to parse the JSON
            try:
                # Clean the response
                json_str = response.text.strip()
                if '```json' in json_str:
                    json_str = json_str.split('```json')[1].split('```')[0].strip()
                elif '```' in json_str:
                    json_str = json_str.split('```')[1].strip()

                result = json.loads(json_str)

                # Return a standardized format
                return {
                    'title': result.get('title', 'No title available'),
                    'genre': result.get('genre', 'Genre not available'),
                    'year': result.get('year', 'Year not available'),
                    'explanation': result.get('explanation', 'No explanation available')
                }
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Received response: {response.text}")
                return None
        except Exception as e:
            print(f"Error in AI request: {str(e)}")
            return None

    def generate_quiz_questions(self, movie_context: dict, difficulty: str) -> List[Dict]:
        """
        Generates quiz questions based on the movie context and desired difficulty level.
        """
        difficulty_guidelines = {
            'leicht': """
                - Focus on obvious facts like main actors, genre, year
                - Easy to answer questions for casual viewers
                - No details from the plot that could be easily forgotten
                - Wrong answers should be clearly distinguishable
            """,
            'mittel': """
                - Important plot points and central characters
                - Relationships between the characters
                - Significant scenes and turning points
                - Production details like director, script, music
                - Wrong answers should be plausible but distinguishable
            """,
            'schwer': """
                - Complex plot details and subtexts
                - Hidden clues and Easter eggs
                - Technical aspects of film production
                - Background information and trivia
                - Details about supporting characters and their development
                - Wrong answers must be very plausible
            """
        }

        prompt = f"""
        Generate 10 film quiz questions for "{movie_context['title']}" ({movie_context['year']}).
        
        Difficulty level: {difficulty}
        
        Follow these guidelines for {difficulty} questions:
        {difficulty_guidelines[difficulty]}
        
        Movie context:
        - Plot: {movie_context['plot']}
        - Genre: {movie_context['genre']}
        - Director: {movie_context['director']}
        
        Format the response as a JSON array with objects:
        [{{
            "question": "The question here",
            "correct_answer": "The correct answer",
            "wrong_answers": ["Wrong answer 1", "Wrong answer 2", "Wrong answer 3"]
        }}]
        
        IMPORTANT REQUIREMENTS:
        1. No repetitions of topics or similar questions
        2. All answers must be factually correct/plausible
        3. Questions must be unambiguously answerable
        4. Answers should be of approximately equal length
        5. No obviously wrong answers
        """

        try:
            response = self.model.generate_content(prompt)

            if not response.text:
                raise ValueError("No response received from the AI")

            # Clean the JSON response
            response_text = response.text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].strip()

            questions = json.loads(response_text)

            # Validate each question
            validated_questions = []
            for q in questions:
                if self._validate_question(q):
                    validated_questions.append(q)

            return validated_questions[:10]  # Return a maximum of 10 questions

        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            return []

    def _validate_question(self, question: Dict) -> bool:
        """
        Validates a single question against various quality criteria.
        """
        try:
            # Check if all required fields are present
            if not all(key in question for key in ['question', 'correct_answer', 'wrong_answers']):
                return False

            # Check if exactly 3 wrong answers are present
            if len(question['wrong_answers']) != 3:
                return False

            # Check if the question is long enough (at least 15 characters)
            if len(question['question']) < 15:
                return False

            # Check if all answers are unique
            all_answers = [question['correct_answer']] + question['wrong_answers']
            if len(set(all_answers)) != 4:
                return False

            # Check if no answer is empty
            if any(not answer.strip() for answer in all_answers):
                return False

            return True

        except Exception:
            return False
