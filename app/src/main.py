"""
Главный файл приложения FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from .database import get_db, engine
from .orm_models import Base
from .repositories import UserRepository, ModelRepository, WalletRepository
from .models import UserRole, ModelType
from .routers import auth, users, balance, predict, history, models
from .auth import get_password_hash


def init_db():
    """Создание таблиц, если их нет."""
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы (или уже существуют)")


def seed_demo_data():
    """Заполнение демо-данными, если таблицы пусты."""
    db = next(get_db())
    user_repo = UserRepository(db)
    wallet_repo = WalletRepository(db)
    model_repo = ModelRepository(db)

    # Проверяем, есть ли уже пользователи
    existing_admin = user_repo.get_user_by_username("admin")
    if existing_admin:
        print("✅ Демо-данные уже существуют, пропускаем инициализацию")
        return

    # Создаём администратора
    admin = user_repo.create_user(
        "admin",
        "admin@ml.com",
        UserRole.ADMIN,
        password_hash=get_password_hash("admin123")
    )
    print(f"👤 Создан администратор: {admin.username} (пароль: admin123)")

    # Создаём обычного пользователя
    user = user_repo.create_user(
        "alex",
        "alex@mail.com",
        UserRole.USER,
        password_hash=get_password_hash("user123")
    )
    print(f"👤 Создан пользователь: {user.username} (пароль: user123)")

    # Пополняем баланс пользователя
    wallet_repo.add_balance(user.user_id, 100.0, "Начальный баланс")
    print(f"💰 Баланс пользователя {user.username} пополнен на 100 кредитов")

    # Создаём ML модель
    model = model_repo.create_model(
        name="Spam Detector",
        version="v1.0",
        model_type=ModelType.CLASSIFICATION.value,
        is_active=True
    )
    print(f"🤖 Создана модель: {model.name} (v{model.version})")

    db.commit()
    print("✅ Демо-данные успешно загружены!")


# Инициализация
init_db()
seed_demo_data()

# Создаём приложение
app = FastAPI(
    title="ML Service API",
    version="1.0.0",
    description="ML сервис с асинхронной обработкой через RabbitMQ"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(balance.router)
app.include_router(predict.router)
app.include_router(history.router)
app.include_router(models.router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "ML Service API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }