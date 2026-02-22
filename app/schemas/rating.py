from pydantic import BaseModel
from datetime import datetime


class RatingCreate(BaseModel):
    rated_user_id: int
    score: int  # 1 to 5


class RatingResponse(BaseModel):
    id: int
    rater_id: int
    rated_user_id: int
    score: int
    created_at: datetime

    model_config = {"from_attributes": True}
