import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException, status
from app.core.config import Settings


ALLOWED_EXTENSIONS = {"image/jpeg", "image/png", "image/webp"}

async def upload_item_image(file: UploadFile) -> str:
    """
    Validates, uploads, and aggressively optimizes an image via Cloudinary.
    Returns the secure URL of the optimized image.
    """
    # 1. Security Check: Validate content type
    if file.content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, and WebP are allowed."
        )

    try:
        # Read the file into memory (FastAPI handles this safely for small files)
        file_content = await file.read()

        # 2. Upload with Eager Transformations (Cost & Bandwidth optimization)
        response = cloudinary.uploader.upload(
            file_content,
            folder="campus_marketplace/items", # Keeps your Cloudinary dashboard organized
            transformation=[
                # Resize to a sensible maximum for a marketplace
                {"width": 800, "height": 800, "crop": "limit"},
                # 'auto' forces Cloudinary to serve WebP/AVIF to supported browsers
                {"quality": "auto", "fetch_format": "auto"} 
            ]
        )
        
        # 3. Return the HTTPS URL
        return response.get("secure_url")

    except Exception as e:
        # Failure Mode: If Cloudinary is down or credentials fail
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}"
        )