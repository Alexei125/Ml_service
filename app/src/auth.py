"""
Аутентификация и JWT
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .repositories import UserRepository
import os

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ============================================================
# ПАРОЛИ
# ============================================================

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if len(plain_password) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)


# ============================================================
# JWT
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT-токена."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Декодирование JWT-токена."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Получение текущего пользователя из токена."""
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from uuid import UUID

    repo = UserRepository(db)
    user = repo.get_user_by_id(UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
