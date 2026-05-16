"""
Import centralisé de tous les modèles pour Alembic.
"""

from app.db.base import Base
from app.models.user import User
from app.models.cv import CV
from app.models.analysis import Analysis
from app.models.interview import InterviewSession, InterviewQA
from app.models.job import Job
from app.models.match import Match

# Pour que Alembic détecte tous les modèles
__all__ = ["Base", "User", "CV", "Analysis", "InterviewSession", "InterviewQA", "Job", "Match"]