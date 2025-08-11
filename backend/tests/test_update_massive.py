import pytest
from src.core import BitrixClient
import json


class TestUpdate:
    """Тесты работоспособности приложения"""

    def test_one(self, test_client):
        data = {
            "specialist": 20,
            "patient": 276,
            "start": "2025-08-12T06:00:00.000Z",
            "end": "2025-08-12T07:00:00.000Z",
            "code": "LM",
            "status": "Бесконечное"
        }
        response = test_client.put(f'/front/appointment/massive/{1636}', content=json.dumps(data))
        assert response.status_code == 200
        json_data = response.json()
        print(json_data)