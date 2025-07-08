"""
Database Migration System
Automatisierte Datenbank-Migrationen und Backups
"""
import os
import shutil
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
import logging

class DatabaseMigration:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.backup_dir = "backups"
        self.migrations_dir = "migrations"

        # Erstelle Backup-Ordner
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self) -> str:
        """Erstellt ein Backup der Datenbank"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"movieapp_backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        try:
            shutil.copy2(self.db_path, backup_path)
            logging.info(f"Backup erstellt: {backup_path}")
            return backup_path
        except Exception as e:
            logging.error(f"Backup fehlgeschlagen: {str(e)}")
            raise

    def restore_backup(self, backup_path: str) -> bool:
        """Stellt eine Backup-Datei wieder her"""
        try:
            # Erstelle Backup der aktuellen DB
            current_backup = self.create_backup()
            logging.info(f"Aktueller Stand gesichert: {current_backup}")

            # Stelle Backup wieder her
            shutil.copy2(backup_path, self.db_path)
            logging.info(f"Backup wiederhergestellt: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Wiederherstellung fehlgeschlagen: {str(e)}")
            return False

    def execute_migration(self, migration_sql: str, migration_name: str) -> bool:
        """Führt eine Migration aus"""
        # Erstelle Backup vor Migration
        backup_path = self.create_backup()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Führe Migration aus
            cursor.executescript(migration_sql)
            conn.commit()

            logging.info(f"Migration '{migration_name}' erfolgreich ausgeführt")
            return True

        except Exception as e:
            logging.error(f"Migration '{migration_name}' fehlgeschlagen: {str(e)}")
            # Stelle Backup wieder her
            self.restore_backup(backup_path)
            return False
        finally:
            conn.close()

    def cleanup_old_backups(self, keep_count: int = 10):
        """Bereinigt alte Backups"""
        backup_files = [f for f in os.listdir(self.backup_dir) if f.endswith('.db')]
        backup_files.sort(reverse=True)  # Neueste zuerst

        for old_backup in backup_files[keep_count:]:
            old_path = os.path.join(self.backup_dir, old_backup)
            os.remove(old_path)
            logging.info(f"Altes Backup entfernt: {old_backup}")

# Spezifische Migrationen für MovieProjekt
class MovieDatabaseMigrations:
    @staticmethod
    def add_user_preferences():
        """Migration: Benutzereinstellungen hinzufügen"""
        return """
        ALTER TABLE users ADD COLUMN theme VARCHAR(20) DEFAULT 'system';
        ALTER TABLE users ADD COLUMN language VARCHAR(5) DEFAULT 'de';
        ALTER TABLE users ADD COLUMN email_notifications BOOLEAN DEFAULT 1;
        """

    @staticmethod
    def add_movie_tags():
        """Migration: Film-Tags System"""
        return """
        CREATE TABLE IF NOT EXISTS movie_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL UNIQUE,
            color VARCHAR(7) DEFAULT '#6366f1',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS movie_tag_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES movie_tags (id) ON DELETE CASCADE,
            UNIQUE(movie_id, tag_id)
        );
        """

    @staticmethod
    def add_user_activity_log():
        """Migration: Benutzeraktivitäten protokollieren"""
        return """
        CREATE TABLE IF NOT EXISTS user_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action VARCHAR(50) NOT NULL,
            details TEXT,
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        
        CREATE INDEX idx_activity_user_date ON user_activity_log(user_id, created_at);
        """

# CLI für Migrationen
def run_migration_cli():
    """Command Line Interface für Migrationen"""
    import argparse

    parser = argparse.ArgumentParser(description='MovieApp Database Migrations')
    parser.add_argument('command', choices=['backup', 'migrate', 'restore', 'cleanup'])
    parser.add_argument('--file', help='Backup-Datei für restore')
    parser.add_argument('--migration', help='Migration name')

    args = parser.parse_args()

    migrator = DatabaseMigration('movie_app.db')
    migrations = MovieDatabaseMigrations()

    if args.command == 'backup':
        backup_path = migrator.create_backup()
        print(f"Backup erstellt: {backup_path}")

    elif args.command == 'migrate':
        if not args.migration:
            print("Verfügbare Migrationen:")
            print("- user_preferences")
            print("- movie_tags")
            print("- user_activity_log")
            return

        migration_method = getattr(migrations, f"add_{args.migration}", None)
        if migration_method:
            sql = migration_method()
            success = migrator.execute_migration(sql, args.migration)
            print(f"Migration {args.migration}: {'Erfolgreich' if success else 'Fehlgeschlagen'}")
        else:
            print(f"Migration '{args.migration}' nicht gefunden")

    elif args.command == 'restore':
        if not args.file:
            print("Bitte geben Sie eine Backup-Datei an: --file backup.db")
            return
        success = migrator.restore_backup(args.file)
        print(f"Wiederherstellung: {'Erfolgreich' if success else 'Fehlgeschlagen'}")

    elif args.command == 'cleanup':
        migrator.cleanup_old_backups()
        print("Alte Backups bereinigt")

if __name__ == "__main__":
    run_migration_cli()
