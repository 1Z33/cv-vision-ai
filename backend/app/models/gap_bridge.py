"""Modèle Gap Bridge — Plan d'action compétences."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base


class GapBridgePlan(Base):
    __tablename__ = "gap_bridge_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    cv_id = Column(String(36), ForeignKey("cvs.id"), nullable=False, index=True)
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=False)

    # Plan généré
    missing_skills = Column(JSON, default=list)  # skills identifiés
    total_resources = Column(Integer, default=0)
    total_duration_hours = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    items = relationship(
        "GapBridgeItem",
        back_populates="plan",
        cascade="all, delete-orphan",
    )


class GapBridgeItem(Base):
    __tablename__ = "gap_bridge_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), ForeignKey("gap_bridge_plans.id"), nullable=False, index=True)

    # Skill cible
    skill_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # programming, web, data, soft_skills

    # Ressource
    resource_title = Column(String(200), nullable=False)
    resource_url = Column(String(500), nullable=False)
    resource_type = Column(String(50))  # documentation, course, book, interactive
    duration_hours = Column(Integer, default=0)
    is_free = Column(Boolean, default=True)

    # Progression
    status = Column(String(20), default="not_started")  # not_started, in_progress, completed
    progress_percent = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relations
    plan = relationship("GapBridgePlan", back_populates="items")

