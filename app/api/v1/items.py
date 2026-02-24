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
    offset: int = Query(0, ge=0)
):
    return await list_available_items(db=db, q=q, category_id=category_id, max_price=max_price, limit=limit, offset=offset)

@router.post("/{item_id}/image", status_code=status.HTTP_200_OK)
async def upload_image_for_item(
    item_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Attaches an image to an existing item.
    Includes BOLA (Broken Object Level Authorization) protection.
    """
    # 1. Fetch the item
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()

    # 2. Verify existence and ownership (Security Guardrail)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You can only upload images for your own items."
        )

    # 3. Upload to Cloudinary (The utility handles the 500 Failure Mode internally)
    secure_url = await upload_item_image(file)

    # 4. Save the URL to the database
    item.image_url = secure_url
    
    try:
        await db.commit()
        await db.refresh(item)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image URL to database."
        )

    return {"message": "Image uploaded successfully", "image_url": secure_url}

