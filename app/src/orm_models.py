import uuid
from datetime import datetime
import enum

from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    ForeignKey,
    UUID,
    JSON,
    Boolean,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from src.database import Base  # ← вместо from .database import Base

# ... остальной код без изменений


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
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DBUser(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.now)

    wallet = relationship(
        "DBWallet", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    predictions = relationship(
        "DBPredictionHistory", back_populates="user", cascade="all, delete-orphan"
    )
    tasks = relationship("DBTask", back_populates="user", cascade="all, delete-orphan")


class DBWallet(Base):
    __tablename__ = "wallets"

    wallet_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    balance = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("DBUser", back_populates="wallet")
    transactions = relationship(
        "DBTransaction", back_populates="wallet", cascade="all, delete-orphan"
    )


class DBTransaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(
        UUID(as_uuid=True),
        ForeignKey("wallets.wallet_id", ondelete="CASCADE"),
        nullable=False,
    )
    amount = Column(Float, nullable=False)
    type = Column(SAEnum(TransactionType), nullable=False)
    description = Column(String(255), default="")
    timestamp = Column(DateTime, default=datetime.now)
    balance_after = Column(Float, nullable=False)
    related_prediction_id = Column(UUID(as_uuid=True), nullable=True)

    wallet = relationship("DBWallet", back_populates="transactions")


class DBMLModel(Base):
    __tablename__ = "ml_models"

    model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    model_type = Column(SAEnum(ModelType), nullable=False)
    is_active = Column(Boolean, default=False)
    extra_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.now)

    predictions = relationship("DBPredictionHistory", back_populates="model")
    tasks = relationship("DBTask", back_populates="model")


class DBPredictionHistory(Base):
    __tablename__ = "predictions_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.model_id", ondelete="SET NULL"),
        nullable=True,
    )
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    duration_ms = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    transaction_id = Column(UUID(as_uuid=True), nullable=True)

    user = relationship("DBUser", back_populates="predictions")
    model = relationship("DBMLModel", back_populates="predictions")


class DBTask(Base):
    __tablename__ = "tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ml_models.model_id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(SAEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    error_message = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("DBUser", back_populates="tasks")
    model = relationship("DBMLModel", back_populates="tasks")
