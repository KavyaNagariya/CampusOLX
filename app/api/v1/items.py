from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemResponse
from app.utils.image_upload import upload_item_image
from app.services.item_service import create_item, list_available_items
from typing import Optional

router = APIRouter(prefix="/items", tags=["Items"])


@router.post("/", response_model=ItemResponse)
async def post_item(
    item_in: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_item(db, item_in, current_user.id)


@router.get("/", response_model=list[ItemResponse], status_code=status.HTTP_200_OK)
async def browse_items(
    db: AsyncSession = Depends(get_db),
    q: Optional[str] = Query(None, description="Search title or description"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    max_price: Optional[int] = Query(None, description="Maximum price in price"),
    limit: int = Query(20, ge=0, le=100),
    offset: int = Query(0, ge=0),
):
    return await list_available_items(
        db=db,
        q=q,
        category_id=category_id,
        max_price=max_price,
        limit=limit,
        offset=offset,
    )


@router.get("/me", response_model=list[ItemResponse])
async def get_my_listings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch all items posted by the current logged-in user."""
    result = await db.execute(select(Item).where(Item.seller_id == current_user.id))
    return result.scalars().all()


@router.get("/purchases", response_model=list[ItemResponse])
async def get_my_purchases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch all items currently reserved by the logged-in user."""
    result = await db.execute(
        select(Item).where(Item.reserved_by_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific item by ID."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/{item_id}/image", status_code=status.HTTP_200_OK)
async def upload_image_for_item(
    item_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Attaches an image to an existing item. Supports up to 4 images via comma separation.
    """
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload images for your own items.",
        )

    # Check limits first before expensive upload
    current_urls = item.image_url.split(",") if item.image_url else []
    if len(current_urls) >= 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum of 4 images allowed per item.",
        )

    secure_url = await upload_item_image(file)

    current_urls.append(secure_url)
    item.image_url = ",".join(current_urls)

    try:
        await db.commit()
        await db.refresh(item)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image URL to database.",
        )

    return {"message": "Image uploaded successfully", "image_url": item.image_url}


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an item. Only the seller who posted it or an admin can delete it."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.seller_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own items. Admins can delete any item.",
        )

    await db.delete(item)
    await db.commit()
    return None
