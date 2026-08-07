import pytest
import requests
from .conftest import BASE_URL


class TestHistory:
    """Тесты истории операций."""

    def test_transactions_history(self, authed_client: requests.Session):
        """Получение истории транзакций."""
        resp = authed_client.get(f"{BASE_URL}/balance/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        if data:
            tx = data[0]
            assert "amount" in tx
            assert "type" in tx
            assert "description" in tx
            assert "balance_after" in tx

    def test_predictions_history(self, authed_client: requests.Session):
        """Получение истории предсказаний."""
        resp = authed_client.get(f"{BASE_URL}/history/predictions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        if data:
            pred = data[0]
            assert "id" in pred
            assert "input" in pred
            assert "output" in pred
            assert "cost" in pred