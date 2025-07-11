import pytest
import json


@pytest.fixture(scope='class')
def test_appointment() -> dict:
    return {
        'id': 0,
        'specialist': 12,
        'code': 'L',
        'patient': 17,
        'start': "2025-07-07T10:00:00+03:00",
        'end': "2025-07-07T10:30:00+03:00",
        'old_patient': 17
    }


class TestCreateAndDeleteAppointment:

    @pytest.fixture(autouse=True)
    def _setup(self, test_client):
        self.client = test_client

    def test_create_one(self, test_appointment):
        content = json.dumps(test_appointment)
        response = self.client.post('/front/appointment/', content=content)
        assert response.status_code == 201
        json_data = response.json()
        test_appointment['id'] = json_data['id']
        assert json_data == test_appointment

    def test_delete_one(self, test_appointment):
        response = self.client.delete(f'/front/appointment/{test_appointment['id']}')
        assert response.status_code == 204


class SetupAppointment:

    @pytest.fixture(scope='class', autouse=True)
    def _setup_obj(self, test_client, test_appointment):
        content = json.dumps(test_appointment)
        response = test_client.post('/front/appointment/', content=content)
        json_data = response.json()
        test_appointment['id'] = json_data['id']
        yield
        test_client.delete(f'/front/appointment/{test_appointment['id']}')


class TestGetAppointment(SetupAppointment):

    def test_one(self, test_client, test_appointment):
        response = test_client.get(f'/front/appointment/{test_appointment['id']}')
        assert response.status_code == 200
        json_data = response.json()
        assert json_data == test_appointment


class TestUpdateAppointment(SetupAppointment):

    def test_one(self, test_client, test_appointment):
        test_appointment['patient'] = 100
        content = json.dumps(test_appointment)
        response = test_client.put(f'/front/appointment/{test_appointment['id']}', content=content)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data == test_appointment

