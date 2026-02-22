
from pydantic import BaseModel
from datetime import datetime
from app.core.constants import ReservationStatus


class ReservationCreate(BaseModel):
    item_id: int


class ReservationResponse(BaseModel):
    id: int
    item_id: int
    buyer_id: int
    status: ReservationStatus
    created_at: datetime

    model_config = {"from_attributes": True}
