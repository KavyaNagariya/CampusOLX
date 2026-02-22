from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.item import Item
from app.core.constants import ItemStatus


async def block_user(db: AsyncSession, user_id: int) -> None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.is_blocked = True
    await db.commit()


async def remove_item(db: AsyncSession, item_id: int) -> None:
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one()
    item.status = ItemStatus.SOLD  # soft remove
    await db.commit()

