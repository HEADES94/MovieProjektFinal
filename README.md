# MovieProjekt - KI-gestützte Film-Management-App

Ein modernes, vollständig ausgestattetes Web-Tool zum Verwalten, Bewerten und Quizzen rund um Filme – gebaut mit Flask, SQLAlchemy, PostgreSQL und Google Gemini AI.

## 🎬 Features

### Core Features
- **Benutzerverwaltung**: Sichere Registrierung, Login und Profilverwaltung mit bcrypt-Passwort-Hashing
- **Filmverwaltung**: Filme hinzufügen, bewerten, kommentieren und verwalten
- **Erweiterte Suchfunktion**: Filme nach Titel, Genre, Regisseur und Jahr filtern
- **Responsive Design**: Modernes Glassmorphism-Design mit Dark/Light Mode Toggle
- **Theme-System**: Vollständig funktionsfähiges Dark/Light/System-Theme mit automatischer Speicherung

### Quiz-System
- **Film-spezifische Quiz**: Individuelle Quiz für jeden Film mit verschiedenen Schwierigkeitsgraden
- **Schwierigkeitsgrade**: Einfach, Mittel, Schwer mit unterschiedlichen Punktesystemen
- **Detaillierte Statistiken**: Film-spezifische Quiz-Statistiken und Fortschrittsverfolgung
- **Achievement-System**: Erfolge für Quiz-Leistungen, Watchlist-Aktivitäten und Reviews

### KI-Integration
- **Google Gemini AI**: KI-basierte Filmempfehlungen basierend auf Benutzerpräferenzen
- **Automatische Fragengeneration**: KI-generierte Quiz-Fragen für bessere Spielerfahrung
- **Intelligente Empfehlungen**: Personalisierte Filmvorschläge basierend auf Bewertungshistorie

### Social Features
- **Watchlist**: Persönliche Watchlist mit einfachem Hinzufügen/Entfernen
- **Reviews & Ratings**: Filme bewerten und kommentieren
- **Achievement-System**: Erfolge für verschiedene Aktivitäten mit Fortschrittsverfolgung
- **Benutzerprofile**: Detaillierte Profile mit Statistiken und Einstellungen

### Erweiterte Features
- **Toast-Benachrichtigungen**: Modernes Feedback-System für Benutzeraktionen
- **Keyboard Shortcuts**: Schnelle Navigation (Ctrl+Shift+T für Theme-Toggle, Ctrl+K für Suche)
- **Animierte Effekte**: Cosmic Particles, Shooting Stars und smooth Transitions
- **Performance-Optimierung**: Lazy Loading, Caching und optimierte Datenbankabfragen

## 🚀 Installation & Setup

### Voraussetzungen
- Python 3.9+
- PostgreSQL 13+
- Node.js (für React-Frontend, optional)

### 1. Repository klonen
```bash
git clone https://github.com/HEADES94/MovieProjektFinal
cd MovieProjektFinal
```

### 2. Virtual Environment erstellen
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# oder
.venv\Scripts\activate     # Windows
```

### 3. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 4. PostgreSQL-Datenbank einrichten
```sql
CREATE DATABASE movie_app_postgres;
CREATE USER movieuser WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE movie_app_postgres TO movieuser;
```

### 5. Umgebungsvariablen konfigurieren
Erstelle eine `.env` Datei im Projektverzeichnis:
```env
# API Keys
OMDB_API_KEY=dein_omdb_api_key
GOOGLE_API_KEY=dein_google_gemini_api_key
TMDB_API_KEY=dein_tmdb_api_key

# Datenbank
DATABASE_URL=postgresql://movieuser:password@localhost/movie_app_postgres
DB_USER=movieuser
DB_PASSWORD=password

