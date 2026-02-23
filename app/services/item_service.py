from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional
from app.models.item import Item
from app.schemas.item import ItemCreate
from app.core.constants import ItemStatus


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
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    max_price: Optional[int] = None,
    limit: int = 50
) -> list[Item]:
    """
    Service function to fetch available items with dynamic filtering.
    """
    stmt = select(Item).where(Item.status == ItemStatus.AVAILABLE)
    
    # Dynamic filtering
    if q: 
        search_term = f"%{q}%" 
        stmt = stmt.where(
            or_(
                Item.title.ilike(search_term),
                Item.description.ilike(search_term)
            )
        )

    if category_id:
        stmt = stmt.where(Item.category_id == category_id)

    if max_price is not None:
        stmt = stmt.where(Item.price <= max_price)

    # Order by newest first, apply limits
    stmt = stmt.order_by(Item.created_at.desc()).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()
