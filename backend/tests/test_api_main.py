import pytest
from httpx import Response


@pytest.fixture(scope='class')
def test_response(test_client) -> Response:
    return test_client.get('/front/get_specialist')


@pytest.fixture(scope='class')
def test_response_json(test_response) -> dict:
    return test_response.json()


class TestGetSpecialists:

    def test_one(self, test_response):
        assert test_response.status_code == 200
    
    def test_two(self, test_response_json):
        data: list[dict] = test_response_json
        assert isinstance(data, list)
        for item in data:
            assert isinstance(item, dict)
            assert isinstance(item['id'], int)
            assert isinstance(item['name'], str)
            assert isinstance(item['departments'], list)
            assert len(item['departments']) > 0