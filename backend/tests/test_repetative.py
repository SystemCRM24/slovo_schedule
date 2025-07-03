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
    yield result
    for appointment in result:
        test_client.delete(f'front/appointment/{appointment['id']}')


class TestHandler:

    def test_0(self, test_data):
        print(test_data)