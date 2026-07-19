"""
Объектная модель ML сервиса
Задание №1: Проектирование (баланс вынесен в отдельную сущность)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

# ========================================
# 1. ПЕРЕЧИСЛЕНИЯ
# ========================================


class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    ADMIN_DEPOSIT = "admin_deposit"


class ModelType(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


# ========================================
# 2. ИСКЛЮЧЕНИЯ
# ========================================


class InsufficientBalanceError(Exception):
    """Недостаточно средств на балансе."""

    pass


# ========================================
# 3. ТРАНЗАКЦИЯ
# ========================================


@dataclass
class Transaction:
    """Запись о движении средств."""

    transaction_id: UUID = field(default_factory=uuid4)
    wallet_id: UUID = None  # ← теперь ссылка на кошелёк
    amount: float = 0.0
    type: TransactionType = TransactionType.DEPOSIT
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    balance_after: float = 0.0
    related_prediction_id: Optional[UUID] = None


# ========================================
# 4. КОШЕЛЁК (НОВАЯ СУЩНОСТЬ!)
# ========================================


class Wallet:
    """
    Отвечает за баланс и транзакции пользователя.
    Вынесено из User (SRP - Single Responsibility Principle).
    """

    def __init__(self, user_id: UUID):
        self._wallet_id: UUID = uuid4()
        self._user_id: UUID = user_id
        self._balance: float = 0.0
        self._transactions: List[Transaction] = []
        self._created_at: datetime = datetime.now()

    @property
    def wallet_id(self) -> UUID:
        return self._wallet_id

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def balance(self) -> float:
        return self._balance

    def add_balance(self, amount: float, description: str = "Deposit") -> Transaction:
        """Пополнить баланс."""
        if amount <= 0:
            raise ValueError("Amount must be positive")

        self._balance += amount
        transaction = Transaction(
            wallet_id=self._wallet_id,
            amount=amount,
            type=TransactionType.DEPOSIT,
            description=description,
            balance_after=self._balance,
        )
        self._transactions.append(transaction)
        return transaction

    def deduct_balance(
        self, amount: float, description: str = "Withdrawal"
    ) -> Transaction:
        """Списать средства."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self._balance < amount:
            raise InsufficientBalanceError(f"Need {amount}, have {self._balance}")

        self._balance -= amount
        transaction = Transaction(
            wallet_id=self._wallet_id,
            amount=-amount,
            type=TransactionType.WITHDRAWAL,
            description=description,
            balance_after=self._balance,
        )
        self._transactions.append(transaction)
        return transaction

    def get_transactions(self) -> List[Transaction]:
        """Получить историю транзакций."""
        return self._transactions.copy()

    def __repr__(self) -> str:
        return f"Wallet(id={self.wallet_id}, balance={self.balance})"


# ========================================
# 5. ПОЛЬЗОВАТЕЛЬ (ТОЛЬКО ПРОФИЛЬ)
# ========================================


class User(ABC):
    """
    Базовый класс пользователя.
    Только профиль: имя, почта, роль.
    Баланс вынесен в отдельную сущность Wallet.
    """

    def __init__(self, username: str, email: str, role: UserRole):
        self.__user_id: UUID = uuid4()
        self.__username: str = username
        self.__email: str = email
        self.__role: UserRole = role
        self._wallet: Wallet = Wallet(
            self.__user_id
        )  # ← кошелёк создаётся вместе с пользователем
        self._created_at: datetime = datetime.now()

    # --- Геттеры ---
    @property
    def user_id(self) -> UUID:
        return self.__user_id

    @property
    def username(self) -> str:
        return self.__username

    @username.setter
    def username(self, new_name: str) -> None:
        if len(new_name) < 3:
            raise ValueError("Username must be at least 3 characters")
        self.__username = new_name

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, new_email: str) -> None:
        if "@" not in new_email:
            raise ValueError("Invalid email")
        self.__email = new_email

    @property
    def role(self) -> UserRole:
        return self.__role

    # --- Доступ к кошельку ---
    @property
    def wallet(self) -> Wallet:
        """Получить кошелёк пользователя."""
        return self._wallet

    @property
    def balance(self) -> float:
        """Удобный доступ к балансу (делегирование)."""
        return self._wallet.balance

    def add_balance(self, amount: float, description: str = "Deposit") -> Transaction:
        """Пополнить баланс (делегирование в Wallet)."""
        return self._wallet.add_balance(amount, description)

    def deduct_balance(
        self, amount: float, description: str = "Withdrawal"
    ) -> Transaction:
        """Списать средства (делегирование в Wallet)."""
        return self._wallet.deduct_balance(amount, description)

    def get_transactions(self) -> List[Transaction]:
        """Получить историю транзакций (делегирование)."""
        return self._wallet.get_transactions()

    # --- Абстрактный метод (полиморфизм) ---
    @abstractmethod
    def get_permissions(self) -> List[str]:
        pass

    def __repr__(self) -> str:
        return f"User(id={self.user_id}, name={self.username}, role={self.role.value}, balance={self.balance})"


