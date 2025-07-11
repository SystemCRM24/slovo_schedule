import pytest
import json


@pytest.fixture(scope='class')
def test_schedule() -> dict:
    return {
        "id": 3606,
        "specialist": 21,
        "date": "2025-07-07T00:00:00.000Z",
        "intervals": [
            "1751868000000:1751882400000"
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
        response = self.client.delete(f'/front/schedule/{test_schedule['id']}')
        assert response.status_code == 204
    
    def test_create_massive(self, test_schedule):
        content = json.dumps(test_schedule)
        response = self.client.post('/front/schedule/massive/', content=content)
        assert response.status_code == 201
        json_data = response.json()
        test_schedule['id'] = json_data[0]['id']
        assert isinstance(json_data, list)

    def test_update_massive(self, test_schedule):
        test_schedule['intervals'].append('1751886000000:1751904000000')
        content = json.dumps(test_schedule)
        response = self.client.put(f'/front/schedule/massive/{test_schedule['id']}', content=content)
        assert response.status_code == 200
        json_data = response.json()
        assert isinstance(json_data, list)
        for item in json_data:
            response = self.client.delete(f'/front/schedule/{item['id']}')


class SetupSchedule:

    @pytest.fixture(scope='class', autouse=True)
    def _setup_obj(self, test_client, test_schedule):
        content = json.dumps(test_schedule)
        response = test_client.post('/front/schedule/', content=content)
        json_data = response.json()
        test_schedule['id'] = json_data['id']
        yield
        test_client.delete(f'/front/schedule/{test_schedule['id']}')


class TestGetSchedule(SetupSchedule):

    def test_one(self, test_client, test_schedule):
        response = test_client.get(f'/front/schedule/{test_schedule['id']}')
        assert response.status_code == 200
        json_data = response.json()
        assert json_data == test_schedule


class TestUpdateSchedule(SetupSchedule):

    def test_one(self, test_client, test_schedule):
        test_schedule['intervals'].append('1749289600000:1749322000000')
        content = json.dumps(test_schedule)
        response = test_client.put(f'/front/schedule/{test_schedule['id']}', content=content)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data == test_schedule
