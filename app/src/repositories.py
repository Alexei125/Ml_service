"""
Репозитории для работы с базой данных
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from datetime import datetime
from typing import Optional, List

from .orm_models import (
    DBUser, DBWallet, DBTransaction, DBMLModel, DBPredictionHistory, DBTask,
    UserRole, TransactionType, TaskStatus
)


class InsufficientBalanceError(Exception):
    pass


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, username: str, email: str, role: UserRole, password_hash: str = None) -> DBUser:
        if password_hash is None:
            from .auth import get_password_hash
            password_hash = get_password_hash("default_password")

        db_user = DBUser(
            username=username,
            email=email,
            role=role.value,   # ← строка
            password_hash=password_hash
        )
        self.db.add(db_user)
        self.db.flush()

        db_wallet = DBWallet(user_id=db_user.user_id, balance=0.0)
        self.db.add(db_wallet)

        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_user_by_id(self, user_id: UUID) -> Optional[DBUser]:
        return self.db.query(DBUser).filter(DBUser.user_id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[DBUser]:
        return self.db.query(DBUser).filter(DBUser.username == username).first()

    def get_user_with_wallet(self, user_id: UUID) -> Optional[DBUser]:
        return self.db.query(DBUser).filter(DBUser.user_id == user_id).first()


class WalletRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_wallet(self, user_id: UUID) -> Optional[DBWallet]:
        return self.db.query(DBWallet).filter(DBWallet.user_id == user_id).first()

    def add_balance(self, user_id: UUID, amount: float, description: str = "Deposit") -> DBTransaction:
        wallet = self.get_wallet(user_id)
        if not wallet:
            raise ValueError(f"Wallet for user {user_id} not found")

        if amount <= 0:
            raise ValueError("Amount must be positive")

        wallet.balance += amount

        transaction = DBTransaction(
            wallet_id=wallet.wallet_id,
            amount=amount,
            type=TransactionType.DEPOSIT.value,
            description=description,
            balance_after=wallet.balance
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def deduct_balance(self, user_id: UUID, amount: float, description: str = "Withdrawal") -> DBTransaction:
        wallet = self.get_wallet(user_id)
        if not wallet:
            raise ValueError(f"Wallet for user {user_id} not found")

        if amount <= 0:
            raise ValueError("Amount must be positive")

        if wallet.balance < amount:
            raise InsufficientBalanceError(f"Need {amount}, have {wallet.balance}")

        wallet.balance -= amount

        transaction = DBTransaction(
            wallet_id=wallet.wallet_id,
            amount=-amount,
            type=TransactionType.WITHDRAWAL.value,
            description=description,
            balance_after=wallet.balance
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_transactions(self, user_id: UUID, limit: int = 100) -> List[DBTransaction]:
        wallet = self.get_wallet(user_id)
        if not wallet:
            return []

        return (self.db.query(DBTransaction)
                .filter(DBTransaction.wallet_id == wallet.wallet_id)
                .order_by(desc(DBTransaction.timestamp))
                .limit(limit)
                .all())


class ModelRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_model(self, name: str, version: str, model_type: str, is_active: bool = False) -> DBMLModel:
        db_model = DBMLModel(
            name=name,
            version=version,
            model_type=model_type,
            is_active=is_active
        )
        self.db.add(db_model)
        self.db.commit()
        self.db.refresh(db_model)
        return db_model

    def get_model_by_id(self, model_id: UUID) -> Optional[DBMLModel]:
        return self.db.query(DBMLModel).filter(DBMLModel.model_id == model_id).first()

    def get_active_model(self) -> Optional[DBMLModel]:
        return self.db.query(DBMLModel).filter(DBMLModel.is_active == True).first()

    def list_models(self) -> List[DBMLModel]:
        return self.db.query(DBMLModel).all()


class HistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_prediction_history(
        self,
        user_id: UUID,
        model_id: UUID,
        input_data: dict,
        output_data: dict,
        cost: float,
        duration_ms: float = 0.0,
        transaction_id: UUID = None
    ) -> DBPredictionHistory:
        history = DBPredictionHistory(
            user_id=user_id,
            model_id=model_id,
            input_data=input_data,
            output_data=output_data,
            cost=cost,
            duration_ms=duration_ms,
            transaction_id=transaction_id
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_user_history(self, user_id: UUID, limit: int = 100) -> List[DBPredictionHistory]:
        return (self.db.query(DBPredictionHistory)
                .filter(DBPredictionHistory.user_id == user_id)
                .order_by(desc(DBPredictionHistory.timestamp))
                .limit(limit)
                .all())


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, user_id: UUID, model_id: UUID, input_data: dict) -> DBTask:
        task = DBTask(
            user_id=user_id,
            model_id=model_id,
            input_data=input_data,
            status=TaskStatus.PENDING
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: UUID) -> Optional[DBTask]:
        return self.db.query(DBTask).filter(DBTask.task_id == task_id).first()

    def update_task_status(self, task_id: UUID, status: TaskStatus, output_data: dict = None, error: str = None) -> DBTask:
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        task.status = status
        if output_data is not None:
            task.output_data = output_data
        if error is not None:
            task.error_message = error
        task.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(task)
        return task