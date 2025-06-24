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


# ========== Тесты для /get_constants ==========

@pytest.fixture(scope='class')
def constants_response(test_client) -> Response:
    return test_client.get('/front/get_constants')


@pytest.fixture(scope='class')
def constants_json(constants_response) -> dict:
    return constants_response.json()


class TestGetConstants:

    def test_status_code(self, constants_response):
        assert constants_response.status_code == 200

    def test_return_type_is_dict(self, constants_json):
        assert isinstance(constants_json, dict)

    def test_expected_top_level_keys(self, constants_json):
        expected_keys = {'appointment', 'schedule', 'deal', 'departments', 'department_ids'}
        returned_keys = set(constants_json.keys())
        assert expected_keys.issubset(returned_keys), f"Missing keys: {expected_keys - returned_keys}"

    def test_appointment_structure(self, constants_json):
        appointment = constants_json['appointment']
        assert isinstance(appointment, dict)
        assert 'entityTypeId' in appointment
        assert isinstance(appointment['entityTypeId'], int)
        assert 'uf' in appointment
        assert isinstance(appointment['uf'], dict)
        assert 'specialist' in appointment['uf']
        assert isinstance(appointment['uf']['specialist'], str)

    def test_schedule_structure(self, constants_json):
        schedule = constants_json['schedule']
        assert isinstance(schedule, dict)
        assert 'entityTypeId' in schedule
        assert isinstance(schedule['entityTypeId'], int)
        assert 'uf' in schedule
        assert isinstance(schedule['uf'], dict)
        assert 'specialist' in schedule['uf']
        assert isinstance(schedule['uf']['specialist'], str)

    def test_deal_structure(self, constants_json):
        deal = constants_json['deal']
        assert isinstance(deal, dict)
        assert len(deal) == 0

    def test_departments_structure(self, constants_json):
        departments = constants_json['departments']
        assert isinstance(departments, dict)
        for key, value in departments.items():
            assert isinstance(key, str)
            assert isinstance(value, str)

    def test_department_ids_structure(self, constants_json):
        department_ids = constants_json['department_ids']
        assert isinstance(department_ids, dict)
        for key, value in department_ids.items():
            assert isinstance(key, str)
            assert isinstance(value, str)