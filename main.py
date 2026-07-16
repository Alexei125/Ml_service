"""
Объектная модель ML сервиса
Задание №1: Проектирование (минимальная версия)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


# ========================================
# 1. ПЕРЕЧИСЛЕНИЯ (константы)
# ========================================

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class ModelType(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


# ========================================
# 2. ИСКЛЮЧЕНИЯ (ошибки)
# ========================================

class InsufficientBalanceError(Exception):
    """Недостаточно средств"""
    pass


# ========================================
# 3. ТРАНЗАКЦИЯ (движение денег)
# ========================================

@dataclass
class Transaction:
    transaction_id: UUID = uuid4()
    user_id: UUID = None
    amount: float = 0.0
    type: TransactionType = TransactionType.DEPOSIT
    description: str = ""
    timestamp: datetime = datetime.now()
    balance_after: float = 0.0


# ========================================
# 4. ПОЛЬЗОВАТЕЛЬ (главный класс)
# ========================================

class User(ABC):
    def __init__(self, username: str, email: str, role: UserRole):
        self.__user_id: UUID = uuid4()           # приватное поле
        self.__username: str = username
        self.__email: str = email
        self.__role: UserRole = role
        self.__balance: float = 0.0              # баланс
        self.__transactions: List[Transaction] = []  # история

    # === ГЕТТЕРЫ (для чтения) ===
    @property
    def user_id(self) -> UUID:
        return self.__user_id

    @property
    def username(self) -> str:
        return self.__username

    @property
    def email(self) -> str:
        return self.__email

    @property
    def role(self) -> UserRole:
        return self.__role

    @property
    def balance(self) -> float:
        return self.__balance

    # === МЕТОДЫ БАЛАНСА ===
    def add_balance(self, amount: float, description: str = "Deposit") -> Transaction:
        """Пополнить баланс"""
        if amount <= 0:
            raise ValueError("Amount must be positive")

        self.__balance += amount
        transaction = Transaction(
            user_id=self.user_id,
            amount=amount,
            type=TransactionType.DEPOSIT,
            description=description,
            balance_after=self.__balance
        )
        self.__transactions.append(transaction)
        return transaction

    def deduct_balance(self, amount: float, description: str = "Withdrawal") -> Transaction:
        """Списать с баланса"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.__balance < amount:
            raise InsufficientBalanceError(
                f"Need {amount}, have {self.__balance}"
            )

        self.__balance -= amount
        transaction = Transaction(
            user_id=self.user_id,
            amount=-amount,
            type=TransactionType.WITHDRAWAL,
            description=description,
            balance_after=self.__balance
        )
        self.__transactions.append(transaction)
        return transaction

    def get_transactions(self) -> List[Transaction]:
        return self.__transactions.copy()

    # === АБСТРАКТНЫЙ МЕТОД (полиморфизм) ===
    @abstractmethod
    def get_permissions(self) -> List[str]:
        pass


# ========================================
# 5. НАСЛЕДНИКИ ПОЛЬЗОВАТЕЛЯ
# ========================================

class AdminUser(User):
    def get_permissions(self) -> List[str]:
        return ["manage_users", "manage_balances"]


class RegularUser(User):
    def get_permissions(self) -> List[str]:
        return ["run_predictions"]


# ========================================
# 6. ML МОДЕЛЬ
# ========================================

class MLModel(ABC):
    def __init__(self, name: str, version: str, model_type: ModelType):
        self._model_id: UUID = uuid4()
        self._name: str = name
        self._version: str = version
        self._is_active: bool = False

    @property
    def model_id(self) -> UUID:
        return self._model_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_active(self) -> bool:
        return self._is_active

    def activate(self) -> None:
        self._is_active = True

    @abstractmethod
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass


class ClassificationModel(MLModel):
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"class": "spam", "confidence": 0.95}


# ========================================
# 7. РЕЕСТР МОДЕЛЕЙ
# ========================================

class ModelRegistry:
    def __init__(self):
        self.__models: Dict[UUID, MLModel] = {}

    def register(self, model: MLModel) -> None:
        self.__models[model.model_id] = model

    def get(self, model_id: UUID) -> Optional[MLModel]:
        return self.__models.get(model_id)


# ========================================
# 8. ГЛАВНЫЙ СЕРВИС
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

    def predict(self, user_id: UUID, model_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Проверяем пользователя
        user = self.get_user(user_id)
        if not user:
            raise PermissionError("User not found")

        # 2. Проверяем права
        if "run_predictions" not in user.get_permissions():
            raise PermissionError("Permission denied")

        # 3. Проверяем модель
        model = self._registry.get(model_id)
        if not model or not model.is_active:
            raise ValueError("Model not found or inactive")

        # 4. Проверяем баланс (стоимость = 1 кредит)
        cost = 1.0
        if user.balance < cost:
            raise InsufficientBalanceError(f"Need {cost}, have {user.balance}")

        # 5. Делаем предсказание
        result = model.predict(data)

        # 6. Списываем кредиты
        user.deduct_balance(cost, f"Prediction: {model.name}")

        # 7. Сохраняем историю
        self._history.append({
            "user_id": user_id,
            "model_id": model_id,
            "input": data,
            "output": result,
            "cost": cost,
            "timestamp": datetime.now()
        })

        return {
            **result,
            "credits_used": cost,
            "credits_remaining": user.balance
        }

    def admin_add_balance(self, admin_id: UUID, user_id: UUID, amount: float) -> Transaction:
        admin = self.get_user(admin_id)
        if not admin or "manage_balances" not in admin.get_permissions():
            raise PermissionError("Admin only")

        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        return user.add_balance(amount, f"Admin deposit")


# ========================================
# 9. ПРИМЕР ИСПОЛЬЗОВАНИЯ
# ========================================

if __name__ == "__main__":
    service = MLService()

    # Создаём админа и пользователя
    admin = AdminUser("admin", "admin@mail.com", UserRole.ADMIN)
    user = RegularUser("alex", "alex@mail.com", UserRole.USER)

    service.register_user(admin)
    service.register_user(user)

    # Админ пополняет баланс
    service.admin_add_balance(admin.user_id, user.user_id, 100)
    print(f"Баланс Алекса: {user.balance}")  # 100.0

    # Создаём модель
    model = ClassificationModel("Spam Detector", "v1.0", ModelType.CLASSIFICATION)
    service.add_model(model)
    model.activate()

    # Алекc делает предсказание
    result = service.predict(user.user_id, model.model_id, {"text": "Hello"})
    print(f"Результат: {result}")
    print(f"Баланс после: {user.balance}")  # 99.0

    # История транзакций
    print("\nИстория:")
    for tx in user.get_transactions():
        print(f"{tx.description}: {tx.amount} кредитов")