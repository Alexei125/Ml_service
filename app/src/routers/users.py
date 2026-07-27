"""
Роутер для пользователей
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from ..database import get_db
from ..repositories import UserRepository, WalletRepository
from ..schemas import UserResponse, UserBalanceResponse
from ..auth import get_current_user
from ..orm_models import DBUser

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: DBUser = Depends(get_current_user)):
    """Получить информацию о текущем пользователе."""
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value,
        "balance": current_user.wallet.balance if current_user.wallet else 0.0,
        "created_at": current_user.created_at,
    }


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Получить информацию о пользователе по ID (публичный)."""
    repo = UserRepository(db)
    user = repo.get_user_with_wallet(UUID(user_id))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "balance": user.wallet.balance if user.wallet else 0.0,
        "created_at": user.created_at,
    }


@router.get("/{user_id}/balance", response_model=UserBalanceResponse)
def get_user_balance(user_id: str, db: Session = Depends(get_db)):
    """Получить баланс пользователя."""
    wallet_repo = WalletRepository(db)
    wallet = wallet_repo.get_wallet(UUID(user_id))
    if not wallet:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    return {"user_id": wallet.user_id, "balance": wallet.balance}
