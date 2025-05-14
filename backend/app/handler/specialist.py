from datetime import datetime

from .interval import Interval
from app import bitrix
from app.utils import BatchBuilder



class Specialist:
    """Класс для работы с графиком и расписанием занятий специалиста"""

    def __init__(self, now: datetime, code: str, qty: int, duration: int):
        self.now = now
        self.code = code
        self.qty = qty
        self.duration = duration
        self.possible_specs: list[dict] = []
    
    def get_specialists_info_batch(self, departments: dict[str, dict]) -> str:
        """Выдает батч на получение информации по спецам для этого кода"""
        department_id = None
        for id, department in departments.items():
            if department.get('NAME', None) == self.code:
                department_id = id
                break
        params = {
            'filter': {
                'ACTIVE': True,
                'UF_DEPARTMENT': department_id
            }
        }
        batch = BatchBuilder('user.get', params)
        return batch.build()
    
    # def 
    


    # def __init__(
    #     self, 
    #     specialist_id, 
    #     schedule, 
    #     appointments, 
    #     duration,
    #     now
    # ):
    #     self.specialist_id = specialist_id
    #     self.schedule = schedule
    #     self.appointments = appointments
    #     self.duration = duration        # Время в минутах
    #     self.now = now
    #     self._last_find = None

    # @property
    # def last_find(self):
    #     """Ищет подходящее время для занятия"""
    #     if self.duration is None:
    #         return self._last_find
    #     if self._last_find is not None:
    #         return self._last_find
    #     schedule_intervals = self.create_schedule_intervals()
    #     appointments_intervals = self.create_appointments_intervals()
    #     for schedule_interval in schedule_intervals:
    #         if schedule_interval.end < self.now:
    #             continue
    #         if self.now in schedule_interval:
    #             schedule_interval.start = self.now
    #         for appointment_interval in appointments_intervals:
    #             if appointment_interval in schedule_interval:
    #                 schedule_interval.start = appointment_interval.end
    #     appointment_duration = timedelta(minutes=self.duration)
    #     for schedule_interval in schedule_intervals:
    #         if schedule_interval.duration() > appointment_duration:
    #             self._last_find = Interval(
    #                 start=schedule_interval.start,
    #                 end=schedule_interval.start + appointment_duration
    #             )
    #             break
    #     return self._last_find
    
    # def create_schedule_intervals(self) -> list[Interval]:
    #     """Возвращает список интеравалов рабочего графика"""
    #     intervals = []
    #     for day in self.schedule:
    #         raw_intervals = day.get('ufCrm4Intervals', [])
    #         for raw_interval in raw_intervals:
    #             start, end = raw_interval.split(':')
    #             interval = Interval.from_js_timestamp(start, end)
    #             intervals.append(interval)
    #     return intervals
    
    # def create_appointments_intervals(self) -> list[Interval]:
    #     """Возвращает список интервалов занятий"""
    #     intervals = []
    #     for appointemnt in self.appointments:
    #         interval = Interval.from_iso(
    #             start=appointemnt.get('ufCrm3StartDate', ''),
    #             end=appointemnt.get('ufCrm3EndDate', '')
    #         )
    #         intervals.append(interval)
    #     return intervals
