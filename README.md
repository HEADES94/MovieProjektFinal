# MovieProjekt

Ein modernes, KI-gestütztes Web-Tool zum Verwalten und Bewerten von Filmen und Nutzern – gebaut mit Flask, SQLAlchemy und Google Gemini AI.

## Features

- Benutzerverwaltung (anlegen, anzeigen)
- Filme hinzufügen, bewerten, kommentieren und löschen
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
- Das Projekt ist PEP8-konform und gut dokumentiert.
- Für eigene Anpassungen siehe die Dateien im `templates/` und `static/` Ordner.

## Screenshots
*(Hier kannst du eigene Screenshots einfügen)*

---
**Viel Spaß mit MovieProjekt!**

