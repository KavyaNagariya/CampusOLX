from pydantic import AfterValidator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime
from app.models.item import Item
from app.schemas.item import ItemCreate
from app.core.constants import ItemStatus
from fastapi import HTTPException
from app.models.reservation import Reservation

async def create_item(
    db: AsyncSession, item_in: ItemCreate, seller_id: int
) -> Item:
    item = Item(**item_in.model_dump(), seller_id=seller_id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def list_available_items(
        db: AsyncSession,
        q: str = None,
        category_id: int = None,
        max_price: int = None,
        limit: int = 20,
        offset: int = 0
) -> list[Item]:
    query = select(Item).where(Item.status == ItemStatus.AVAILABLE)

    if q:
        search_term = f"%{q}%"
        query = query.filter(
                or_(
                    Item.title.ilike(search_term),
                    Item.description.ilike(search_term)
                )
        )

    if category_id:
        query = query.filter(Item.category_id == category_id)

    if max_price:
        query = query.filter(Item.price <= max_price)

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()

async def reserve_item(db: AsyncSession, item_id: int, buyer_id: int) -> Item:
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.status != ItemStatus.AVAILABLE:
        raise HTTPException(
            status_code=400,
            detail=f"Item is currently {item.status}"
        )
    if item.seller_id == buyer_id:
        raise HTTPException(
            status_code=400,
            detail=f"You cannot buy your own item!"
            )

    item.status = ItemStatus.RESERVED
    item.reserved_by_id = buyer_id
    item.reserved_at = datetime.now()

    new_reservation = Reservation(
        item_id=item.id,
        buyer_id=buyer_id,
        status="REQUESTED"     )
    db.add(new_reservation)

    try:
        await db.commit()
        await db.refresh(item)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database update failed: {str(e)}") 
    return item

async def mark_item_as_sold(db: AsyncSession, item_id: int, seller_id: int) -> Item:
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.seller_id != seller_id:
        raise HTTPException(status_code=403, detail="Only the seller can confirm the sale.")
    
    item.status = ItemStatus.SOLD
    await db.commit()
    await db.refresh(item)
    return item

async def cancel_reservation(db: AsyncSession, item_id: int, user_id: int) -> Item:
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()

    if not item or item.status != ItemStatus.RESERVED:
        raise HTTPException(status_code=400, detail="Item is not currently reserved.")
    
    # Only the seller or the person who reserved it can cancel
    if user_id not in [item.seller_id, item.reserved_by_id]:
        raise HTTPException(status_code=403, detail="Unauthorized to cancel this reservation.")

    item.status = ItemStatus.AVAILABLE
    item.reserved_by_id = None
    item.reserved_at = None
    
    await db.commit()
    await db.refresh(item)
    return item
