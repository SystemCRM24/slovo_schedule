import pytest
from httpx import Response

from src.schemas.api import BXAppointment, BXSchedule


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


@pytest.fixture(scope='class')
def appointments_response(test_client) -> Response:
    url = f'/front/get_schedules?start=2025-05-01T10:00:00+03:00&end=2025-05-30T10:00:00+03:00'
    return test_client.get(url)


@pytest.fixture(scope='class')
def appointments_json(appointments_response) -> dict:
    return appointments_response.json()


class TestGetAppointments:

    def test_one(self, appointments_response):
        assert appointments_response.status_code == 200
    
    def test_two(self, appointments_json):
        data: list[dict] = appointments_json
        assert isinstance(data, list)
        for item in data:
            assert isinstance(item, dict)
            appointment = BXAppointment(**item)
            assert appointment.is_valid()


@pytest.fixture(scope='class')
def schedules_response(test_client) -> Response:
    url = f'/front/get_work_schedules?start=2025-05-01T10:00:00+03:00&end=2025-05-30T10:00:00+03:00'
    return test_client.get(url)


@pytest.fixture(scope='class')
def schedules_json(schedules_response) -> dict:
    return schedules_response.json()


class TestGetSchedules:

    def test_one(self, schedules_response):
        assert schedules_response.status_code == 200
    
    def test_two(self, schedules_json):
        data: list[dict] = schedules_json
        assert isinstance(data, list)
        for item in data:
            assert isinstance(item, dict)
            schedule = BXSchedule(**item)
            assert schedule.is_valid()
