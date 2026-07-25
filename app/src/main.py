"""
Главный файл приложения FastAPI
Задание №3: Подключение базы данных и ORM
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import os

from sqlalchemy.orm import Session

from .database import get_db, engine
from .orm_models import Base, DBUser, DBWallet, DBMLModel
from .repositories import (
    UserRepository, WalletRepository, ModelRepository,
    HistoryRepository, InsufficientBalanceError
)
from .models import UserRole, ModelType, ClassificationModel


# ============================================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ============================================================

def init_db():
    """Создание таблиц, если их нет."""
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы (или уже существуют)")


def seed_demo_data():
    """Заполнение демо-данными, если таблицы пусты."""
    db = next(get_db())
    user_repo = UserRepository(db)

    # Проверяем, есть ли уже пользователи
    existing_admin = user_repo.get_user_by_username("admin")
    if existing_admin:
        print("✅ Демо-данные уже существуют, пропускаем инициализацию")
        return

    # Создаём администратора
    admin = user_repo.create_user("admin", "admin@ml.com", UserRole.ADMIN)
    print(f"👤 Создан администратор: {admin.username} (ID: {admin.user_id})")

    # Создаём обычного пользователя
    user = user_repo.create_user("alex", "alex@mail.com", UserRole.USER)
    print(f"👤 Создан пользователь: {user.username} (ID: {user.user_id})")

    # Пополняем баланс пользователя
    wallet_repo = WalletRepository(db)
    wallet_repo.add_balance(user.user_id, 100.0, "Начальный баланс")
    print(f"💰 Баланс пользователя {user.username} пополнен на 100 кредитов")

    # Создаём ML модель
    model_repo = ModelRepository(db)
    model = model_repo.create_model(
        name="Spam Detector",
        version="v1.0",
        model_type=ModelType.CLASSIFICATION,
        is_active=True
    )
    print(f"🤖 Создана модель: {model.name} (v{model.version})")

    db.commit()
    print("✅ Демо-данные успешно загружены!")


# Выполняем инициализацию при старте
init_db()
seed_demo_data()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(title="ML Service API", version="1.0.0")


# ============================================================
# PYDANTIC МОДЕЛИ ДЛЯ API
# ============================================================

class CreateUserRequest(BaseModel):
    username: str
    email: str
    role: str = "user"  # "admin" или "user"


class PredictRequest(BaseModel):
    user_id: str
    model_id: str
    data: Dict[str, Any]


class BalanceRequest(BaseModel):
    user_id: str
    amount: float


# ============================================================
# ЭНДПОИНТЫ
# ============================================================

@app.get("/")
def root():
    return {"status": "ok", "service": "ML Service"}


@app.post("/users")
def create_user(request: CreateUserRequest, db: Session = Depends(get_db)):
    """Создать нового пользователя."""
    repo = UserRepository(db)

    # Проверяем, что пользователь не существует
    existing = repo.get_user_by_username(request.username)
    if existing:
        raise HTTPException(400, "User already exists")

    role = UserRole.ADMIN if request.role.lower() == "admin" else UserRole.USER
    user = repo.create_user(request.username, request.email, role)

    return {
        "user_id": str(user.user_id),
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "balance": 0.0
    }


@app.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Получить информацию о пользователе."""
    repo = UserRepository(db)
    user = repo.get_user_with_wallet(UUID(user_id))
    if not user:
        raise HTTPException(404, "User not found")

    return {
        "user_id": str(user.user_id),
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "balance": user.wallet.balance if user.wallet else 0.0
    }


@app.post("/balance/deposit")
def deposit(request: BalanceRequest, db: Session = Depends(get_db)):
    """Пополнить баланс пользователя."""
    try:
        wallet_repo = WalletRepository(db)
        transaction = wallet_repo.add_balance(
            UUID(request.user_id),
            request.amount,
            "API deposit"
        )

        # Получаем обновлённый баланс
        wallet = wallet_repo.get_wallet(UUID(request.user_id))
        return {
            "success": True,
            "amount": request.amount,
            "new_balance": wallet.balance if wallet else 0.0,
            "transaction_id": str(transaction.transaction_id)
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/predict")
def predict(request: PredictRequest, db: Session = Depends(get_db)):
    """Выполнить предсказание."""
    try:
        user_id = UUID(request.user_id)
        model_id = UUID(request.model_id)

        user_repo = UserRepository(db)
        user = user_repo.get_user_with_wallet(user_id)
        if not user:
            raise HTTPException(404, "User not found")

        model_repo = ModelRepository(db)
        model = model_repo.get_model_by_id(model_id)
        if not model or not model.is_active:
            raise HTTPException(404, "Model not found or inactive")

        # Проверяем баланс
        cost = 1.0
        if user.wallet.balance < cost:
            raise InsufficientBalanceError(f"Need {cost}, have {user.wallet.balance}")

        # Имитируем предсказание (в реальности здесь вызывается ML модель)
        # Можно использовать ClassificationModel из models.py
        result = {"class": "spam", "confidence": 0.95}

        # Списываем средства
        wallet_repo = WalletRepository(db)
        transaction = wallet_repo.deduct_balance(
            user_id,
            cost,
            f"Prediction: {model.name} (v{model.version})"
        )

        # Сохраняем историю
        history_repo = HistoryRepository(db)
        history = history_repo.create_prediction_history(
            user_id=user_id,
            model_id=model_id,
            input_data=request.data,
            output_data=result,
            cost=cost,
            duration_ms=0.0,
            transaction_id=transaction.transaction_id
        )

        return {
            "success": True,
            "result": result,
            "credits_used": cost,
            "credits_remaining": user.wallet.balance
        }

    except InsufficientBalanceError as e:
        raise HTTPException(402, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/users/{user_id}/balance")
def get_balance(user_id: str, db: Session = Depends(get_db)):
    """Получить баланс пользователя."""
    wallet_repo = WalletRepository(db)
    wallet = wallet_repo.get_wallet(UUID(user_id))
    if not wallet:
        raise HTTPException(404, "User not found")

    return {
        "user_id": user_id,
        "balance": wallet.balance
    }


@app.get("/users/{user_id}/history")
def get_history(user_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """Получить историю транзакций пользователя."""
    wallet_repo = WalletRepository(db)
    transactions = wallet_repo.get_transactions(UUID(user_id), limit)

    return {
        "user_id": user_id,
        "transactions": [
            {
                "id": str(tx.transaction_id),
                "amount": tx.amount,
                "type": tx.type.value,
                "description": tx.description,
                "timestamp": tx.timestamp.isoformat(),
                "balance_after": tx.balance_after
            }
            for tx in transactions
        ]
    }


@app.get("/predictions/users/{user_id}")
def get_predictions_history(user_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """Получить историю предсказаний пользователя."""
    history_repo = HistoryRepository(db)
    history = history_repo.get_user_history(UUID(user_id), limit)

    return {
        "user_id": user_id,
        "predictions": [
            {
                "id": str(h.history_id),
                "model_id": str(h.model_id) if h.model_id else None,
                "input": h.input_data,
                "output": h.output_data,
                "cost": h.cost,
                "timestamp": h.timestamp.isoformat()
            }
            for h in history
        ]
    }


@app.get("/models")
def list_models(db: Session = Depends(get_db)):
    """Получить список всех моделей."""
    model_repo = ModelRepository(db)
    models = model_repo.list_models()

    return {
        "models": [
            {
                "id": str(m.model_id),
                "name": m.name,
                "version": m.version,
                "type": m.model_type.value,
                "active": m.is_active
            }
            for m in models
        ]
    }