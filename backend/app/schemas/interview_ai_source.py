from pydantic import BaseModel
from typing import Optional, Literal


GeminiSource = Literal["gemini", "fallback"]


class GeminiStatusPayload(BaseModel):
    available: bool
    retry_after: Optional[int] = None


class InterviewSourceInfo(BaseModel):
    source: GeminiSource
    fallback_reason: Optional[str] = None  # quota_exceeded | api_error | timeout | null
    gemini_status: Optional[GeminiStatusPayload] = None

