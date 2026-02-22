from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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


async def list_available_items(db: AsyncSession) -> list[Item]:
    result = await db.execute(
        select(Item).where(Item.status == ItemStatus.AVAILABLE)
    )
    return result.scalars().all()
