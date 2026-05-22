import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.models.enums import UserRole


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(
    user_id: uuid.UUID,
    role: UserRole,
    token_version: int,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "ver": token_version,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        print(repr(settings.JWT_SECRET_KEY), repr(settings.JWT_ALGORITHM))
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def generate_refresh_token() -> str:
    return str(uuid.uuid4())


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
