"""
Роутер для аутентификации
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from datetime import timedelta

from ..database import get_db
from ..repositories import UserRepository
from ..schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from ..auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from ..models import UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Регистрация нового пользователя."""
    repo = UserRepository(db)

    # Проверяем, что пользователь не существует
    existing = repo.get_user_by_username(user_data.username)
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already exists")

    existing_email = db.query(
        repo.db.query(repo.db.model_class)
        .filter(repo.db.model_class.email == user_data.email)
        .first()
    )
    if existing_email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    # Создаём пользователя
    user = repo.create_user(
        username=user_data.username,
        email=user_data.email,
        role=UserRole.USER,
        password_hash=get_password_hash(user_data.password),
    )

    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "balance": user.wallet.balance if user.wallet else 0.0,
        "created_at": user.created_at,
    }


@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Авторизация пользователя."""
    repo = UserRepository(db)
    user = repo.get_user_by_username(user_data.username)
    if not user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid username or password"
        )

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid username or password"
        )

    # Создаём JWT
    access_token = create_access_token(
        data={"sub": str(user.user_id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": access_token, "token_type": "bearer"}
