from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext
import bcrypt
from app.core.config import get_settings

settings = get_settings()


# FIX 1: Removed bcrypt__truncate_error=False so it doesn't forcefully crash
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

# --------------------
# Password utils
# --------------------
def hash_password(password: str) -> str:
    """Uses bcrypt directly to avoid passlib version conflicts."""
    # 1. Truncate to 72 bytes strictly to prevent the ValueError
    # 2. Convert to bytes for bcrypt
    pwd_bytes = password.encode('utf-8')[:72]
    
    # 3. Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    
    # 4. Return as a string for the database
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies using bcrypt directly."""
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

# --------------------
# JWT utils
# --------------------
def create_access_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None, # FIX 3: Changed timezone to timedelta
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # FIX 3: Changed timezone() to timedelta()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    payload = {
        "exp": expire,
        "sub": str(subject),
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt
