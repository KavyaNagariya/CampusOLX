from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.item import Item
from app.schemas.reservation import (
    ReservationCreate,
    ReservationResponse,
)
from app.services.reservation_service import (
    request_reservation,
    accept_reservation,
    reject_reservation,
    cancel_reservation,
    confirm_sale,
    get_reservation,
    list_my_reservations,
)

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("/", response_model=ReservationResponse)
async def create_reservation(
    data: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new reservation request for an item."""
    return await request_reservation(
        db=db, item_id=data.item_id, buyer_id=current_user.id
    )


@router.get("/", response_model=list[ReservationResponse])
async def get_my_reservations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all reservations where user is either buyer or seller."""
    return await list_my_reservations(db, current_user.id)


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation_by_id(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific reservation by ID."""
    return await get_reservation(db, reservation_id, current_user.id)


@router.post("/{reservation_id}/accept", response_model=ReservationResponse)
async def accept_reservation_request(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seller accepts a reservation request."""
    return await accept_reservation(db, reservation_id, seller_id=current_user.id)


@router.post("/{reservation_id}/reject", response_model=ReservationResponse)
async def reject_reservation_request(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seller rejects a reservation request."""
    return await reject_reservation(db, reservation_id, seller_id=current_user.id)


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
async def cancel_reservation_request(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a reservation (buyer or seller can cancel)."""
    return await cancel_reservation(db, reservation_id, user_id=current_user.id)


@router.post("/{reservation_id}/sold", response_model=ReservationResponse)
async def confirm_item_sold(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seller confirms the item has been sold and payment received."""
    return await confirm_sale(db, reservation_id, seller_id=current_user.id)
