"""
Главный файл приложения FastAPI
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from uuid import UUID
import os

from .models import MLService, User, UserRole, MLModel, InsufficientBalanceError, AdminUser, RegularUser, \
    ClassificationModel, ModelType

# ========== ИНИЦИАЛИЗАЦИЯ ==========

# Создаем сервис
service = MLService()
# Создаем админа и пользователя
admin = AdminUser("admin", "admin@mail.com", UserRole.ADMIN)
user = RegularUser("alex", "alex@mail.com", UserRole.USER)

service.register_user(admin)
service.register_user(user)

# Админ пополняет баланс пользователя
service.admin_add_balance(admin.user_id, user.user_id, 100)

# Создаем и активируем модель
model = ClassificationModel("Spam Detector", "v1.0", ModelType.CLASSIFICATION)
service.add_model(model)
model.activate()

print(f"✅ Сервис запущен! Пользователь: {user.username}, баланс: {user.balance}")

# ========== FASTAPI ==========

app = FastAPI(title="ML Service API", version="1.0.0")


# ========== МОДЕЛИ ДЛЯ API ==========


class PredictRequest(BaseModel):
    user_id: str
    model_id: str
    data: Dict[str, Any]


class BalanceRequest(BaseModel):
    user_id: str
    amount: float


# ========== ЭНДПОИНТЫ ==========


@app.get("/")
def root():
    return {"status": "ok", "service": "ML Service"}


@app.post("/predict")
def predict(request: PredictRequest):
    try:
        result = service.predict(
            UUID(request.user_id),
            UUID(request.model_id),
            request.data,
        )
        return {"success": True, "result": result}
    except InsufficientBalanceError as e:
        raise HTTPException(402, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("balance/deposit")
def deposit(request: BalanceRequest):
    try:
        user_id = UUID(request.user_id)
        tx = service.admin_add_balance(admin, user_id, request.amount)
        return {
            "success": True,
            "amount": request.amount,
            "new_balance": service.get_user(user_id).balance,
        }
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/user/{user_id}/balance")
def get_balance(user_id: str):
    user = service.get_user(UUID(user_id))
    if not user:
        raise HTTPException(404, f"User {user_id} not found")
    return {"user_id": user_id, "balance": user.balance}
