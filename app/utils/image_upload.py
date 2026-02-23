import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, status, UploadFile
from app.core.config import get_settings

settings = get_settings()

async def upload_item_image(file: UploadFile) -> str:
    # 1. Validation
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    try:
        file_content = await file.read()

        # SECURE: Using variables from settings instead of hardcoded strings
        response = cloudinary.uploader.upload(
            file_content,
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            folder="campus_marketplace/items",
            transformation=[
                {"width": 800, "height": 800, "crop": "limit"},
                {"quality": "auto", "fetch_format": "auto"} 
            ]
        )
        return response.get("secure_url")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cloudinary Error: {str(e)}"
        )
