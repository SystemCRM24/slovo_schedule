import pytest
import os
import json
from pathlib import Path


def parse_mock_data() -> list:
    lst = []
    path = Path(__file__).parent / 'mocks'
    for request in os.listdir(str(path)):
        if request.startswith('repetative'):
            with open(path / request, mode='r', encoding='utf-8') as file:
                data = json.load(file)
            lst.append(json.dumps(data))
    return lst

samples = parse_mock_data()


@pytest.fixture(scope='class', params=samples)
def test_data(request, test_client):
    url = f'/test_repetative?data={request.param}'
    result = test_client.post(url).json()
    print('-' * 20)
    print(result)
    print('-' * 20)
    yield result


class TestHandler:

    def test_delete(self, test_data, test_client):
        appointment = test_data[0]
        result = test_client.delete(f'front/appointment/massive/{appointment.get('item', {}).get('id')}')
        print('[DEBUG]', result)
