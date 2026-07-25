"""
ORM-модели для базы данных
"""

from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, UUID, Text, JSON, Integer
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import uuid
import enum

from .database import Base


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ENUM (для SQLAlchemy)
# ============================================================

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    ADMIN_DEPOSIT = "admin_deposit"


class ModelType(str, enum.Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================
# ORM-МОДЕЛИ
# ============================================================

class DBUser(Base):
    """Таблица пользователей (только профиль)."""
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.now)

    # Связи
    wallet = relationship("DBWallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    predictions = relationship("DBPredictionHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DBUser(id={self.user_id}, username={self.username}, role={self.role.value})>"


class DBWallet(Base):
    """Таблица кошельков (баланс и транзакции)."""
    __tablename__ = "wallets"

    wallet_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # Связи
    user = relationship("DBUser", back_populates="wallet")
    transactions = relationship("DBTransaction", back_populates="wallet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DBWallet(id={self.wallet_id}, user_id={self.user_id}, balance={self.balance})>"


class DBTransaction(Base):
    """Таблица транзакций (движение средств)."""
    __tablename__ = "transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.wallet_id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    description = Column(String(255), default="")
    timestamp = Column(DateTime, default=datetime.now)
    balance_after = Column(Float, nullable=False)
    related_prediction_id = Column(UUID(as_uuid=True), nullable=True)

    # Связи
    wallet = relationship("DBWallet", back_populates="transactions")

    def __repr__(self):
        return f"<DBTransaction(id={self.transaction_id}, wallet_id={self.wallet_id}, amount={self.amount}, type={self.type.value})>"


class DBMLModel(Base):
    """Таблица ML моделей."""
    __tablename__ = "ml_models"

    model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    model_type = Column(Enum(ModelType), nullable=False)
    is_active = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.now)

    # Связи
    predictions = relationship("DBPredictionHistory", back_populates="model")

    def __repr__(self):
        return f"<DBMLModel(id={self.model_id}, name={self.name}, version={self.version})>"


class DBPredictionHistory(Base):
    """Таблица истории предсказаний."""
    __tablename__ = "predictions_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    model_id = Column(UUID(as_uuid=True), ForeignKey("ml_models.model_id", ondelete="SET NULL"), nullable=True)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    duration_ms = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    transaction_id = Column(UUID(as_uuid=True), nullable=True)

    # Связи
    user = relationship("DBUser", back_populates="predictions")
    model = relationship("DBMLModel", back_populates="predictions")

    def __repr__(self):
        return f"<DBPredictionHistory(id={self.history_id}, user_id={self.user_id}, model_id={self.model_id}, cost={self.cost})>"