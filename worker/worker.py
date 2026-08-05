import pika
import json
import os
import time
import sys
from uuid import UUID
from datetime import datetime

sys.path.append("/app")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.orm_models import TaskStatus
from src.repositories import TaskRepository, HistoryRepository
from src.ml_model import load_model, predict

# Настройки RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
QUEUE_NAME = "ml_tasks"

# Настройки БД (используем те же)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@database:5432/ml_service"
)

# Загружаем ML-модель при старте воркера
try:
    load_model()
    print("✅ ML-модель загружена в воркере")
except Exception as e:
    print(f"⚠️ Ошибка загрузки модели: {e}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def process_task(ch, method, properties, body):
    db = None
    try:
        print(f"📩 Получено сообщение: {body}")
        data = json.loads(body)
        task_id = data.get("task_id")
        user_id = data.get("user_id")
        model_id = data.get("model_id")
        features = data.get("features", {})

        if not task_id or not user_id or not model_id:
            raise ValueError("Missing required fields")

        db = SessionLocal()
        task_repo = TaskRepository(db)
        task_repo.update_task_status(UUID(task_id), TaskStatus.PROCESSING)

        # Выполняем реальное ML-предсказание
        text = features.get("text", "")
        if not text:
            raise ValueError("No text provided for prediction")

        result = predict(text)  # ← реальная модель
        time.sleep(1)  # имитация задержки (можно убрать)

        # Обновляем задачу
        task_repo.update_task_status(
            UUID(task_id), TaskStatus.COMPLETED, output_data=result
        )

        # Сохраняем в историю
        history_repo = HistoryRepository(db)
        history_repo.create_prediction_history(
            user_id=UUID(user_id),
            model_id=UUID(model_id),
            input_data=features,
            output_data=result,
            cost=1.0,
        )

        db.commit()
        db.close()
        print(f"✅ Задача {task_id} обработана")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        try:
            if db is None:
                db = SessionLocal()
            task_repo = TaskRepository(db)
            task_repo.update_task_status(UUID(task_id), TaskStatus.FAILED, error=str(e))
            db.commit()
        except Exception as inner_e:
            print(f"⚠️ Ошибка обновления статуса: {inner_e}")
        finally:
            if db:
                db.close()
        ch.basic_ack(delivery_tag=method.delivery_tag)


def connect_with_retry():
    max_retries = 10
    retry_delay = 3
    for attempt in range(1, max_retries + 1):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials
                )
            )
            print(f"✅ Connected to RabbitMQ (attempt {attempt})")
            return connection
        except Exception as e:
            print(f"⚠️ Connection attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                raise


def main():
    connection = connect_with_retry()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_task)
    print(f" [*] Worker started. Waiting for messages in '{QUEUE_NAME}'.")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Worker stopped.")


if __name__ == "__main__":
    main()
