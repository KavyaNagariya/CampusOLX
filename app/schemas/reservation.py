from pydantic import BaseModel
from datetime import datetime
from app.core.constants import ReservationStatus


from app.schemas.item import ItemResponse


class ReservationCreate(BaseModel):
    item_id: int


class BuyerInfo(BaseModel):
    id: int
    name: str
    email: str
    phone: str

    model_config = {"from_attributes": True}


class ReservationResponse(BaseModel):
    id: int
    item_id: int
    buyer_id: int
    status: ReservationStatus
    created_at: datetime
    item: ItemResponse
    buyer: BuyerInfo | None = None

    model_config = {"from_attributes": True}
