#!/usr/bin/env python3
"""
Achievement Cleanup Script
Removes duplicate achievements and fixes language inconsistencies.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datamanager.sqlite_data_manager import SQliteDataManager
from data_models import Achievement, UserAchievement
from dotenv import load_dotenv

load_dotenv()


def cleanup_achievements():
    """Clean up duplicate achievements and fix descriptions."""
    db_url = os.getenv('DATABASE_URL', 'postgresql://localhost/movie_app_postgres')
    data_manager = SQliteDataManager(db_url)

    with data_manager.SessionFactory() as session:
        print("🧹 Starting Achievement Cleanup...")

        # 1. Find and remove duplicates
        print("\n1. Removing duplicate achievements...")

        # Get all achievements
        all_achievements = session.query(Achievement).all()

        # Group by description to find duplicates
        description_groups = {}
        for achievement in all_achievements:
            desc = achievement.description
            if desc not in description_groups:
                description_groups[desc] = []
            description_groups[desc].append(achievement)

        # Remove duplicates (keep the one with English name/description)
        duplicates_removed = 0
        for desc, achievements in description_groups.items():
            if len(achievements) > 1:
                print(f"Found duplicates for: {desc}")

                # Sort by preference: English names first, then by code
                sorted_achievements = sorted(achievements, key=lambda x: (
                    1 if any(german in x.name.lower() for german in ['sammler', 'neuling', 'fan']) else 0,
                    x.code or 'zzz'
                ))

                # Keep the first (best) one, remove others
                keep = sorted_achievements[0]
                remove_list = sorted_achievements[1:]

                print(f"  Keeping: {keep.name} ({keep.code})")

                for dup in remove_list:
                    print(f"  Removing: {dup.name} ({dup.code})")

                    # Move user achievements to the kept achievement
                    user_achievements = session.query(UserAchievement).filter_by(
                        achievement_id=dup.id
                    ).all()

                    for ua in user_achievements:
                        # Check if user already has the kept achievement
                        existing = session.query(UserAchievement).filter_by(
                            user_id=ua.user_id,
                            achievement_id=keep.id
                        ).first()

                        if not existing:
                            ua.achievement_id = keep.id
                        else:
                            session.delete(ua)

                    session.delete(dup)
                    duplicates_removed += 1

        # 2. Update achievement names and descriptions to English
        print(f"\n2. Updating achievement descriptions to English...")

        english_updates = {
            'Quiz-Neuling': ('🎉 Quiz Beginner', 'Complete your first quiz!'),
            'Perfect Quiz': ('🎯 Perfect Quiz', 'Achieve perfect score in a quiz!'),
            'Quiz Profi': ('🎓 Quiz Expert', 'Complete a hard quiz with at least 8 correct answers!'),
            'First Highscore': ('🏆 First Highscore', 'Achieve your first highscore!'),
            'Quiz Master': ('👑 Quiz Master', 'Achieve at least 400 points in 5 different quizzes!'),
            'Wissensdurst': ('📚 Knowledge Seeker', 'Answer 100 questions correctly!'),
            'Film Enthusiast': ('🎬 Movie Enthusiast', 'Complete 10 different movie quizzes!'),
            'Perfektionist': ('🌟 Perfectionist', 'Achieve 3 perfect quizzes in a row!'),
            'Streak Master': ('🔥 Streak Master', 'Answer 20 questions in a row correctly!'),
            '5er Streak': ('🔥 5 Streak', 'Answer 5 questions in a row correctly!'),
            '10er Streak': ('🔥 10 Streak', 'Answer 10 questions in a row correctly!'),
            'Quiz-Veteran': ('💯 Quiz Veteran', 'Complete 100 quizzes!'),
            'Erster Sammler': ('📺 First Collector', 'Add your first movie to watchlist!'),
            'Sammler': ('📺 Collector', 'Add 10 movies to watchlist!'),
            'Mega-Sammler': ('📺 Mega Collector', 'Add 50 movies to watchlist!'),
            'Watchlist-Fan': ('📺 Collector', 'Add 10 movies to watchlist!'),  # Duplicate
            'Erster Kritiker': ('📝 First Critic', 'Write your first review!'),
            'Kritiker': ('📝 Critic', 'Write 10 reviews!'),
        }

        updated_count = 0
        try:
            # Use no_autoflush to prevent premature commits
            with session.no_autoflush:
                for achievement in session.query(Achievement).all():
                    old_name = achievement.name.replace('🎉 ', '').replace('🎯 ', '').replace('🎓 ', '').replace('🏆 ', '').replace('👑 ', '').replace('📚 ', '').replace('🎬 ', '').replace('🌟 ', '').replace('🔥 ', '').replace('💯 ', '').replace('📺 ', '').replace('📝 ', '')

                    if old_name in english_updates:
                        new_name, new_desc = english_updates[old_name]

                        # Check if the new name already exists in another achievement
                        existing_with_name = session.query(Achievement).filter(
                            Achievement.name == new_name,
                            Achievement.id != achievement.id
                        ).first()

                        if not existing_with_name:
                            print(f"  Updating: {achievement.name} -> {new_name}")
                            achievement.name = new_name
                            achievement.description = new_desc
                            updated_count += 1
                        else:
                            print(f"  Skipping {achievement.name} -> {new_name} (name already exists)")

                # Manual flush to catch any remaining conflicts
                session.flush()
        except Exception as e:
            print(f"  Error during updates: {e}")
            session.rollback()

        # 3. Ensure all achievements have proper codes
        print(f"\n3. Adding missing achievement codes...")

        code_mapping = {
            '🎉 Quiz Beginner': 'quiz_beginner',
            '🎯 Perfect Quiz': 'perfect_quiz',
            '🎓 Quiz Expert': 'quiz_expert',
            '🏆 First Highscore': 'first_highscore',
            '👑 Quiz Master': 'quiz_master',
            '📚 Knowledge Seeker': 'knowledge_seeker',
            '🎬 Movie Enthusiast': 'movie_enthusiast',
            '🌟 Perfectionist': 'perfectionist',
            '🔥 Streak Master': 'streak_master',
            '🔥 5 Streak': 'streak_5',
            '🔥 10 Streak': 'streak_10',
            '💯 Quiz Veteran': 'quiz_100',
            '📺 First Collector': 'first_watchlist',
            '📺 Collector': 'collector_10',
            '📺 Mega Collector': 'collector_50',
            '📝 First Critic': 'first_review',
            '📝 Critic': 'critic_10',
        }

        codes_added = 0
        for achievement in session.query(Achievement).all():
            if not achievement.code and achievement.name in code_mapping:
                achievement.code = code_mapping[achievement.name]
                print(f"  Added code '{achievement.code}' to {achievement.name}")
                codes_added += 1

        # Commit all changes
        session.commit()

        print(f"\n✅ Cleanup completed!")
        print(f"   - Removed {duplicates_removed} duplicate achievements")
        print(f"   - Updated {updated_count} achievement descriptions to English")
        print(f"   - Added {codes_added} missing achievement codes")

        # Show final achievement count
        final_count = session.query(Achievement).count()
        print(f"   - Total achievements in database: {final_count}")


if __name__ == "__main__":
    cleanup_achievements()
