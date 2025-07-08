"""Logging configuration for the MovieProjekt."""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(app):
    """Configure the logging system."""
    if not os.path.exists('logs'):
        os.mkdir('logs')

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    file_handler = RotatingFileHandler(
        'logs/movieapp.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=10240000,
        backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)

    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)

    logging.getLogger('werkzeug').setLevel(logging.WARNING)


def log_user_action(user_id, action, details=None):
    """Log user actions."""
    message = f"User {user_id}: {action}"
    if details:
        message += f" - {details}"
    logging.info(message)


def log_database_operation(operation, table, success=True, error=None):
    """Log database operations."""
    if success:
        logging.info(f"DB Operation: {operation} on {table} - SUCCESS")
    else:
        logging.error(f"DB Operation: {operation} on {table} - FAILED: {error}")


def log_api_request(endpoint, method, user_id=None, response_time=None):
    """Log API requests."""
    message = f"API: {method} {endpoint}"
    if user_id:
        message += f" (User: {user_id})"
    if response_time:
        message += f" - {response_time:.2f}ms"
    logging.info(message)
