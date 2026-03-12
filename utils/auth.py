from datetime import datetime, timedelta, timezone

# 1. Use the modern PyJWT library you already installed
import jwt
from jwt.exceptions import InvalidTokenError

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional

# 2. Use the secure Argon2 hasher instead of bcrypt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# 3. Import your settings (assuming config.py is in the utils folder)
from .config import settings
from db.database import get_db
from db.models import UserRecord

security = HTTPBearer(auto_error=False)
password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """Hashes a password using the modern Argon2 algorithm."""
    return password_hash.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifies a plain password against the hashed version."""
    return password_hash.verify(plain, hashed)


def create_token(user_id: int) -> str:
    """Generates a secure JWT token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expire}, settings.secret_key, algorithm=settings.algorithm)


def get_current_user(
  credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> UserRecord:
    """Dependency to extract and verify the current logged-in user."""
    if not credentials or credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization",
        )

    # Step 2: Decode JWT using PyJWT
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = int(user_id)
    except (InvalidTokenError, ValueError): # Catch PyJWT's specific error
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(UserRecord).filter(UserRecord.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user