# app/src/routers/predict.py
import pika
import json
import os
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories import ModelRepository, TaskRepository
from ..schemas import PredictRequest
from ..auth import get_current_user
from ..orm_models import DBUser, TaskStatus
from ..ml_model import predict as ml_predict, load_model

router = APIRouter(prefix="/predict", tags=["predict"])

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
QUEUE_NAME = "ml_tasks"

# Загружаем модель при старте
try:
    load_model()
    print("✅ ML-модель загружена")
except FileNotFoundError:
    print("⚠️ Модель не найдена. Запустите train_model.py")


def publish_task(task_data: dict):
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(task_data),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()


@router.post("/", response_model=dict)
def create_prediction_task(
    request: PredictRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Проверяем активную модель (в БД, но для async используем любую)
    model_repo = ModelRepository(db)
    model = model_repo.get_active_model()
    if not model:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active model found")

    # 2. Создаём задачу в БД
    task_repo = TaskRepository(db)
    task = task_repo.create_task(
        user_id=current_user.user_id, model_id=model.model_id, input_data=request.data
    )

    # 3. Формируем сообщение
    message = {
        "task_id": str(task.task_id),
        "user_id": str(current_user.user_id),
        "model_id": str(model.model_id),
        "features": request.data,
        "timestamp": datetime.now().isoformat(),
    }

    # 4. Отправляем в RabbitMQ
    try:
        publish_task(message)
    except Exception as e:
        task_repo.update_task_status(task.task_id, TaskStatus.FAILED, error=str(e))
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"RabbitMQ error: {e}")

    return {"task_id": str(task.task_id), "status": task.status.value}


@router.get("/{task_id}")
def get_task_status(
    task_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