# ========================================
# 6. НАСЛЕДНИКИ ПОЛЬЗОВАТЕЛЯ
# ========================================


class AdminUser(User):
    def get_permissions(self) -> List[str]:
        return ["manage_users", "manage_balances"]


class RegularUser(User):
    def get_permissions(self) -> List[str]:
        return ["run_predictions"]


# ========================================
# 7. ML МОДЕЛЬ
# ========================================


class MLModel(ABC):
    def __init__(self, name: str, version: str, model_type: ModelType):
        self._model_id: UUID = uuid4()
        self._name: str = name
        self._version: str = version
        self._model_type: ModelType = model_type
        self._is_active: bool = False

    @property
    def model_id(self) -> UUID:
        return self._model_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def is_active(self) -> bool:
        return self._is_active

    def activate(self) -> None:
        self._is_active = True

    def deactivate(self) -> None:
        self._is_active = False

    @abstractmethod
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass


class ClassificationModel(MLModel):
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"class": "spam", "confidence": 0.95}


# ========================================
# 8. РЕЕСТР МОДЕЛЕЙ
# ========================================


class ModelRegistry:
    def __init__(self):
        self.__models: Dict[UUID, MLModel] = {}

    def register(self, model: MLModel) -> None:
        self.__models[model.model_id] = model

    def get(self, model_id: UUID) -> Optional[MLModel]:
        return self.__models.get(model_id)


# ========================================
# 9. ГЛАВНЫЙ СЕРВИС
# ========================================


class MLService:
    def __init__(self):
        self._registry = ModelRegistry()
        self._users: Dict[UUID, User] = {}
        self._history: List[Dict] = []

    def register_user(self, user: User) -> None:
        self._users[user.user_id] = user

    def get_user(self, user_id: UUID) -> Optional[User]:
        return self._users.get(user_id)

    def add_model(self, model: MLModel) -> None:
        self._registry.register(model)

    def predict(
        self, user_id: UUID, model_id: UUID, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        user = self.get_user(user_id)
        if not user:
            raise PermissionError("User not found")

        if "run_predictions" not in user.get_permissions():
            raise PermissionError("Permission denied")

        model = self._registry.get(model_id)
        if not model or not model.is_active:
            raise ValueError("Model not found or inactive")

        # Проверка баланса через кошелёк
        cost = 1.0
        if user.balance < cost:
            raise InsufficientBalanceError(f"Need {cost}, have {user.balance}")

        result = model.predict(data)

        # Списание через кошелёк
        user.deduct_balance(cost, f"Prediction: {model.name}")

        self._history.append(
            {
                "user_id": user_id,
                "model_id": model_id,
                "input": data,
                "output": result,
                "cost": cost,
                "timestamp": datetime.now(),
            }
        )

        return {**result, "credits_used": cost, "credits_remaining": user.balance}

    def admin_add_balance(
        self, admin_id: UUID, user_id: UUID, amount: float
    ) -> Transaction:
        admin = self.get_user(admin_id)
        if not admin or "manage_balances" not in admin.get_permissions():
            raise PermissionError("Admin only")

        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        return user.add_balance(amount, f"Admin deposit")


# ========================================
# 10. ПРИМЕР ИСПОЛЬЗОВАНИЯ
# ========================================

if __name__ == "__main__":
    service = MLService()

    # Создаём пользователей
    admin = AdminUser("admin", "admin@mail.com", UserRole.ADMIN)
    user = RegularUser("alex", "alex@mail.com", UserRole.USER)

    service.register_user(admin)
    service.register_user(user)

    print(f"Пользователь: {user.username}")
    print(f"Баланс: {user.balance}")
    print(f"Кошелёк: {user.wallet}")
    print()

    # Админ пополняет баланс
    service.admin_add_balance(admin.user_id, user.user_id, 100)
    print(f"Баланс после пополнения: {user.balance}")

    # Создаём модель
    model = ClassificationModel("Spam Detector", "v1.0", ModelType.CLASSIFICATION)
    service.add_model(model)
    model.activate()

    # Пользователь делает предсказание
    result = service.predict(user.user_id, model.model_id, {"text": "Hello"})
    print(f"Результат: {result}")
    print(f"Баланс после: {user.balance}")

    # История транзакций
    print("\nИстория транзакций (из кошелька):")
    for tx in user.wallet.get_transactions():
        print(f"  {tx.description}: {tx.amount} кредитов (баланс: {tx.balance_after})")
