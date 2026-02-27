from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.permissions import require_admin
from app.services.admin_service import block_user, remove_item
from app.models.item import Item
from app.models.user import User
from sqlalchemy import select

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/block-user/{user_id}")
async def admin_block_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    await block_user(db, user_id)
    return {"message": "User blocked"}


@router.delete("/soft-delete-item/{item_id}")
async def admin_soft_delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    await remove_item(db, item_id)
    return {"message": "Item removed (soft delete)"}


@router.delete("/hard-delete-item/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_hard_delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
    await db.commit()
    return None
