# app/src/routers/predict.py
"""
Роутер для ML-предсказаний (асинхронный через RabbitMQ)
"""

import pika
import json
import os
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories import ModelRepository, TaskRepository, HistoryRepository
from ..schemas import PredictRequest
from ..auth import get_current_user
from ..orm_models import DBUser, TaskStatus

router = APIRouter(prefix="/predict", tags=["predict"])

# ============================================================
# НАСТРОЙКИ RABBITMQ
# ============================================================
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
QUEUE_NAME = "ml_tasks"


# ============================================================
# ФУНКЦИЯ ПУБЛИКАЦИИ СООБЩЕНИЯ В ОЧЕРЕДЬ
# ============================================================
def publish_task(task_data: dict):
    """Отправить задачу в очередь RabbitMQ."""
    print(f"🔍 QUEUE_NAME = '  {QUEUE_NAME}  '")
    print(f"🔍 Routing key = '  {QUEUE_NAME}  '")
    print(f"🔍 Task data:  {task_data}  ")
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=QUEUE_NAME,
        body=json.dumps(task_data),
        properties=pika.BasicProperties(
            delivery_mode=2,  # persistent
        )
    )
    connection.close()
    print("✅ Сообщение отправлено в очередь")


# ============================================================
# ЭНДПОИНТ: СОЗДАНИЕ ЗАДАЧИ
# ============================================================
@router.post("/", response_model=dict)
def create_prediction_task(
    request: PredictRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать задачу на предсказание (асинхронно)."""
    print("🔵 [1] Начало обработки запроса")

    # 1. Проверяем активную модель
    model_repo = ModelRepository(db)
    model = model_repo.get_active_model()
    if not model:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active model found")
    print(f"🟢 [2] Активная модель найдена: {model.name} (ID: {model.model_id})")

    # 2. Создаём задачу в БД со статусом PENDING
    task_repo = TaskRepository(db)
    task = task_repo.create_task(
        user_id=current_user.user_id,
        model_id=model.model_id,
        input_data=request.data
    )
    print(f"🟢 [3] Задача создана в БД: task_id={task.task_id}")

    # 3. Формируем сообщение для очереди
    message = {
        "task_id": str(task.task_id),
        "user_id": str(current_user.user_id),
        "model_id": str(model.model_id),
        "features": request.data,
        "timestamp": datetime.now().isoformat()
    }
    print(f"📦 [4] Сообщение сформировано: {message}")

    # 4. Отправляем в RabbitMQ
    try:
        print("📤 [5] Попытка отправки в RabbitMQ...")
        publish_task(message)
        print("✅ [6] Задача успешно опубликована в очередь")
    except Exception as e:
        print(f"❌ [6] Ошибка при отправке в RabbitMQ: {e}")
        task_repo.update_task_status(task.task_id, TaskStatus.FAILED, error=str(e))
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"RabbitMQ error: {e}")

    # 5. Возвращаем task_id
    return {"task_id": str(task.task_id), "status": task.status.value}


# ============================================================
# ЭНДПОИНТ: ПОЛУЧЕНИЕ СТАТУСА ЗАДАЧИ
# ============================================================
@router.get("/{task_id}")
def get_task_status(
    task_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статус задачи и результат (если готов)."""
    task_repo = TaskRepository(db)
    task = task_repo.get_task(UUID(task_id))
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    if task.user_id != current_user.user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your task")

    response = {
        "task_id": str(task.task_id),
        "status": task.status.value,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }
    if task.status == TaskStatus.COMPLETED:
        response["result"] = task.output_data
    if task.status == TaskStatus.FAILED:
        response["error"] = task.error_message
    return response