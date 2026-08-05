FROM python:3.12-slim

RUN pip install pika sqlalchemy psycopg2-binary scikit-learn joblib

WORKDIR /worker

COPY worker.py .

CMD ["python", "worker.py"]
