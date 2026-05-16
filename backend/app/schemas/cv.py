"""
Schémas Pydantic pour les CVs.
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class CVUploadResponse(BaseModel):
    id: UUID
    filename: str
    file_size_kb: Optional[int]
    page_count: Optional[int]
    message: str = "CV uploadé avec succès"


class CVBase(BaseModel):
    filename: str
    file_size_kb: Optional[int] = None
    page_count: Optional[int] = None


class CVInDB(CVBase):
    id: UUID
    user_id: UUID
    extracted_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CVResponse(CVInDB):
    pass


class CVListResponse(BaseModel):
    items: list[CVResponse]
    total: int