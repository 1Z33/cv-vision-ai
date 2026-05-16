"""
Modèle SQLAlchemy : CV uploadé
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class CV(Base):
    __tablename__ = "cvs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    extracted_text = Column(Text)
    file_size_kb = Column(Integer)
    page_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relations
    user = relationship("User", back_populates="cvs")
    analysis = relationship("Analysis", back_populates="cv", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CV(id={self.id}, filename={self.filename})>"