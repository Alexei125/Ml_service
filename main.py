"""
Объектная модель ML сервиса
Задание №1: Проектирование
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


# ========== 1. ПЕРЕЧИСЛЕНИЯ ==========

class UserRole(Enum):
    """Роли пользователей."""
    ADMIN = "admin"
    ANALYST = "analyst"
    USER = "user"


class TaskStatus(Enum):
    """Статусы задач."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ModelType(Enum):
    """Типы ML моделей."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


# ========== 2. ПОЛЬЗОВАТЕЛЬ ==========

class User(ABC):
    """
    Базовый класс пользователя.
    Инкапсуляция: приватные поля __user_id, __username, __email, __role.
    """

    def __init__(self, username: str, email: str, role: UserRole):
        self.__user_id: UUID = uuid4()
        self.__username: str = username
        self.__email: str = email
        self.__role: UserRole = role
        self._created_at: datetime = datetime.now()

    @property
    def user_id(self) -> UUID:
        """Геттер для user_id (только чтение)."""
        return self.__user_id

    @property
    def username(self) -> str:
        """Геттер для username."""
        return self.__username

    @username.setter
    def username(self, new_name: str) -> None:
        """Сеттер для username с валидацией."""
        if len(new_name) < 3:
            raise ValueError("Username must be at least 3 characters")
        self.__username = new_name

    @property
    def email(self) -> str:
        """Геттер для email."""
        return self.__email

    @email.setter
    def email(self, new_email: str) -> None:
        """Сеттер для email с валидацией."""
        if "@" not in new_email:
            raise ValueError("Invalid email")
        self.__email = new_email

    @property
    def role(self) -> UserRole:
        """Геттер для role (только чтение)."""
        return self.__role

    @abstractmethod
    def get_permissions(self) -> List[str]:
        """Каждый наследник определяет свои права."""
        pass


# ========== 3. НАСЛЕДНИКИ ПОЛЬЗОВАТЕЛЯ ==========

class AdminUser(User):
    """Администратор системы."""

    def get_permissions(self) -> List[str]:
        return ["manage_users", "view_all_logs", "manage_models"]


class RegularUser(User):
    """Обычный пользователь."""

    def get_permissions(self) -> List[str]:
        return ["run_predictions", "view_own_history"]


# ========== 4. ML МОДЕЛЬ ==========

class MLModel(ABC):
    """Базовый класс ML модели."""

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
        """Активировать модель."""
        self._is_active = True

    def deactivate(self) -> None:
        """Деактивировать модель."""
        self._is_active = False

    @abstractmethod
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить предсказание."""
        pass


# ========== 5. КОНКРЕТНЫЕ ML МОДЕЛИ ==========

class ClassificationModel(MLModel):
    """Модель для классификации."""

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Симулирует предсказание для классификации."""
        # В реальности здесь был бы вызов библиотеки
        return {"class": "spam", "confidence": 0.95}


class RegressionModel(MLModel):
    """Модель для регрессии."""

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Симулирует предсказание для регрессии."""
        return {"value": 42.5}


# ========== 6. ЗАДАЧА ==========

@dataclass
class Task:
    """Задача на выполнение предсказания."""
    task_id: UUID = uuid4()
    model_id: UUID = None
    input_data: Dict[str, Any] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = datetime.now()
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# ========== 7. ИСТОРИЯ ПРЕДСКАЗАНИЙ ==========

@dataclass
class PredictionHistory:
    """История транзакций/предсказаний."""
    history_id: UUID = uuid4()
    user_id: UUID = None
    model_id: UUID = None
    input_data: Dict[str, Any] = None
    output_data: Dict[str, Any] = None
    timestamp: datetime = datetime.now()
    duration_ms: float = 0.0


# ========== 8. РЕЕСТР МОДЕЛЕЙ ==========

class ModelRegistry:
    """Реестр для хранения моделей (инкапсуляция)."""

    def __init__(self):
        self.__models: Dict[UUID, MLModel] = {}

    def register_model(self, model: MLModel) -> None:
        """Зарегистрировать модель."""
        self.__models[model.model_id] = model

    def get_model(self, model_id: UUID) -> Optional[MLModel]:
        """Получить модель по ID."""
        return self.__models.get(model_id)

    def get_active_model(self) -> Optional[MLModel]:
        """Получить первую активную модель."""
        for model in self.__models.values():
            if model.is_active:
                return model
        return None

    def list_models(self) -> List[MLModel]:
        """Получить список всех моделей."""
        return list(self.__models.values())


# ========== 9. ГЛАВНЫЙ СЕРВИС ==========

