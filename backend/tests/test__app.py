"""Тестирование основного приложения"""
import pytest
from fastapi.testclient import TestClient
from src.core import BitrixClient


class TestApp:
    """Тесты работоспособности приложения"""

    @pytest.mark.asyncio
    async def test_ping(self, test_client: TestClient):
        response = test_client.get('/ping')
        assert response.status_code == 200, "YOU ARE NOT PREPARED!"
        msg = response.json()
        assert msg == 'pong', 'Pong message da best!!!'

    @pytest.mark.asyncio
    async def test_bizproc(self):
        result = await BitrixClient.init_bizporc(1025)
