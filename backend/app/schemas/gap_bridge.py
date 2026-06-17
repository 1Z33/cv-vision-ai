"""Schémas Pydantic Gap Bridge."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class GapBridgeResource(BaseModel):
    title: str
    url: str
    type: str
    duration_hours: int
    is_free: bool


class GapBridgeItemResponse(BaseModel):
    id: str
    skill_name: str
    category: str
    resource_title: str
    resource_url: str
    resource_type: str
    duration_hours: int
    is_free: bool
    status: str
    progress_percent: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class GapBridgePlanResponse(BaseModel):
    id: str
    cv_id: str
    analysis_id: str
    missing_skills: List[str]
    total_resources: int
    total_duration_hours: int
    items: List[GapBridgeItemResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GapBridgeCreateRequest(BaseModel):
    cv_id: str


class GapBridgeUpdateProgressRequest(BaseModel):
    item_id: str
    status: str  # not_started, in_progress, completed
    progress_percent: Optional[int] = None


class GapBridgeSummaryResponse(BaseModel):
    plan_id: str
    total_items: int
    completed_items: int
    in_progress_items: int
    overall_progress_percent: int
    total_duration_hours: int
    estimated_completion: Optional[str]

