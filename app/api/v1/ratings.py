from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.rating import Rating
from app.schemas.rating import RatingCreate, RatingResponse

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.post("/", response_model=RatingResponse)
async def rate_user(
    rating_in: RatingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rating = Rating(
        rater_id=current_user.id,
        rated_user_id=rating_in.rated_user_id,
        score=rating_in.score,
    )
    db.add(rating)
    await db.commit()
    await db.refresh(rating)
    return rating

