from datetime import timedelta
from typing import Dict
from urllib.parse import quote as url_quote
import json

from app.handler.interval import Interval
from app.schemas import RequestSchema


class BatchBuilder:
    """Создает батч запрос"""

    __slots__ = ("method", "params")

    def __init__(self, method: str, params: dict | None = None):
        self.method = method
        self.params = params or {}

    def build(self) -> str:
        """Возвращает батч-запрос в виде строки"""
        batch = f"{self.method}?"
        for cmd, cmd_params in self.params.items():
            match cmd_params:
                case dict() as params:
                    batch += self._get_subbatch_from_dict(cmd, params)
                case tuple() | list() as params:
                    batch += self._get_subbatch_from_iterable(cmd, params)
                case params:
                    batch += self._get_subbatch(cmd, params)
        return batch

    @staticmethod
    def _get_subbatch_from_dict(cmd, params: dict) -> str:
        """Возвращает подзапрос для словарей"""
        subbatch = ""
        for key, value in params.items():
            key = url_quote(str(key))
            if isinstance(value, tuple | list):
                for sub_cmd in BatchBuilder._iterable_iterator(value):
                    subbatch += f"&{cmd}[{key}]{sub_cmd}"
            else:
                value = url_quote(str(value))
                subbatch += f"&{cmd}[{key}]={value}"
        return subbatch

    @staticmethod
    def _get_subbatch_from_iterable(cmd, params: list | tuple) -> str:
        """Возвращает подзапрос для словарей"""
        subbatch = ""
        for sub_cmd in BatchBuilder._iterable_iterator(params):
            subbatch += f"&{cmd}{sub_cmd}"
        return subbatch

    @staticmethod
    def _iterable_iterator(iterable: tuple | list):
        """Генератор строк из кортежа или списка"""
        for index, value in enumerate(iterable):
            value = url_quote(str(value))
            yield f"[{index}]={value}"

    @staticmethod
    def _get_subbatch(cmd, params: int | float | str) -> str:
        """Возвращает подзапрос для этих типов данных"""
        params = url_quote(str(params))
        subbatch = f"&{cmd}={params}"
        return subbatch


def subtract_busy_from_interval(
    work: Interval, busys: list[Interval]
) -> list[Interval]:
    print(f"\nSubtract busy: work={work}, busys={busys}")
    busys = sorted(busys, key=lambda x: x.start)
    result = []
    cur = work.start
    for busy in busys:
        if busy.end <= cur or busy.start >= work.end:
            continue
        if busy.start > cur:
            result.append(Interval(cur, busy.start))
        cur = max(cur, busy.end)
    if cur < work.end:
        result.append(Interval(cur, work.end))
    return [x for x in result if x.duration() > timedelta(minutes=0)]


def parse_query(query: str) -> RequestSchema:
    obj = json.loads(query)
    obj["deal_id"] = int(obj["deal_id"])
    obj["user_id"] = int(str(obj["user_id"]).replace("user_", ""))
    for stage in ["first_stage", "second_stage"]:
        if stage in obj:
            obj[stage]["duration"] = int(obj[stage]["duration"])
            for appoint in obj[stage]["data"]:
                if appoint.get("q", ""):
                    appoint["q"] = int(appoint["q"])
                if appoint.get("d", ""):
                    appoint["d"] = int(appoint["d"])
    obj["data"] = {
        "first_stage": obj["first_stage"],
        "second_stage": obj["second_stage"],
    }
    obj.pop("first_stage", None)
    obj.pop("second_stage", None)
    return RequestSchema(**obj)


def parse_query_v2(query: Dict) -> RequestSchema:
    """
    Парсит входной словарь и преобразует его в RequestSchema, удаляя словари в data,
    где t, q или d пустые или None.

    Args:
        query (Dict): Входной словарь с данными о сделке и этапах.

    Returns:
        RequestSchema: Валидированный объект RequestSchema.

    Raises:
        KeyError: Если отсутствуют обязательные ключи (deal_id, user_id).
        ValueError: Если преобразование в int невозможно.
    """
    obj = query.copy()  # Создаем копию, чтобы не изменять исходный словарь

    # Преобразование deal_id и user_id
    try:
        obj["deal_id"] = int(obj["deal_id"])
        obj["user_id"] = int(str(obj["user_id"]).replace("user_", ""))
    except (KeyError, ValueError) as e:
        raise

    # Обработка этапов first_stage и second_stage
    for stage in ["first_stage", "second_stage"]:
        if stage not in obj:
            continue

        try:
            # Преобразование duration в int
            obj[stage]["duration"] = int(obj[stage]["duration"])
        except (KeyError, ValueError) as e:
            raise

        # Фильтрация data: удаляем словари с пустыми t, q, d
        if "data" in obj[stage]:
            filtered_data = []
            for appoint in obj[stage]["data"]:
                # Проверяем, что t, q, d не пустые и не None
                if (
                    appoint.get("t")
                    and appoint.get("t") != ""
                    and appoint.get("q")
                    and appoint.get("q") != ""
                    and appoint.get("d")
                    and appoint.get("d") != ""
                ):
                    try:
                        # Преобразование q и d в int
                        appoint["q"] = int(appoint["q"])
                        appoint["d"] = int(appoint["d"])
                        filtered_data.append(appoint)
                    except ValueError as e:
                        print(
                            f"Пропущен словарь {appoint} в этапе {stage}: ошибка преобразования q или d: {e}"
                        )
                else:
                    print(
                        f"Пропущен словарь {appoint} в этапе {stage}: пустое или отсутствующее t, q или d"
                    )
            obj[stage]["data"] = filtered_data
        else:
            print(f"Отсутствует поле data в этапе {stage}")
            obj[stage]["data"] = []

    # Формирование поля data и удаление исходных этапов
    obj["data"] = {
        "first_stage": obj.get("first_stage", {"duration": 0, "data": []}),
        "second_stage": obj.get("second_stage", {"duration": 0, "data": []}),
    }
    obj.pop("first_stage", None)
    obj.pop("second_stage", None)

    print(f"Парсинг завершен, результат: {obj}")
    try:
        return RequestSchema(**obj)
    except Exception as e:
        print(f"Ошибка при создании RequestSchema: {e}")
        raise
