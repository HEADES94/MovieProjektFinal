"""
Stellt die Daten aus dem Backup wieder her
"""
import sqlite3

def restore_data():
    # Verbindung zu beiden Datenbanken
    backup = sqlite3.connect('movie_app.db.backup')
    current = sqlite3.connect('movie_app.db')

    backup_cur = backup.cursor()
    current_cur = current.cursor()

    try:
        # Liste der Tabellen aus dem Backup holen
        backup_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = backup_cur.fetchall()

        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':  # Systemtabelle überspringen
                try:
                    # Daten aus dem Backup lesen
                    backup_cur.execute(f"SELECT * FROM {table_name}")
                    rows = backup_cur.fetchall()

                    if rows:
                        # Spaltennamen aus dem Backup holen
                        backup_cur.execute(f"PRAGMA table_info({table_name})")
                        columns = backup_cur.fetchall()
                        column_names = [col[1] for col in columns]

                        # Für quiz_attempts Tabelle das neue Feld hinzufügen
                        if table_name == 'quiz_attempts':
                            column_names.append('max_possible_score')
                            # Einfügen mit Standardwert 10 für max_possible_score
                            for row in rows:
                                placeholders = ','.join(['?' for _ in range(len(column_names))])
                                values = list(row) + [10]  # 10 als Standardwert
                                current_cur.execute(f"INSERT INTO {table_name} ({','.join(column_names)}) VALUES ({placeholders})", values)
                        else:
                            # Normale Tabellen wiederherstellen
                            for row in rows:
                                placeholders = ','.join(['?' for _ in range(len(row))])
                                current_cur.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", row)

                        print(f"Daten für Tabelle {table_name} wiederhergestellt")
                except Exception as e:
                    print(f"Fehler beim Wiederherstellen von {table_name}: {str(e)}")
                    continue

        current.commit()
        print("Datenwiederherstellung abgeschlossen!")

    except Exception as e:
        print(f"Fehler bei der Wiederherstellung: {str(e)}")
        current.rollback()
    finally:
        backup.close()
        current.close()

if __name__ == "__main__":
    restore_data()
