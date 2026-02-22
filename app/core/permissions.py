from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.api.deps import get_current_user
from app.core.constants import UserRole


def require_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blocked",
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
