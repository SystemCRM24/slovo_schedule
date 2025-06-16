"""
Тестирование автозаполнения расписания.
Запрос приходит в виде json-строки, которая находится в query-параметре data.
Основыные моменты, которые нужно помнить:

1) Транзакционность. Если какой-то один пункт не соблюден, то занятия не проставляются.
2) По специалистам:
 - Специалист может работать на несколько подразделений
 - У специалиста может быть сколько угодно много занятий в день. Ограничено графиком работы.
 - Занятия для специалиста могут идти друг за другом без перерыва.
3) По детям:
 - Не больше 2х занятий одного типа в 1 день
 - Не больше 6 занятий в 1 день
 - Между занятиями перерыв не более 45 минут
4) По занятиям:
 - Занятия начинаются с определенной даты указанной в запросе.
 - Занятия могут делиться на несколько стадий. Это указано в запросе.
 - Стадии идут друг за другом без перерыва. Следующая стадия начинается на следующий день от конца предыдущей.
 - Стадии имеют продолжительность, которая выражена в неделях. Например, 4 недели.
 - Если занятия выходят за продолжительность стадии, то это ошибка.
 - Стадия может содержать занятия нескольких типов.
 - Помимо типа, занятия имеют атрибуты: количество и продолжительность (выражено в минутах)Занятия имеют тип,
 - Внутри одной стадии занятия разных типов можно ставить "плоско", т.е. не обязательно, что они идут друг за другом.
"""

import pytest
import os
import json
from pathlib import Path

from src.appointplan.handler import Handler
from src.appointplan.handler.handler import Context
from src.schemas.appointplan import Deal


def parse_mock_data() -> list:
    lst = []
    path = Path(__file__).parent / 'mocks'
    for request in os.listdir(str(path)):
        with open(path / request, mode='r', encoding='utf-8') as file:
            data = json.load(file)
        lst.append(json.dumps(data))
    return lst

samples = parse_mock_data()


@pytest.fixture(scope='class', params=samples)
def test_handler(request, test_client):
    return Handler(request.param)


class TestHandler:

    def test_0(self):
        pass

    def test_1(self):
        pass


# class TestHandlerContext:

#     @pytest.mark.asyncio
#     async def test_context_filling(self, test_handler: Handler):
#         result = await test_handler.run()
#         for appointment in result:
#             test_handler
