"""
Pydantic-схемы для валидации запросов и ответов API
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

# ============================================================
# АУТЕНТИФИКАЦИЯ
# ============================================================


class UserRegister(BaseModel):
    """Схема для регистрации."""

    username: str = Field(
        ..., min_length=3, max_length=50, description="Имя пользователя"
    )
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., min_length=6, description="Пароль (минимум 6 символов)")


class UserLogin(BaseModel):
    """Схема для входа."""

    username: str = Field(..., description="Имя пользователя")
    password: str = Field(..., description="Пароль")


class TokenResponse(BaseModel):
    """Ответ с токеном."""

    access_token: str
    token_type: str = "bearer"


# ============================================================
# ПОЛЬЗОВАТЕЛИ
# ============================================================


class UserResponse(BaseModel):
    """Ответ с данными пользователя."""

    user_id: UUID
    username: str
    email: str
    role: str
    balance: float
    created_at: datetime


class UserBalanceResponse(BaseModel):
    """Ответ с балансом пользователя."""

    user_id: UUID
    balance: float


# ============================================================
# БАЛАНС И ТРАНЗАКЦИИ
# ============================================================


class BalanceDepositRequest(BaseModel):
    """Запрос на пополнение баланса."""

    amount: float = Field(..., gt=0, description="Сумма пополнения (> 0)")


class TransactionResponse(BaseModel):
    """Ответ с информацией о транзакции."""

    transaction_id: UUID
    amount: float
    type: str
    description: str
    timestamp: datetime
    balance_after: float


class BalanceDepositResponse(BaseModel):
    """Ответ после пополнения."""

    success: bool
    amount: float
    new_balance: float
    transaction_id: UUID


# ============================================================
# ML ПРЕДСКАЗАНИЯ
# ============================================================


class PredictRequest(BaseModel):
    """Запрос на предсказание."""

    data: Dict[str, Any] = Field(..., description="Данные для модели")


class PredictResponse(BaseModel):
    """Ответ с предсказанием."""

    success: bool
    result: Dict[str, Any]
    credits_used: float
    credits_remaining: float


# ============================================================
# МОДЕЛИ
# ============================================================


class ModelResponse(BaseModel):
    """Ответ с информацией о модели."""

    id: UUID
    name: str
    version: str
    type: str
    active: bool


# ============================================================
# ИСТОРИЯ
# ============================================================


class PredictionHistoryResponse(BaseModel):
    """Ответ с историей предсказаний."""

    id: UUID
    model_id: Optional[UUID]
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]]
    cost: float
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Стандартный ответ с ошибкой."""

    detail: str
