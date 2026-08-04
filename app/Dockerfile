FROM python:3.12-slim

RUN pip install poetry==1.8.0

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY src/ ./src/
COPY ml_models/ ./ml_models/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]