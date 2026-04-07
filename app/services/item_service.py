from pydantic import AfterValidator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime
from app.models.item import Item
from app.schemas.item import ItemCreate
from app.core.constants import ItemStatus


async def create_item(db: AsyncSession, item_in: ItemCreate, seller_id: int) -> Item:
    item_data = item_in.model_dump()
    if item_data.get("available_till") and item_data["available_till"].tzinfo:
        item_data["available_till"] = item_data["available_till"].replace(tzinfo=None)
    item = Item(**item_data, seller_id=seller_id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


from sqlalchemy.orm import selectinload
from app.models.user import User

async def list_available_items(
    db: AsyncSession,
    q: str = None,
    category_id: int = None,
    max_price: int = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Item]:
    query = select(Item).options(
        selectinload(Item.seller).selectinload(User.ratings_received)
    ).where(Item.status == ItemStatus.AVAILABLE)

    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(Item.title.ilike(search_term), Item.description.ilike(search_term))
        )

    if category_id:
        query = query.filter(Item.category_id == category_id)

    if max_price:
        query = query.filter(Item.price <= max_price)

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()
