"""
Настройка подключения к базе данных
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# Загружаем переменные окружения
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ml_service")

# Создаём движок SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Включаем логирование SQL-запросов (для отладки)
    pool_size=10,
    max_overflow=20
)

# Создаём фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для ORM-моделей
Base = declarative_base()

# Функция для получения сессии (для Dependency Injection в FastAPI)
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
