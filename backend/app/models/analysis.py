"""
Modèle SQLAlchemy : Résultat d'analyse IA d'un CV
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, ForeignKey, Integer, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cv_id = Column(UUID(as_uuid=True), ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Scores
    overall_score = Column(Integer)
    structure_score = Column(Integer)
    content_score = Column(Integer)
    keywords_score = Column(Integer)
    
    # Données IA
    detected_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    strengths = Column(JSON, default=list)
    weaknesses = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    
    # Métadonnées
    sections_detected = Column(JSON, default=dict)
    word_count = Column(Integer)
    contact_info_found = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relations
    cv = relationship("CV", back_populates="analysis")
    
    def __repr__(self):
        return f"<Analysis(cv_id={self.cv_id}, score={self.overall_score})>"