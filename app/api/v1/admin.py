from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.permissions import require_admin
from app.services.admin_service import block_user, remove_item

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/block-user/{user_id}")
async def admin_block_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    await block_user(db, user_id)
    return {"message": "User blocked"}


@router.delete("/remove-item/{item_id}")
async def admin_remove_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    await remove_item(db, item_id)
    return {"message": "Item removed"}

