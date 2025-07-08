# Dockerfile für MovieProjekt
FROM python:3.11-slim

WORKDIR /app

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY . .

# Erstelle nicht-root Benutzer
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Umgebungsvariablen
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

# Health Check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
