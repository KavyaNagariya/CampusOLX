from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base
from app.models import user, item, category, reservation, report, rating
from app.core.constants import DEFAULT_CATEGORIES


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Optional: seed default categories
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from app.models.category import Category
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Category))
        existing = result.scalars().all()

        if not existing:
            session.add_all(
                [Category(name=name) for name in DEFAULT_CATEGORIES]
            )
            await session.commit()
