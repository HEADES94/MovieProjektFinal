"""
Security Utils - Input Sanitization und XSS-Schutz
"""
import re
import html
from typing import Any, Dict, Optional
from flask import request
import bleach

class SecurityValidator:
    """Klasse für Sicherheitsvalidierung und Input Sanitization"""

    # Erlaubte HTML-Tags für Benutzerinhalte
    ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']

    @staticmethod
    def sanitize_html(content: str) -> str:
        """Bereinigt HTML-Content von schädlichen Tags"""
        if not content:
            return ""
        return bleach.clean(content, tags=SecurityValidator.ALLOWED_TAGS, strip=True)

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validiert E-Mail-Format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_username(username: str) -> bool:
        """Validiert Username (nur Buchstaben, Zahlen, Unterstriche)"""
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, username))

    @staticmethod
    def escape_sql_wildcards(text: str) -> str:
        """Escaped SQL-Wildcards für LIKE-Queries"""
        return text.replace('%', '\\%').replace('_', '\\_')

    @staticmethod
    def validate_rating(rating: Any) -> bool:
        """Validiert Film-Rating (1-5)"""
        try:
            rating = int(rating)
            return 1 <= rating <= 5
        except (ValueError, TypeError):
            return False

    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """Bereinigt Suchanfragen"""
        if not query:
            return ""

        # Entferne gefährliche Zeichen
        query = re.sub(r'[<>"\']', '', query)

        # Begrenze Länge
        query = query[:100]

        # Escape für SQL LIKE
        return SecurityValidator.escape_sql_wildcards(query.strip())

def require_https():
    """Erzwingt HTTPS in Production"""
    if not request.is_secure and not request.headers.get('X-Forwarded-Proto', 'http') == 'https':
        if current_app.env == 'production':
            return redirect(request.url.replace('http://', 'https://', 1), code=301)

def add_security_headers(response):
    """Fügt Sicherheits-Headers hinzu"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self';"
    )
    return response
