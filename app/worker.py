# app/worker.py
import pika
import json
import os
import time
import sys
from uuid import UUID
from datetime import datetime

# Настройки RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
QUEUE_NAME = "ml_tasks"

# Настройки базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@database:5432/ml_service")

# Добавляем путь к проекту, чтобы импортировать наши модули
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.orm_models import TaskStatus
from src.repositories import TaskRepository, HistoryRepository

# Создаём движок БД
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def process_task(ch, method, properties, body):
    """Обработка полученного сообщения."""
    db = None
    try:
        print(f"📩 Получено сообщение: {body}")  # ← ОТЛАДОЧНЫЙ ВЫВОД

        # 1. Парсим JSON
        data = json.loads(body)
        task_id = data.get("task_id")
        user_id = data.get("user_id")
        model_id = data.get("model_id")
        features = data.get("features", {})

        if not task_id or not user_id or not model_id:
            raise ValueError("Missing required fields in message")

        print(f"🔄 Обработка задачи {task_id} для пользователя {user_id}")

        # 2. Отмечаем задачу как PROCESSING
        db = SessionLocal()
        task_repo = TaskRepository(db)
        task_repo.update_task_status(UUID(task_id), TaskStatus.PROCESSING)

        # 3. Выполняем ML‑предсказание (заглушка)
        # В реальности здесь вызывается ML модель
        print("🧠 Выполнение ML-предсказания...")
        time.sleep(2)  # Имитация долгой работы
        result = {"class": "spam", "confidence": 0.95}

        # 4. Сохраняем результат в БД
        task_repo.update_task_status(UUID(task_id), TaskStatus.COMPLETED, output_data=result)

        # Сохраняем в историю предсказаний
        history_repo = HistoryRepository(db)
        history_repo.create_prediction_history(
            user_id=UUID(user_id),
            model_id=UUID(model_id),
            input_data=features,
            output_data=result,
            cost=1.0,
            duration_ms=0.0,
            transaction_id=None
        )

        db.commit()
        db.close()
        print(f"✅ Задача {task_id} успешно обработана")

        # 5. Подтверждаем успешную обработку
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"❌ Ошибка обработки задачи: {e}")
        # В случае ошибки: обновляем статус задачи на FAILED
        try:
            if db is None:
                db = SessionLocal()
            task_repo = TaskRepository(db)
            task_repo.update_task_status(UUID(task_id), TaskStatus.FAILED, error=str(e))
            db.commit()
        except Exception as inner_e:
            print(f"⚠️ Ошибка при обновлении статуса задачи: {inner_e}")
        finally:
            if db:
                db.close()
        # Всё равно подтверждаем, чтобы не зацикливаться
        ch.basic_ack(delivery_tag=method.delivery_tag)


def connect_with_retry():
    """Подключение к RabbitMQ с повторными попытками."""
    max_retries = 10
    retry_delay = 3
    for attempt in range(1, max_retries + 1):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)
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
    print(f" [*] Worker started. Waiting for messages in '{QUEUE_NAME}'. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Worker stopped.")


if __name__ == "__main__":
    main()