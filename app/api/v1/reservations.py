from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.reservation import (
    ReservationCreate,
    ReservationResponse,
)
from app.services.reservation_service import (
    request_reservation,
    accept_reservation,
)

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("/", response_model=ReservationResponse)
async def reserve_item(
    data: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await request_reservation(
        db=db, item_id=data.item_id, buyer_id=current_user.id
    )


@router.post("/{reservation_id}/accept", response_model=ReservationResponse)
async def accept_request(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await accept_reservation(db, reservation_id, seller_id=current_user.id)

