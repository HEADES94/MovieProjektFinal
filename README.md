# MovieProjekt

Ein modernes, KI-gestütztes Web-Tool zum Verwalten, Bewerten und Quizzen rund um Filme – gebaut mit Flask, SQLAlchemy und Google Gemini AI.

## Features

- Benutzerverwaltung (Registrierung, Login, Profil)
- Filme hinzufügen, bewerten, kommentieren und löschen
- Quiz-Modul: Quiz zu Filmen spielen, Schwierigkeitsgrade, Highscores
- Achievements: Erfolge für Quiz, Watchlist und Kommentare/Likes
- Watchlist: Eigene Watchlist verwalten
- Kommentare & Likes: Filme kommentieren, Erfolge für Viel-Kommentierer
- KI-basierte Filmempfehlungen (Google Gemini)
- Responsive, modernes Glassmorphism-Design mit Dark/Light Mode
- Animierter Hintergrund und Theme-Toggle
- Übersichtliche, intuitive Oberfläche

## Getting Started

1. **Repository klonen**
```bash
git clone <dein-repo-url>
cd MovieProjekt
```
2. **Abhängigkeiten installieren**
```bash
pip install -r requirements.txt
```
3. **.env Datei anlegen**
Lege eine `.env` Datei im Projektverzeichnis an mit folgendem Inhalt:
```
OMDB_API_KEY=dein_omdb_api_key
GOOGLE_API_KEY=dein_google_gemini_api_key
```
4. **App starten**
```bash
python app.py
```
5. **Im Browser öffnen**
[http://127.0.0.1:5000](http://127.0.0.1:5000)

## Hinweise
- Für KI-Empfehlungen benötigst du einen Google Gemini API Key.
- Für Filmdaten benötigst du einen OMDB API Key ([omdbapi.com](https://www.omdbapi.com/apikey.aspx)).
- CSRF-Schutz ist aktiv: Bei allen POST-Formularen wird ein CSRF-Token benötigt.
- Das Projekt ist PEP8-konform und gut dokumentiert.
- Für eigene Anpassungen siehe die Dateien im `templates/` und `static/` Ordner.
- Quiz, Watchlist und Kommentare vergeben Achievements automatisch.

---
**Viel Spaß mit MovieProjekt!**
