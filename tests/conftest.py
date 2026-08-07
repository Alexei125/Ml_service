import pytest
import requests
from uuid import uuid4
from typing import Dict, Any, Generator

BASE_URL = "http://localhost"


@pytest.fixture(scope="session")
def api_client() -> Generator[requests.Session, None, None]:
    """
    Сессионная фикстура: HTTP-клиент для всех тестов.
    Проверяет доступность сервиса перед запуском.
    """
    session = requests.Session()
    try:
        resp = session.get(f"{BASE_URL}/")
        assert resp.status_code == 200, "Сервис недоступен"
    except requests.ConnectionError:
        pytest.fail("Не удалось подключиться к серверу. Убедитесь, что docker-compose запущен.")
    yield session


@pytest.fixture
def unique_user_data() -> Dict[str, str]:
    """
    Генерирует уникальные данные для тестового пользователя.
    """
    uid = str(uuid4())[:8]
    return {
        "username": f"testuser_{uid}",
        "email": f"test_{uid}@mail.com",
        "password": "TestPassword123!"
    }


@pytest.fixture
def registered_user(api_client: requests.Session, unique_user_data: Dict[str, str]) -> Dict[str, Any]:
    """
    Регистрирует пользователя и возвращает его данные.
    """
    resp = api_client.post(f"{BASE_URL}/auth/register", json=unique_user_data)
    assert resp.status_code == 200, f"Регистрация не удалась: {resp.text}"
    data = resp.json()
    return {
        **unique_user_data,
        "user_id": data["user_id"],
        "balance": data.get("balance", 0.0)
    }


@pytest.fixture
def auth_token(api_client: requests.Session, registered_user: Dict[str, str]) -> str:
    """
    Выполняет вход и возвращает JWT-токен.
    """
    resp = api_client.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": registered_user["username"],
            "password": registered_user["password"]
        }
    )
    assert resp.status_code == 200, f"Вход не удался: {resp.text}"
    token = resp.json().get("access_token")
    assert token, "Токен не получен"
    return token


@pytest.fixture
def authed_client(api_client: requests.Session, auth_token: str) -> requests.Session:
    """
    Возвращает HTTP-клиент с авторизацией (Bearer token).
    """
    api_client.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return api_client