# Flask
SECRET_KEY=dein_geheimer_schlüssel
FLASK_ENV=development
DEBUG=True
```

### 6. Datenbank-Migrationen ausführen
```bash
python migrations/add_movie_id_to_quiz_attempts_postgresql.py
```

### 7. Anwendung starten
```bash
python app.py
```

Die App ist nun unter [http://127.0.0.1:5002](http://127.0.0.1:5002) verfügbar.

## 📊 Technologie-Stack

### Backend
- **Flask 3.1.0**: Web-Framework
- **SQLAlchemy 2.0.40**: ORM für Datenbankoperationen
- **PostgreSQL**: Hauptdatenbank
- **Flask-Login**: Benutzerauthentifizierung
- **Flask-WTF**: Formularverarbeitung und CSRF-Schutz
- **bcrypt**: Passwort-Hashing

### Frontend
- **HTML5/CSS3**: Responsive Design
- **JavaScript**: Interaktive Features
- **React** (optional): Moderne Frontend-Komponenten
- **Glassmorphism Design**: Modernes UI-Design

### APIs & Services
- **Google Gemini AI**: KI-basierte Empfehlungen
- **OMDB API**: Filmdaten
- **TMDB API**: Zusätzliche Filmmetadaten

## 🎮 Benutzung

### Quiz-System
1. Wähle einen Film aus der Filmliste
2. Klicke auf "Quiz starten"
3. Wähle den Schwierigkeitsgrad (Einfach, Mittel, Schwer)
4. Beantworte die Fragen und erhalte sofortiges Feedback
5. Verfolge deine Fortschritte in den film-spezifischen Statistiken

### Watchlist
1. Klicke auf "Zur Watchlist hinzufügen" bei einem Film
2. Verwalte deine Watchlist über das Hauptmenü
3. Entferne Filme mit einem Klick

### Achievements
- Automatische Freischaltung basierend auf Aktivitäten
- Verschiedene Kategorien: Quiz, Reviews, Watchlist
- Fortschrittsverfolgung im Benutzerprofil

## 🔧 Entwicklung

### Projektstruktur
```
MovieProjektFinal/
├── app.py                 # Hauptanwendung
├── data_models.py         # SQLAlchemy-Modelle
├── requirements.txt       # Python-Abhängigkeiten
├── services/             # Business-Logic-Services
├── migrations/           # Datenbank-Migrationen
├── templates/            # HTML-Templates
├── static/              # CSS, JS, Bilder
├── utils/               # Hilfsfunktionen
└── tests/               # Unit-Tests
```

### Neue Features hinzufügen
1. Erstelle Service-Klassen in `services/`
2. Definiere Datenmodelle in `data_models.py`
3. Implementiere Routes in `app.py`
4. Erstelle Templates in `templates/`
5. Füge Tests in `tests/` hinzu

### Datenbank-Migrationen
```bash
# Neue Migration erstellen
python migrations/create_migration.py

# Migration ausführen
python migrations/run_migration.py
```

## 🧪 Testing

```bash
# Alle Tests ausführen
pytest tests/

# Bestimmte Test-Datei
pytest tests/test_app.py

# Mit Coverage
pytest --cov=. tests/
```

## 🚢 Deployment

### Docker (Empfohlen)
```bash
# Docker-Image erstellen
docker build -t movieprojekt .

# Container starten
docker run -p 5002:5002 movieprojekt
```

### Manuell
```bash
# Produktionsserver (Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5002 app:app
```

## 🤝 Contributing

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne eine Pull Request

## 📝 API-Dokumentation

### REST-Endpoints
- `GET /api/movies` - Alle Filme mit Pagination
- `GET /api/movie/<id>` - Einzelner Film
- `GET /api/genres` - Verfügbare Genres
- `POST /quiz/<id>/submit` - Quiz-Antworten einreichen

## 🔐 Sicherheit

- **CSRF-Schutz**: Alle Formulare sind CSRF-geschützt
- **Passwort-Hashing**: bcrypt für sichere Passwort-Speicherung
- **Input-Validierung**: Alle Eingaben werden validiert
- **SQL-Injection-Schutz**: SQLAlchemy ORM verhindert SQL-Injection

## 🐛 Bekannte Probleme

- Quiz-Statistiken werden nach Migration korrekt angezeigt
- PostgreSQL-Verbindung erfordert korrekte Umgebungsvariablen
- React-Frontend ist optional und experimentell

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.

## 🙏 Danksagungen

- **Google Gemini AI** für KI-basierte Features
- **OMDB & TMDB** für Filmdaten
- **Flask-Community** für das großartige Framework

---

**Viel Spaß mit MovieProjekt! 🎬✨**

Für Fragen oder Support: [GitHub Issues](https://github.com/dein-username/MovieProjektFinal/issues)
