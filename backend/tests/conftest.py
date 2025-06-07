import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope='session')
def test_client():
    """Создает тестовый клиент"""
    with TestClient(app) as test_client:
        yield test_client
