"""
Modèles SQLAlchemy : Sessions d'entretien et Questions/Réponses
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cv_id = Column(UUID(as_uuid=True), ForeignKey("cvs.id"), nullable=True)
    job_title = Column(String(200))
    difficulty = Column(String(20), default="medium")
    total_score = Column(Integer)
    status = Column(String(20), default="in_progress")
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    
    # Relations
    user = relationship("User", back_populates="interview_sessions")
    questions = relationship("InterviewQA", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<InterviewSession(id={self.id}, status={self.status})>"


class InterviewQA(Base):
    __tablename__ = "interview_qa"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_number = Column(Integer, nullable=False)
    
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))  # technical, behavioral, situational
    expected_keywords = Column(JSON, default=list)
    
    user_answer = Column(Text)
    answer_score = Column(Integer)
    feedback_text = Column(Text)
    detected_keywords = Column(JSON, default=list)
    missing_keywords = Column(JSON, default=list)
    
    answered_at = Column(DateTime(timezone=True))
    
    # Relations
    session = relationship("InterviewSession", back_populates="questions")
    
    def __repr__(self):
        return f"<InterviewQA(session={self.session_id}, q={self.question_number})>"