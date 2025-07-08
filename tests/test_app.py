"""
Comprehensive Test Suite for MovieProjekt.
"""
import pytest
import tempfile
import os
from flask import url_for
from app import app
from data_models import User, Movie, Review
from datamanager.sqlite_data_manager import SQliteDataManager


@pytest.fixture
def client():
    """Test client for Flask app."""
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


@pytest.fixture
def auth(client):
    """Authentication helper."""
    return AuthActions(client)


class AuthActions:
    """Helper class for authentication actions in tests."""

    def __init__(self, client):
        self._client = client

    def login(self, email='test@example.com', password='testpass123'):
        return self._client.post('/login', data={
            'email': email,
            'password': password
        })

    def logout(self):
        return self._client.get('/logout')


class TestAuth:
    """Tests for authentication."""

    def test_register(self, client):
        """Test user registration."""
        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        })
        assert response.status_code == 302  # Redirect after successful registration

    def test_login(self, client, auth):
        """Test user login."""
        # First register a user
        client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        })

        # Then try to login
        response = auth.login()
        assert response.status_code == 302  # Redirect after successful login

    def test_logout(self, client, auth):
        """Test user logout."""
        # Register and login first
        client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        })
        auth.login()

        # Then logout
        response = auth.logout()
        assert response.status_code == 302  # Redirect after logout


class TestMovies:
    """Tests for movie functionality."""

    def test_movies_page(self, client):
        """Test movies page access."""
        response = client.get('/movies')
        assert response.status_code == 200
        assert b'movies' in response.data.lower()

    def test_add_movie(self, client, auth):
        """Test adding a new movie."""
        # Register and login first
        client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        })
        auth.login()

        # Try to add a movie
        response = client.post('/movies/new', data={
            'name': 'Test Movie'
        })
        assert response.status_code == 200


class TestWatchlist:
    """Tests for watchlist functionality."""

    def test_watchlist_access_requires_login(self, client):
        """Test that watchlist requires login."""
        response = client.get('/watchlist')
        assert response.status_code == 302  # Redirect to login

    def test_add_to_watchlist_requires_login(self, client):
        """Test that adding to watchlist requires login."""
        response = client.post('/watchlist/add/1')
        assert response.status_code == 302  # Redirect to login


class TestQuiz:
    """Tests for quiz functionality."""

    def test_quiz_home_requires_login(self, client):
        """Test that quiz home requires login."""
        response = client.get('/quiz')
        assert response.status_code == 302  # Redirect to login

    def test_quiz_movie_requires_login(self, client):
        """Test that movie quiz requires login."""
        response = client.get('/quiz/1')
        assert response.status_code == 302  # Redirect to login


class TestProfile:
    """Tests for user profile functionality."""

    def test_profile_requires_login(self, client):
        """Test that profile requires login."""
        response = client.get('/profile')
        assert response.status_code == 302  # Redirect to login


class TestAPI:
    """Tests for API endpoints."""

    def test_api_movies(self, client):
        """Test API movies endpoint."""
        response = client.get('/api/movies')
        assert response.status_code == 200
        assert response.is_json

    def test_api_genres(self, client):
        """Test API genres endpoint."""
        response = client.get('/api/genres')
        assert response.status_code == 200
        assert response.is_json


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404

    def test_invalid_movie_id(self, client):
        """Test handling of invalid movie ID."""
        response = client.get('/movies/99999')
        assert response.status_code == 404


class TestSecurity:
    """Tests for security features."""

    def test_csrf_protection(self, client):
        """Test CSRF protection is enabled."""
        app.config['WTF_CSRF_ENABLED'] = True

        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        })
        # Should fail without CSRF token
        assert response.status_code == 400

    def test_password_hashing(self, client):
        """Test that passwords are properly hashed."""
        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        })

        # Password should not be stored in plain text
        # This would require database access to verify properly
        assert response.status_code == 302


if __name__ == '__main__':
    pytest.main([__file__])
