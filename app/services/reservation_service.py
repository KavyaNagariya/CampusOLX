from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload, selectinload
from app.models.reservation import Reservation
from app.models.item import Item
from app.models.user import User
from app.core.constants import ReservationStatus, ItemStatus


def _reservation_load_options():
    """Shared eager-load options for reservation queries."""
    return [
        joinedload(Reservation.item)
        .joinedload(Item.seller)
        .selectinload(User.ratings_received),
        joinedload(Reservation.buyer),
    ]


async def _reload_reservation(db: AsyncSession, reservation_id: int) -> Reservation:
    """Reload a reservation with all relationships for the response schema."""
    stmt = (
        select(Reservation)
        .options(*_reservation_load_options())
        .where(Reservation.id == reservation_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def request_reservation(
    db: AsyncSession, item_id: int, buyer_id: int
) -> Reservation:
    """Create a reservation request. Item stays available for other buyers."""
    stmt = select(Item).where(Item.id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.seller_id == buyer_id:
        raise HTTPException(
            status_code=400, detail="You can't reserve your own product"
        )

    if item.status != ItemStatus.AVAILABLE:
        raise HTTPException(
            status_code=400, detail="Item is not available for reservation"
        )

    # Prevent duplicate active reservations from the same buyer
    existing_stmt = select(Reservation).where(
        Reservation.item_id == item_id,
        Reservation.buyer_id == buyer_id,
        Reservation.status.in_([ReservationStatus.REQUESTED, ReservationStatus.ACCEPTED]),
    )
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="You already have an active reservation for this item",
        )

    reservation = Reservation(
        item_id=item_id, buyer_id=buyer_id, status=ReservationStatus.REQUESTED
    )
    db.add(reservation)
    await db.commit()

    return await _reload_reservation(db, reservation.id)


async def accept_reservation(
    db: AsyncSession, reservation_id: int, seller_id: int
) -> Reservation:
    """Seller accepts a reservation request. Buyer details become visible."""
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation_id)
    )
    result = await db.execute(stmt)
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.item.seller_id != seller_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to accept this reservation"
        )

    if reservation.status != ReservationStatus.REQUESTED:
        raise HTTPException(
            status_code=400, detail="Reservation is not in requested state"
        )

    reservation.status = ReservationStatus.ACCEPTED
    await db.commit()

    return await _reload_reservation(db, reservation.id)


async def reject_reservation(
    db: AsyncSession, reservation_id: int, seller_id: int
) -> Reservation:
    """Seller rejects a reservation request. Item stays available."""
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation_id)
    )
    result = await db.execute(stmt)
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.item.seller_id != seller_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to reject this reservation"
        )

    if reservation.status != ReservationStatus.REQUESTED:
        raise HTTPException(
            status_code=400, detail="Reservation is not in requested state"
        )

    reservation.status = ReservationStatus.REJECTED
    await db.commit()

    return await _reload_reservation(db, reservation.id)


async def cancel_reservation(
    db: AsyncSession, reservation_id: int, user_id: int
) -> Reservation:
    """Cancel a reservation. Buyer or seller can cancel."""
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation_id)
    )
    result = await db.execute(stmt)
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.buyer_id != user_id and reservation.item.seller_id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to cancel this reservation"
        )

    if reservation.status not in [
        ReservationStatus.REQUESTED,
        ReservationStatus.ACCEPTED,
    ]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a reservation that is already cancelled, rejected, or sold",
        )

    reservation.status = ReservationStatus.CANCELLED
    await db.commit()

    return await _reload_reservation(db, reservation.id)


async def confirm_sale(
    db: AsyncSession, reservation_id: int, seller_id: int
) -> Reservation:
    """Seller confirms the sale. Item marked SOLD, other reservations auto-rejected."""
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation_id)
    )
    result = await db.execute(stmt)
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.item.seller_id != seller_id:
        raise HTTPException(
            status_code=403, detail="Only the seller can confirm the sale"
        )

    if reservation.status not in [
        ReservationStatus.REQUESTED,
        ReservationStatus.ACCEPTED,
    ]:
        raise HTTPException(
            status_code=400, detail="Cannot confirm sale for this reservation"
        )

    reservation.status = ReservationStatus.ACCEPTED
    reservation.item.status = ItemStatus.SOLD
    reservation.item.reserved_by_id = reservation.buyer_id

    # Auto-reject all other pending reservations for this item
    other_stmt = select(Reservation).where(
        Reservation.item_id == reservation.item_id,
        Reservation.id != reservation.id,
        Reservation.status.in_(
            [ReservationStatus.REQUESTED, ReservationStatus.ACCEPTED]
        ),
    )
    other_result = await db.execute(other_stmt)
    for other_res in other_result.scalars().all():
        other_res.status = ReservationStatus.REJECTED

    await db.commit()

    return await _reload_reservation(db, reservation.id)


async def get_reservation(
    db: AsyncSession, reservation_id: int, user_id: int
) -> Reservation:
    """Get a specific reservation. User must be buyer or seller."""
    stmt = (
        select(Reservation)
        .options(*_reservation_load_options())
        .where(Reservation.id == reservation_id)
    )
    result = await db.execute(stmt)
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.buyer_id != user_id and reservation.item.seller_id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to view this reservation"
        )

    return reservation


async def list_my_reservations(db: AsyncSession, user_id: int) -> list[Reservation]:
    """Get all reservations where user is either buyer or seller."""
    stmt = (
        select(Reservation)
        .options(*_reservation_load_options())
        .where(
            or_(
                Reservation.buyer_id == user_id,
                Reservation.item.has(Item.seller_id == user_id),
            )
        )
        .order_by(Reservation.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
