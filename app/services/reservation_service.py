from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.models.reservation import Reservation
from app.models.item import Item
from app.core.constants import ReservationStatus, ItemStatus


async def request_reservation(
    db: AsyncSession, item_id: int, buyer_id: int
) -> Reservation:
    """ Making sure that our system can handle the competitive reservation for the time being - meaning " Database crashing fixing for the future use if more users came ' """
    #Locking item row to prevent the race conditions
    stmt = select(Item).where(Item.id == item_id).with_for_update()
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    #Preventing the self dealing
    if item.seller_id == buyer_id:
        raise HTTPException(status_code=400, detail="You can't reserve your own product")

    #checking availability using 5 minute reservation timeout 
    if not item.is_actually_available:
        raise HTTPException(status_code=400, detail="Item is currently reserved or sold") 

    reservation = Reservation(
        item_id=item_id,
        buyer_id=buyer_id,
        status=ReservationStatus.REQUESTED
    )
    db.add(reservation)

    item.status = ItemStatus.RESERVED
    item.reserved_at = datetime.utcnow()
    item.reserved_by_id = buyer_id

    await db.commit()
    await db.refresh(reservation)
    return reservation


async def accept_reservation(
        db: AsyncSession, reservation_id: int, seller_id: int
) -> Reservation:
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.item))
        .where(Reservation.id == reservation_id)
        .with_for_update() # Lock the reservation to prevent double-acceptance
    )
    result  = await db.execute(stmt)
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.item.seller_id != seller_id:
        raise HTTPException(status_code=403, detail="Not authorized to access")

    if reservation.status != ReservationStatus.REQUESTED:
        raise HTTPException(status_code=400, detail="Reservation is not in requested state") 
    
    reservation.status = ReservationStatus.ACCEPTED

    await db.commit()
    await db.refresh(reservation)

    return reservation
