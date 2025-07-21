# MovieProjekt - KI-gestützte Film-Management-App

Ein modernes, vollständig ausgestattetes Web-Tool zum Verwalten, Bewerten und Quizzen rund um Filme – gebaut mit Flask, SQLAlchemy, PostgreSQL und Google Gemini AI.

## 🎬 Features

### Core Features
- **Benutzerverwaltung**: Sichere Registrierung, Login und Profilverwaltung mit bcrypt-Passwort-Hashing
- **Filmverwaltung**: Filme hinzufügen, bewerten, kommentieren und verwalten
- **Erweiterte Suchfunktion**: Filme nach Titel, Genre, Regisseur und Jahr filtern
- **Responsive Design**: Modernes Glassmorphism-Design mit vollständig funktionsfähigem Dark/Light Mode
- **Theme-System**: Dark/Light/System-Theme mit automatischer Speicherung und Backend-Synchronisation

### Quiz-System
- **Film-spezifische Quiz**: Individuelle Quiz für jeden Film mit drei Schwierigkeitsgraden
- **Schwierigkeitsgrade**: 
  - **Easy** (5 Fragen, 100-300 Punkte)
  - **Medium** (7 Fragen, 150-450 Punkte) 
  - **Hard** (10 Fragen, 200-600 Punkte)
- **KI-generierte Fragen**: Automatische Fragenerstellung durch Google Gemini AI
- **Detaillierte Statistiken**: Film-spezifische Quiz-Performance und globale Highscores
- **Anti-Repeat System**: Intelligente Vermeidung kürzlich gestellter Fragen

### Achievement-System
- **25+ Verschiedene Erfolge**: Quiz-Leistungen, Streaks, Social-Aktivitäten
- **Gamification-Elemente**: 
  - Perfect Quiz, Quiz Master, Perfectionist
  - 5er/10er/20er Streaks
  - Watchlist-Fan, Movie Critic, Knowledge Seeker
- **Fortschrittsverfolgung**: Detaillierte Erfolgsstatistiken mit Unlock-System

### KI-Integration
- **Google Gemini AI**: Intelligente Filmempfehlungen und Quiz-Generierung
- **TMDB/OMDB APIs**: Umfangreiche Filmdaten-Integration
- **Personalisierte Empfehlungen**: Basierend auf Bewertungshistorie und Präferenzen
- **Automatische Metadaten**: Poster, Plots, Cast-Informationen

### Social Features
- **Watchlist**: Persönliche Film-Merkliste mit einfacher Verwaltung
- **Reviews & Ratings**: Umfassendes Bewertungs- und Kommentarsystem
- **Benutzerprofile**: Detaillierte Profile mit Statistiken und personalisierten Einstellungen
- **Achievement-Sharing**: Erfolge und Fortschritte verfolgen

### Frontend-Technologien
- **React 18**: Moderne Frontend-Komponenten mit Hooks
- **Vite**: Blitzschnelle Entwicklungsumgebung
- **Framer Motion**: Elegante Animationen und Transitions
- **Emotion**: CSS-in-JS für dynamisches Styling
- **Responsive Design**: Optimiert für alle Bildschirmgrößen

### Erweiterte Features
- **Toast-Benachrichtigungen**: Elegantes Feedback-System
- **Keyboard Shortcuts**: 
  - `Ctrl+Shift+T`: Theme-Wechsel
  - `Ctrl+K`: Suchfunktion
- **Animierte Effekte**: Cosmic Particles, Shooting Stars, Glassmorphism
- **Performance-Optimierung**: Caching, Lazy Loading, optimierte Datenbankabfragen
- **Logging-System**: Strukturierte Fehlerprotokollierung und Monitoring

## 🚀 Installation & Setup

### Voraussetzungen
- **Python 3.11+**
- **PostgreSQL 13+**
- **Node.js 18+** (für React-Frontend)
- **Git**

### 1. Repository klonen
```bash
git clone https://github.com/HEADES94/MovieProjektFinal
cd MovieProjektFinal
```

### 2. Backend Setup (Python/Flask)
```bash
# Virtual Environment erstellen
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# oder
.venv\Scripts\activate     # Windows

# Python-Abhängigkeiten installieren
pip install -r requirements.txt
```

### 3. Frontend Setup (React/Node.js)
```bash
# Node.js-Abhängigkeiten installieren
npm install
```

### 4. PostgreSQL-Datenbank einrichten
```sql
CREATE DATABASE movie_app_postgres;
CREATE USER movieuser WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE movie_app_postgres TO movieuser;
```

### 5. Umgebungsvariablen konfigurieren
Erstelle eine `.env` Datei im Projektverzeichnis:
```env
# API Keys
OMDB_API_KEY=your_omdb_api_key
GOOGLE_API_KEY=your_google_gemini_api_key
TMDB_API_KEY=your_tmdb_api_key

# Datenbank
DATABASE_URL=postgresql://movieuser:your_secure_password@localhost/movie_app_postgres

# Flask
SECRET_KEY=your_super_secret_key_here
FLASK_ENV=development
DEBUG=True
```

### 6. Datenbank initialisieren
```bash
# Datenbank-Migrationen ausführen
python scripts/database_migrations.py

# Optional: Beispieldaten laden
python scripts/extend_to_2000_movies.py
```

### 7. Anwendung starten

**Option 1: Entwicklungsumgebung (empfohlen)**
```bash
# Backend und Frontend gleichzeitig starten
npm run start:dev
```

