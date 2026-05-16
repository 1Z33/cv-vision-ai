"""
Modèle SQLAlchemy : Résultat de matching CV/Job
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, ForeignKey, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Match(Base):
    __tablename__ = "matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cv_id = Column(UUID(as_uuid=True), ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    compatibility_score = Column(Integer)
    matching_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    skill_gap_analysis = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<Match(cv={self.cv_id}, job={self.job_id}, score={self.compatibility_score})>"