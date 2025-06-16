"""
Migration: Fügt das Schwierigkeitsgrad-Feld zu Quiz-Versuchen hinzu
"""
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Füge die neue Spalte hinzu
    op.add_column('quiz_attempts', sa.Column('difficulty', sa.String(), nullable=True, server_default='mittel'))

def downgrade():
    # Entferne die Spalte im Falle eines Rollbacks
    op.drop_column('quiz_attempts', 'difficulty')
