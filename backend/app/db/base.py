"""
Base SQLAlchemy déclarative pour tous les modèles ORM.
"""

from sqlalchemy.orm import declarative_base

# Base commune à tous les modèles
Base = declarative_base()