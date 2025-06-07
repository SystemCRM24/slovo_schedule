import pytest
import json


@pytest.fixture(scope='class')
def test_schedule() -> dict:
    return {
        "id": 138,
        "specialist": 19,
        "date": "2025-06-06T03:00:00+03:00",
        "intervals": [
            "1749189600000:1749222000000"
        ]
    }


class TestCreateAndDeleteSchedule:

    @pytest.fixture(autouse=True)
    def _setup(self, test_client):
        self.client = test_client

    def test_create_one(self, test_schedule):
        content = json.dumps(test_schedule)
        response = self.client.post('/front/schedule/', content=content)
        assert response.status_code == 201
        json_data = response.json()
        test_schedule['id'] = json_data['id']
        assert json_data == test_schedule

    def test_delete_one(self, test_schedule):
        print(test_schedule)
        response = self.client.delete(f'/front/schedule/{test_schedule['id']}')
        assert response.status_code == 204


class SetupSchedule:

    @pytest.fixture(scope='class', autouse=True)
    def _setup_obj(self, test_client, test_schedule):
        content = json.dumps(test_schedule)
        response = test_client.post('/front/schedule/', content=content)
        json_data = response.json()
        test_schedule['id'] = json_data['id']
        yield
        test_client.delete(f'/front/schedule/{test_schedule['id']}')


class TestGetAppointment(SetupSchedule):

    def test_one(self, test_client, test_schedule):
        response = test_client.get(f'/front/schedule/{test_schedule['id']}')
        assert response.status_code == 200
        json_data = response.json()
        assert json_data == test_schedule


class TestUpdateAppointment(SetupSchedule):

    def test_one(self, test_client, test_schedule):
        test_schedule['intervals'].append('1749289600000:1749322000000')
        content = json.dumps(test_schedule)
        response = test_client.put(f'/front/schedule/{test_schedule['id']}', content=content)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data == test_schedule
