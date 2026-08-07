import pytest
import requests
from .conftest import BASE_URL


class TestRegistration:
    """Тесты регистрации."""

    def test_register_success(self, api_client: requests.Session, unique_user_data: dict):
        """Успешная регистрация нового пользователя."""
        resp = api_client.post(f"{BASE_URL}/auth/register", json=unique_user_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == unique_user_data["username"]
        assert data["email"] == unique_user_data["email"]
        assert "user_id" in data

    def test_register_duplicate(self, api_client: requests.Session, registered_user: dict):
        """Повторная регистрация с теми же данными — ошибка."""
        payload = {
            "username": registered_user["username"],
            "email": registered_user["email"],
            "password": registered_user["password"]
        }
        resp = api_client.post(f"{BASE_URL}/auth/register", json=payload)
        assert resp.status_code == 400
        assert "already exists" in resp.text or "already registered" in resp.text


class TestLogin:
    """Тесты авторизации."""

    def test_login_success(self, api_client: requests.Session, registered_user: dict):
        """Успешный вход с правильными данными."""
        resp = api_client.post(
            f"{BASE_URL}/auth/login",
            json={
                "username": registered_user["username"],
                "password": registered_user["password"]
            }
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, api_client: requests.Session, registered_user: dict):
        """Неверный пароль — ошибка 401."""
        resp = api_client.post(
            f"{BASE_URL}/auth/login",
            json={
                "username": registered_user["username"],
                "password": "wrong_password"
            }
        )
        assert resp.status_code == 401
        assert "Invalid username or password" in resp.text

    def test_login_nonexistent_user(self, api_client: requests.Session):
        """Несуществующий пользователь — ошибка 401."""
        resp = api_client.post(
            f"{BASE_URL}/auth/login",
            json={
                "username": "nonexistent_user",
                "password": "any"
            }
        )
        assert resp.status_code == 401