**Option 2: Separate Terminals**
```bash
# Terminal 1: Backend
python app.py

# Terminal 2: Frontend
npm run dev
```

Die App ist nun verfügbar:
- **Backend**: [http://localhost:5000](http://localhost:5000)
- **Frontend**: [http://localhost:5173](http://localhost:5173)

## 📊 Technologie-Stack

### Backend
- **Python 3.11+**
- **Flask 3.1.0** - Web-Framework
- **SQLAlchemy 2.0.40** - ORM
- **PostgreSQL** - Primäre Datenbank
- **Flask-Login** - Authentifizierung
- **bcrypt** - Passwort-Verschlüsselung
- **Google Gemini AI** - KI-Integration

### Frontend
- **React 18.2.0** - UI-Framework
- **Vite 5.0+** - Build-Tool
- **Framer Motion** - Animationen
- **Emotion** - CSS-in-JS
- **Axios** - HTTP-Client
- **Lucide React** - Icon-Library

### DevOps & Tools
- **Docker** - Containerisierung (optional)
- **Gunicorn** - Production WSGI-Server
- **pytest** - Testing-Framework
- **ESLint/Prettier** - Code-Qualität

## 🏗️ Projektstruktur

```
MovieProjektFinal/
├── 📁 services/           # Backend-Services
│   ├── achievement_service.py
│   ├── auth_service.py
│   ├── quiz_service.py
│   └── watchlist_service.py
├── 📁 frontend/           # React-Frontend
│   ├── components/
│   ├── hooks/
│   └── styles/
├── 📁 templates/          # Jinja2-Templates
├── 📁 static/            # Statische Assets
├── 📁 migrations/        # Datenbank-Migrationen
├── 📁 scripts/           # Utility-Scripts
├── 📁 tests/            # Test-Suite
├── 📁 utils/            # Helper-Funktionen
├── 📄 app.py            # Haupt-Flask-App
├── 📄 data_models.py    # SQLAlchemy-Modelle
├── 📄 ai_request.py     # Gemini AI-Client
└── 📄 requirements.txt  # Python-Dependencies
```

## 🔧 Entwicklung

### Verfügbare Scripts
```bash
# Entwicklung
npm run dev              # Frontend-Entwicklungsserver
npm run start:backend    # Backend-Server
npm run start:dev        # Beide Server gleichzeitig

# Production
npm run build           # Frontend für Production bauen
npm run preview         # Production-Preview

# Testing
pytest                  # Python-Tests ausführen
npm test               # Frontend-Tests (falls konfiguriert)
```

### Code-Qualität
- **Services-Pattern**: Saubere Trennung der Business-Logik
- **Error Handling**: Umfassende Fehlerbehandlung
- **Logging**: Strukturierte Protokollierung
- **Security**: CSRF-Schutz, sichere Sessions, Input-Validation

## 🐳 Docker Deployment (Optional)

```bash
# Docker-Image bauen
docker build -t movieprojekt .

# Container starten
docker run -p 5000:5000 movieprojekt
```

Das Docker-Setup enthält:
- **Gunicorn WSGI-Server** mit 4 Workern
- **Health Checks** für Container-Monitoring
- **Non-root User** für Sicherheit
- **Production-optimierte Konfiguration**

## 🎯 Key Features im Detail

### Quiz-System
- **Adaptive Schwierigkeit**: Drei Levels mit unterschiedlichen Punktesystemen
- **KI-generierte Fragen**: Keine statischen Fragen, immer frischer Content
- **Performance-Tracking**: Detaillierte Statistiken pro Film und global
- **Achievement-Integration**: Erfolge für verschiedene Quiz-Leistungen

### Theme-System
- **Drei Modi**: Dark, Light, System (folgt OS-Einstellungen)
- **Persistierung**: Speicherung in Backend + localStorage
- **Live-Switching**: Sofortiger Themenwechsel ohne Reload
- **Responsive Effekte**: Angepasste Animationen für jeden Modus

### Performance
- **Caching-Layer**: Intelligente Zwischenspeicherung
- **Lazy Loading**: Optimierte Ladezeiten
- **Database Indexing**: Performance-optimierte Datenbankabfragen
- **Frontend-Optimierung**: Vite-basierte Build-Pipeline

## 📈 Statistiken

- **~15 Python-Module**: Strukturierte Backend-Architektur  
- **10+ React-Komponenten**: Moderne Frontend-Architektur
- **25+ Achievement-Typen**: Umfassendes Gamification-System
- **3 Quiz-Schwierigkeitsgrade**: Flexible Herausforderungen
- **Multi-API Integration**: TMDB, OMDB, Google Gemini

## 🚀 Zukünftige Erweiterungen

- **Mobile App**: React Native Integration
- **Real-time Features**: WebSocket-basierte Live-Updates  
- **Advanced Analytics**: Erweiterte Benutzer-Insights
- **Social Features**: Freunde-System und Vergleiche
- **API-Entwicklung**: RESTful API für Third-Party Integration

## 🤝 Contributing

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/amazing-feature`)
3. Committe deine Änderungen (`git commit -m 'Add amazing feature'`)
4. Push zum Branch (`git push origin feature/amazing-feature`)  
5. Öffne eine Pull Request

## 📝 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## 🎬 Demo

Eine vollständige Funktionsübersicht und Live-Demo finden Sie in der [PROJEKT_ZUSAMMENFASSUNG.md](PROJEKT_ZUSAMMENFASSUNG.md).

---

**MovieProjekt** - Wo KI auf Kino trifft! 🌟🎬
