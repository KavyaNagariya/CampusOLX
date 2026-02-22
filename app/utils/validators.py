from fastapi import HTTPException


def validate_price(price: int) -> None:
    if price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Price must be greater than zero",
        )


def validate_rating(score: int) -> None:
    if score < 1 or score > 5:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1 and 5",
        )

