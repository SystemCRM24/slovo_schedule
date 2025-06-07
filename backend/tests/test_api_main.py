import pytest
from httpx import Response


@pytest.fixture(scope='class')
def specialists_response(test_client) -> Response:
    return test_client.get('/front/get_specialist')


@pytest.fixture(scope='class')
def specialists_json(specialists_response) -> dict:
    return specialists_response.json()


class TestGetSpecialists:

    def test_one(self, specialists_response):
        assert specialists_response.status_code == 200
    
    def test_two(self, specialists_json):
        data: list[dict] = specialists_json
        assert isinstance(data, list)
        for item in data:
            assert isinstance(item, dict)
            assert isinstance(item['id'], int)
            assert isinstance(item['name'], str)
            assert isinstance(item['departments'], list)
            assert len(item['departments']) > 0


@pytest.fixture(scope='class')
def clients_response(test_client) -> Response:
    return test_client.get('/front/get_clients')


@pytest.fixture(scope='class')
def clients_json(clients_response) -> dict:
    return clients_response.json()


class TestGetClients:

    def test_one(self, clients_response):
        assert clients_response.status_code == 200
    
    def test_two(self, clients_json):
        data: list[dict] = clients_json
        assert isinstance(data, list)
        for item in data:
            assert isinstance(item, dict)
            assert isinstance(item['id'], int)
            assert isinstance(item['full_name'], str)