class MLService:
    """Главный сервис, объединяющий все компоненты."""

    def __init__(self):
        self._registry = ModelRegistry()
        self._task_queue: List[Task] = []
        self._history: List[PredictionHistory] = []
        self._users: Dict[UUID, User] = {}

    # === Управление пользователями ===
    def register_user(self, user: User) -> None:
        """Зарегистрировать пользователя."""
        self._users[user.user_id] = user

    def get_user(self, user_id: UUID) -> Optional[User]:
        """Получить пользователя по ID."""
        return self._users.get(user_id)

    # === Управление моделями ===
    def add_model(self, model: MLModel) -> None:
        """Добавить модель."""
        self._registry.register_model(model)

    def get_model(self, model_id: UUID) -> Optional[MLModel]:
        """Получить модель по ID."""
        return self._registry.get_model(model_id)

    # === Синхронное предсказание ===
    def predict_sync(self, user_id: UUID, model_id: UUID, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Синхронное предсказание.
        Проверяет пользователя, его права, активность модели.
        """
        # 1. Проверяем пользователя
        user = self.get_user(user_id)
        if not user:
            raise PermissionError("User not found")

        # 2. Проверяем права (полиморфизм)
        if "run_predictions" not in user.get_permissions():
            raise PermissionError("Permission denied")

        # 3. Проверяем модель
        model = self._registry.get_model(model_id)
        if not model or not model.is_active:
            raise ValueError("Model not found or inactive")

        # 4. Выполняем предсказание (полиморфизм)
        start = datetime.now()
        result = model.predict(input_data)
        duration = (datetime.now() - start).total_seconds() * 1000

        # 5. Сохраняем историю
        history = PredictionHistory(
            user_id=user_id,
            model_id=model_id,
            input_data=input_data,
            output_data=result,
            duration_ms=duration
        )
        self._history.append(history)

        return result

    # === Асинхронное предсказание ===
    def create_task(self, user_id: UUID, model_id: UUID, input_data: Dict[str, Any]) -> Task:
        """Создать задачу для асинхронного выполнения."""
        user = self.get_user(user_id)
        if not user or "run_predictions" not in user.get_permissions():
            raise PermissionError("Permission denied")

        task = Task(model_id=model_id, input_data=input_data)
        self._task_queue.append(task)
        return task

    def get_task_status(self, task_id: UUID) -> Optional[Task]:
        """Получить статус задачи."""
        for task in self._task_queue:
            if task.task_id == task_id:
                return task
        return None

    # === История ===
    def get_user_history(self, user_id: UUID) -> List[PredictionHistory]:
        """Получить историю конкретного пользователя."""
        return [h for h in self._history if h.user_id == user_id]

    def get_all_history(self, admin_id: UUID) -> List[PredictionHistory]:
        """Получить всю историю (только для админа)."""
        admin = self.get_user(admin_id)
        if not admin or "view_all_logs" not in admin.get_permissions():
            raise PermissionError("Only admin can view all history")
        return self._history


# ========== 10. ПРИМЕР ИСПОЛЬЗОВАНИЯ ==========

if __name__ == "__main__":
    # Создаем сервис
    service = MLService()

    # Создаем пользователей
    admin = AdminUser("admin", "admin@ml.com", UserRole.ADMIN)
    user = RegularUser("alex", "alex@mail.com", UserRole.USER)

    service.register_user(admin)
    service.register_user(user)

    print("=== ПОЛЬЗОВАТЕЛИ ===")
    print(f"Admin: {admin.username}, rights: {admin.get_permissions()}")
    print(f"User: {user.username}, rights: {user.get_permissions()}")
    print()

    # Создаем и регистрируем модель
    model = ClassificationModel("Spam Detector", "v1.0", ModelType.CLASSIFICATION)
    service.add_model(model)
    model.activate()  # Активируем модель

    print("=== МОДЕЛЬ ===")
    print(f"Model: {model.name} v{model.version}, Active: {model.is_active}")
    print()

    # Выполняем синхронное предсказание
    print("=== СИНХРОННОЕ ПРЕДСКАЗАНИЕ ===")
    result = service.predict_sync(user.user_id, model.model_id, {"text": "You won a lottery!"})
    print(f"Result: {result}")
    print()

    # Создаем асинхронную задачу
    print("=== АСИНХРОННАЯ ЗАДАЧА ===")
    task = service.create_task(user.user_id, model.model_id, {"text": "Hello world"})
    print(f"Task created with ID: {task.task_id}")
    print(f"Task status: {task.status.value}")
    print()

    # Проверяем историю пользователя
    print("=== ИСТОРИЯ ПОЛЬЗОВАТЕЛЯ ===")
    history = service.get_user_history(user.user_id)
    for h in history:
        print(f"Input: {h.input_data}, Output: {h.output_data}, Duration: {h.duration_ms:.2f}ms")
