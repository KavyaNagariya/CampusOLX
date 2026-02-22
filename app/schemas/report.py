from pydantic import BaseModel
from datetime import datetime
from app.core.constants import ReportReason


class ReportCreate(BaseModel):
    item_id: int
    reason: ReportReason
    description: str


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    item_id: int
    reason: ReportReason
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}

