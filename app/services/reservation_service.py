from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload
from app.models.reservation import Reservation
from app.models.item import Item
from app.core.constants import ReservationStatus, ItemStatus


async def request_reservation(
    db: AsyncSession, item_id: int, buyer_id: int
) -> Reservation:
    """Create a reservation request with row locking to prevent race conditions."""
    stmt = select(Item).where(Item.id == item_id).with_for_update()
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.seller_id == buyer_id:
        raise HTTPException(
            status_code=400, detail="You can't reserve your own product"
        )

    if not item.is_actually_available:
        raise HTTPException(
            status_code=400, detail="Item is currently reserved or sold"
        )

    reservation = Reservation(
        item_id=item_id, buyer_id=buyer_id, status=ReservationStatus.REQUESTED
    )
    db.add(reservation)

    item.status = ItemStatus.RESERVED
    item.reserved_at = datetime.utcnow().replace(tzinfo=None)
    item.reserved_by_id = buyer_id

    await db.commit()

    # Reload with joinedload to satisfy ReservationResponse schema
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def accept_reservation(
    db: AsyncSession, reservation_id: int, seller_id: int
) -> Reservation:
    """Seller accepts a reservation request."""
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation_id)
        .with_for_update()
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

    # Reload with joinedload to satisfy ReservationResponse schema
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def reject_reservation(
    db: AsyncSession, reservation_id: int, seller_id: int
) -> Reservation:
    """Seller rejects a reservation request and releases the item."""
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation_id)
        .with_for_update()
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

    reservation.item.status = ItemStatus.AVAILABLE
    reservation.item.reserved_by_id = None
    reservation.item.reserved_at = None

    await db.commit()

    # Reload with joinedload to satisfy ReservationResponse schema
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def cancel_reservation(
    db: AsyncSession, reservation_id: int, user_id: int
) -> Reservation:
    """Cancel a reservation. Buyer or seller can cancel."""
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation_id)
        .with_for_update()
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

    reservation.item.status = ItemStatus.AVAILABLE
    reservation.item.reserved_by_id = None
    reservation.item.reserved_at = None

    await db.commit()

    # Reload with joinedload to satisfy ReservationResponse schema
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def confirm_sale(
    db: AsyncSession, reservation_id: int, seller_id: int
) -> Reservation:
    """Seller confirms the item has been sold. Marks item as SOLD and reservation as ACCEPTED."""
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation_id)
        .with_for_update()
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

    await db.commit()

    # Reload with joinedload to satisfy ReservationResponse schema
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_reservation(
    db: AsyncSession, reservation_id: int, user_id: int
) -> Reservation:
    """Get a specific reservation. User must be buyer or seller."""
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
            status_code=403, detail="Not authorized to view this reservation"
        )

    return reservation


async def list_my_reservations(db: AsyncSession, user_id: int) -> list[Reservation]:
    """Get all reservations where user is either buyer or seller."""
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
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
