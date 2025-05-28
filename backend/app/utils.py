from datetime import timedelta
from typing import Dict, List
from urllib.parse import quote as url_quote
import json

from app.handler.interval import Interval
from app.schemas import RequestSchema, RequestSchemaV2
import logging

logger = logging.getLogger(__name__)

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
    work: Interval, busys: List[Interval]
) -> List[Interval]:
    """
    Вычитает занятые интервалы из рабочего интервала, возвращая свободные слоты.

    Args:
        work: Рабочий интервал (Interval).
        busys: Список занятых интервалов (List[Interval]).

    Returns:
        Список свободных интервалов (List[Interval]).
    """
    if not work:
        logger.debug("Рабочий интервал пуст, возвращаю пустой список")
        return []

    # Фильтруем занятые интервалы, оставляя только те, что в тот же день
    work_date = work.start.date()
    relevant_busys = [
        busy
        for busy in busys
        if busy.start.date() == work_date and busy.end.date() == work_date
    ]

    logger.debug(
        f"Subtract busy: work={work}, relevant_busys={[str(b) for b in relevant_busys]}"
    )

    if not relevant_busys:
        logger.debug(
            "Нет занятых интервалов в этот день, возвращаю весь рабочий интервал"
        )
        return [work]

    # Нормализуем временные зоны
    work_start = work.start
    work_end = work.end
    free_slots = []
    current_start = work_start

    # Сортируем занятые интервалы по началу
    sorted_busys = sorted(relevant_busys, key=lambda x: x.start)

    for busy in sorted_busys:
        busy_start = busy.start
        busy_end = busy.end

        # Пропускаем занятые интервалы, которые заканчиваются до начала рабочего времени
        if busy_end <= work_start:
            logger.debug(f"Пропущен занятый интервал {busy}: до начала работы")
            continue

        # Пропускаем занятые интервалы, которые начинаются после конца рабочего времени
        if busy_start >= work_end:
            logger.debug(f"Пропущен занятый интервал {busy}: после конца работы")
            continue

        # Если есть свободный слот до начала занятого интервала
        if current_start < busy_start:
            free_slot = Interval(current_start, min(busy_start, work_end))
            if free_slot.start < free_slot.end:
                free_slots.append(free_slot)
                logger.debug(f"Добавлен свободный слот: {free_slot}")
            else:
                logger.debug(f"Пропущен пустой слот: {free_slot}")

        # Перемещаем текущую точку после конца занятого интервала
        current_start = max(busy_end, current_start)

    # Добавляем последний слот, если он есть
    if current_start < work_end:
        free_slot = Interval(current_start, work_end)
        if free_slot.start < free_slot.end:
            free_slots.append(free_slot)
            logger.debug(f"Добавлен последний свободный слот: {free_slot}")
        else:
            logger.debug(f"Пропущен пустой последний слот: {free_slot}")

    logger.debug(
        f"Возвращено {len(free_slots)} свободных слотов: {[str(s) for s in free_slots]}"
    )
    return free_slots


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


def parse_query_v2(query: Dict) -> RequestSchemaV2:
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
        return RequestSchemaV2(**obj)
    except Exception as e:
        print(f"Ошибка при создании RequestSchema: {e}")
        raise
