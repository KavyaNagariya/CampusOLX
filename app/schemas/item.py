from pydantic import BaseModel
from datetime import datetime
from app.core.constants import ItemStatus


class ItemBase(BaseModel):
    title: str
    description: str
    price: int
    pickup_location: str
    available_till: datetime
    category_id: int


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int
    status: ItemStatus
    seller_id: int
    created_at: datetime
    image_url: str | None = None
    reserved_at: datetime | None = None
    reserved_by_id: int | None = None

    model_config = {"from_attributes": True}

