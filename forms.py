"""
forms.py - WTForms für bessere Validierung
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, PasswordField, EmailField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, ValidationError
from data_models import User
from datamanager.sqlite_data_manager import SQliteDataManager

class RegistrationForm(FlaskForm):
    username = StringField('Benutzername', validators=[
        DataRequired(message='Benutzername ist erforderlich'),
        Length(min=3, max=20, message='Benutzername muss zwischen 3 und 20 Zeichen lang sein')
    ])
    email = EmailField('E-Mail', validators=[
        DataRequired(message='E-Mail ist erforderlich'),
        Email(message='Ungültige E-Mail-Adresse')
    ])
    password = PasswordField('Passwort', validators=[
        DataRequired(message='Passwort ist erforderlich'),
        Length(min=8, message='Passwort muss mindestens 8 Zeichen lang sein')
    ])
    confirm_password = PasswordField('Passwort bestätigen', validators=[
        DataRequired(message='Passwort-Bestätigung ist erforderlich'),
        EqualTo('password', message='Passwörter müssen übereinstimmen')
    ])

    def validate_username(self, username):
        data_manager = SQliteDataManager("sqlite:///movie_app.db")
        with data_manager.SessionFactory() as session:
            user = session.query(User).filter_by(username=username.data).first()
            if user:
                raise ValidationError('Benutzername bereits vergeben.')

    def validate_email(self, email):
        data_manager = SQliteDataManager("sqlite:///movie_app.db")
        with data_manager.SessionFactory() as session:
            user = session.query(User).filter_by(email=email.data).first()
            if user:
                raise ValidationError('E-Mail bereits registriert.')

class LoginForm(FlaskForm):
    email = EmailField('E-Mail', validators=[
        DataRequired(message='E-Mail ist erforderlich'),
        Email(message='Ungültige E-Mail-Adresse')
    ])
    password = PasswordField('Passwort', validators=[
        DataRequired(message='Passwort ist erforderlich')
    ])

class ReviewForm(FlaskForm):
    rating = SelectField('Bewertung', choices=[
        (1, '1 Stern'), (2, '2 Sterne'), (3, '3 Sterne'),
        (4, '4 Sterne'), (5, '5 Sterne')
    ], coerce=int, validators=[DataRequired()])
    comment = TextAreaField('Kommentar', validators=[
        Length(max=500, message='Kommentar darf maximal 500 Zeichen lang sein')
    ])

class MovieForm(FlaskForm):
    title = StringField('Filmtitel', validators=[
        DataRequired(message='Filmtitel ist erforderlich'),
        Length(min=1, max=255, message='Titel muss zwischen 1 und 255 Zeichen lang sein')
    ])

class SuggestQuestionForm(FlaskForm):
    movie_id = SelectField('Film', coerce=int, validators=[DataRequired()])
    question_text = TextAreaField('Frage', validators=[
        DataRequired(message='Frage ist erforderlich'),
        Length(min=10, max=500, message='Frage muss zwischen 10 und 500 Zeichen lang sein')
    ])
    correct_answer = StringField('Richtige Antwort', validators=[
        DataRequired(message='Richtige Antwort ist erforderlich'),
        Length(min=1, max=255, message='Antwort muss zwischen 1 und 255 Zeichen lang sein')
    ])
    wrong_answer1 = StringField('Falsche Antwort 1', validators=[
        DataRequired(message='Falsche Antwort 1 ist erforderlich'),
        Length(min=1, max=255, message='Antwort muss zwischen 1 und 255 Zeichen lang sein')
    ])
    wrong_answer2 = StringField('Falsche Antwort 2', validators=[
        DataRequired(message='Falsche Antwort 2 ist erforderlich'),
        Length(min=1, max=255, message='Antwort muss zwischen 1 und 255 Zeichen lang sein')
    ])
    wrong_answer3 = StringField('Falsche Antwort 3', validators=[
        DataRequired(message='Falsche Antwort 3 ist erforderlich'),
        Length(min=1, max=255, message='Antwort muss zwischen 1 und 255 Zeichen lang sein')
    ])
