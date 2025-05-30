from datetime import datetime, timedelta
import logging
from typing import List, Tuple
from .interval import Interval
from app import bitrix
from app.utils import BatchBuilder, subtract_busy_from_interval
from app.settings import Settings

logger = logging.getLogger(__name__)

class Specialist:
    """Класс для работы с графиком и расписанием занятий специалиста"""

    def __init__(self, now: datetime, code: str, qty: int, duration: int, stage_duration: int):
        self.now = now
        self.code = code
        self.qty = qty
        self.duration = duration
        self.stage_duration = stage_duration
        self.possible_specs: List[dict] = []
        self.specialists_data: dict = {}
        logger.debug(f"Создан Specialist: code={code}, qty={qty}, duration={duration}, stage_duration={stage_duration}")

    def get_specialists_info_batch(self, departments: dict[str, dict]) -> str:
        """Выдает батч на получение информации по спецам для этого кода"""
        department_id = None
        for id, department in departments.items():
            if department.get("NAME") == self.code:
                department_id = id
                break
        if not department_id:
            logger.warning(f"Отдел для типа {self.code} не найден")
            return BatchBuilder("user.get", {"filter": {"ACTIVE": True}}).build()
        params = {"filter": {"ACTIVE": True, "UF_DEPARTMENT": department_id}}
        batch = BatchBuilder("user.get", params)
        logger.debug(f"Сформирован батч для отдела {department_id}, code={self.code}")
        return batch.build()

    def get_free_slots_count(self) -> int:
        slots = self.get_all_free_slots()
        return len(slots)

    def get_all_free_slots(self) -> List[Tuple[str, Interval]]:
        all_slots = []
        specialists_data = getattr(self, "specialists_data", {})
        now = datetime.now(Settings.TIMEZONE)
        total_duration = self.stage_duration * 7 * 2  # 56 дней для двух этапов
        max_date = now + timedelta(days=total_duration)
        logger.debug(f"Поиск свободных слотов для code={self.code}, now={now}, max_date={max_date}")

        if not specialists_data:
            logger.error(f"Нет данных о специалистах для code={self.code}")
            return []

        for spec_id, data in specialists_data.items():
            schedule = data.get("schedule", [])
            appointments = data.get("appointments", [])
            intervals = []

            if not schedule:
                logger.error(f"Нет графика для специалиста {spec_id}")
                continue

            for s in schedule:
                intervals_ms = s.get("ufCrm4Intervals", [])
                if intervals_ms:
                    for pair in intervals_ms:
                        try:
                            start_ms, end_ms = map(int, pair.split(":"))
                            start = datetime.fromtimestamp(start_ms / 1000, tz=Settings.TIMEZONE)
                            end = datetime.fromtimestamp(end_ms / 1000, tz=Settings.TIMEZONE)
                            if now <= start <= max_date:
                                intervals.append(Interval(start, end))
                            else:
                                logger.debug(f"Пропущен интервал {start} — {end}: вне периода")
                        except (ValueError, TypeError) as e:
                            logger.error(f"Ошибка обработки интервала {pair} для {spec_id}: {e}")
                            continue
                else:
                    try:
                        start = datetime.fromisoformat(s.get("ufCrm4Date"))
                        end = datetime.fromisoformat(s.get("ufCrm4DateEnd"))
                        if now <= start <= max_date:
                            intervals.append(Interval(start, end))
                        else:
                            logger.debug(f"Пропущен график {start} — {end}: вне периода")
                    except (ValueError, TypeError) as e:
                        logger.error(f"Ошибка обработки графика {s} для {spec_id}: {e}")
                        continue

            busy = []
            for a in appointments:
                start_str = a.get("ufCrm3StartDate")
                end_str = a.get("ufCrm3EndDate")
                if start_str and end_str:
                    try:
                        start = datetime.fromisoformat(start_str)
                        if now <= start <= max_date:
                            busy.append(Interval.from_iso(start_str, end_str))
                    except ValueError as e:
                        logger.error(f"Ошибка обработки занятия {start_str} — {end_str}: {e}")
                        continue

            free_slots = []
            for work_interval in intervals:
                slots = subtract_busy_from_interval(work_interval, busy)
                for slot in slots:
                    duration_minutes = (slot.end - slot.start).total_seconds() / 60
                    if duration_minutes >= self.duration:
                        free_slots.append(slot)
                    else:
                        logger.debug(f"Слот {slot.start} — {slot.end} слишком короткий ({duration_minutes} мин < {self.duration} мин)")

            all_slots += [(spec_id, slot) for slot in free_slots]
            logger.debug(f"Найдено {len(free_slots)} слотов для специалиста {spec_id}")

        logger.info(f"Всего найдено {len(all_slots)} свободных слотов для code={self.code}")
        return all_slots