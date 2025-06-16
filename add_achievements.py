"""
Script zum Hinzufügen von Achievements in die Datenbank
"""
from datamanager.sqlite_data_manager import SQliteDataManager
from data_models import Achievement

# Liste der Achievements mit Emojis
achievements = [
    # Film-bezogene Achievements
    ("🎬 Filmkenner", "Bewerte deinen ersten Film", "movie_rating_1"),
    ("⭐ Filmkritiker", "Bewerte 10 verschiedene Filme", "movie_rating_10"),
    ("🌟 Filmorakel", "Bewerte 50 verschiedene Filme", "movie_rating_50"),
    ("🎯 Treffsicher", "Gib 5 Bewertungen ab, die dem Durchschnitt entsprechen", "accurate_ratings"),
    ("🎭 Genre-Meister", "Schaue Filme aus 5 verschiedenen Genres", "genre_diverse"),

    # Quiz-bezogene Achievements
    ("🎲 Quiz-Neuling", "Beende dein erstes Quiz", "quiz_complete_1"),
    ("🎮 Quiz-Enthusiast", "Beende 10 verschiedene Quizze", "quiz_complete_10"),
    ("🏆 Quiz-Champion", "Erreiche 100% in einem Quiz", "quiz_perfect"),
    ("🎯 Quizmaster", "Erreiche in 5 verschiedenen Quizzen mehr als 80%", "quiz_master"),
    ("⚡ Schnelldenker", "Beende ein Quiz in unter 2 Minuten", "quiz_speed"),

    # Community-Achievements
    ("📝 Rezensent", "Schreibe deine erste Filmrezension", "review_1"),
    ("✍️ Schriftsteller", "Schreibe 10 ausführliche Rezensionen", "review_10"),
    ("🌟 Kritiker-Guru", "Erhalte 50 'Hilfreich'-Bewertungen für deine Rezensionen", "helpful_reviews"),
    ("💭 Fragensteller", "Schlage eine Quiz-Frage vor", "suggest_question"),
    ("🎓 Quiz-Autor", "5 deiner vorgeschlagenen Fragen wurden akzeptiert", "questions_accepted"),

    # Watchlist-Achievements
    ("📋 Planer", "Füge den ersten Film zu deiner Watchlist hinzu", "watchlist_1"),
    ("📚 Sammler", "Habe 20 Filme in deiner Watchlist", "watchlist_20"),
    ("✅ Fleißig", "Schaue 5 Filme von deiner Watchlist", "watchlist_complete_5"),
    ("🎯 Zielstrebig", "Schaue 20 Filme von deiner Watchlist", "watchlist_complete_20"),
    ("⚡ Schnell", "Schaue einen Film innerhalb einer Woche nach dem Hinzufügen zur Watchlist", "watchlist_quick"),

    # Spezial-Achievements
    ("🎬 Filmmarathon", "Schaue 3 Filme am selben Tag", "movie_marathon"),
    ("🌙 Nachteule", "Schaue einen Film zwischen 0:00 und 5:00 Uhr", "night_owl"),
    ("🎅 Feiertagsfilmer", "Schaue einen Weihnachtsfilm im Dezember", "holiday_spirit"),
    ("🌈 Weltenbummler", "Schaue Filme aus 5 verschiedenen Ländern", "international"),
    ("⏳ Zeitreisender", "Schaue Filme aus 5 verschiedenen Jahrzehnten", "time_traveler"),

    # Genre-spezifische Achievements
    ("🦸‍♂️ Superhelden-Fan", "Schaue 5 Superhelden-Filme", "superhero"),
    ("👻 Horror-Meister", "Schaue 5 Horrorfilme", "horror_master"),
    ("❤️ Romantiker", "Schaue 5 Romantische Filme", "romance_lover"),
    ("🔍 Detective", "Schaue 5 Krimi-Filme", "mystery_solver"),
    ("🚀 Weltraum-Erkunder", "Schaue 5 Science-Fiction-Filme", "space_explorer"),

    # Streak-Achievements
    ("🔥 Auf Kurs", "Logge dich 3 Tage in Folge ein", "login_streak_3"),
    ("⚡ Durchstarter", "Logge dich 7 Tage in Folge ein", "login_streak_7"),
    ("💫 Sternenjäger", "Logge dich 30 Tage in Folge ein", "login_streak_30"),
    ("🎯 Bewerter-Streak", "Bewerte 5 Tage in Folge einen Film", "rating_streak_5"),
    ("🏆 Quiz-Streak", "Löse 7 Tage in Folge ein Quiz", "quiz_streak_7"),

    # Social Achievements
    ("👋 Willkommen", "Vervollständige dein Profil", "profile_complete"),
    ("💬 Gesprächig", "Kommentiere 5 verschiedene Filmrezensionen", "commenter"),
    ("❤️ Hilfreich", "Erhalte 10 'Hilfreich'-Bewertungen", "helpful_user"),
    ("🤝 Teamplayer", "Hilf 5 anderen Nutzern mit Filmempfehlungen", "helpful_recommender"),
    ("🌟 Community-Star", "Erreiche 100 'Hilfreich'-Bewertungen", "community_star"),

    # Entdecker-Achievements
    ("🎬 Indie-Fan", "Schaue 5 Independent-Filme", "indie_lover"),
    ("🌍 Weltenbummler", "Schaue Filme in 3 verschiedenen Sprachen", "polyglot"),
    ("⏳ Klassiker-Fan", "Schaue 5 Filme, die vor 1960 erschienen sind", "classic_lover"),
    ("🎯 Trendsetter", "Schaue einen Film in seiner Premierenwoche", "early_bird"),
    ("🔍 Entdecker", "Finde und bewerte 5 Filme mit weniger als 100 Bewertungen", "discoverer"),

    # Experten-Achievements
    ("📽️ Filmhistoriker", "Schaue Filme aus jedem Jahrzehnt seit 1950", "film_historian"),
    ("🎭 Genre-Experte", "Schaue mindestens einen Film aus jedem verfügbaren Genre", "genre_expert"),
    ("🌟 Kritiker-Legende", "Schreibe 100 qualitativ hochwertige Rezensionen", "review_legend"),
    ("🏆 Quiz-Legende", "Erreiche 100% in 10 verschiedenen Quizzen", "quiz_legend"),
    ("👑 Film-Guru", "Schalte 40 andere Achievements frei", "achievement_master"),

    # Event-Achievements
    ("🎃 Halloween-Fan", "Schaue einen Horrorfilm an Halloween", "halloween_spirit"),
    ("💘 Romantiker", "Schaue einen Liebesfilm am Valentinstag", "valentine"),
    ("🎅 Weihnachtsfreund", "Schaue alle 'Stirb Langsam' Filme im Dezember", "die_hard_fan"),
    ("🎭 Oscar-Kenner", "Schaue alle Oscar-Nominierten eines Jahres", "oscar_enthusiast"),
    ("🌟 Festival-Fan", "Schaue 3 Filme, die auf dem aktuellen Filmfestival laufen", "festival_visitor")
]

def add_achievements():
    """Fügt die vordefinierten Achievements zur Datenbank hinzu"""
    data_manager = SQliteDataManager("sqlite:///movie_app.db")

    with data_manager.SessionFactory() as session:
        # Lösche bestehende Achievements
        session.query(Achievement).delete()

        # Füge neue Achievements hinzu
        for title, description, code in achievements:
            achievement = Achievement(
                title=title,
                description=description,
                code=code
            )
            session.add(achievement)

        session.commit()
        print(f"{len(achievements)} Achievements wurden erfolgreich hinzugefügt!")

if __name__ == "__main__":
    add_achievements()
