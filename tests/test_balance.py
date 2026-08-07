import pytest
import requests
from .conftest import BASE_URL


class TestBalance:
    """Тесты баланса и пополнения."""

    def test_get_balance(self, authed_client: requests.Session):
        """Получение баланса авторизованным пользователем."""
        resp = authed_client.get(f"{BASE_URL}/users/me")
        assert resp.status_code == 200
        data = resp.json()
        assert "balance" in data
        assert isinstance(data["balance"], (int, float))

    def test_deposit(self, authed_client: requests.Session):
        """Успешное пополнение баланса."""
        resp = authed_client.post(f"{BASE_URL}/balance/deposit", json={"amount": 50.0})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["new_balance"] >= 50.0
        assert "transaction_id" in data

    def test_deposit_negative(self, authed_client: requests.Session):
        """Пополнение с отрицательной суммой — ошибка."""
        resp = authed_client.post(f"{BASE_URL}/balance/deposit", json={"amount": -10.0})
        assert resp.status_code in (400, 422)