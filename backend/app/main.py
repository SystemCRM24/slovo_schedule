from datetime import datetime, timedelta
from typing import Self

from .utils import BatchBuilder
from .settings import Settings, UserFields
from . import bitrix


class Interval:
    __slots__ = ('start', 'end')

    @classmethod
    def from_timestamp(cls, start: float, end: float) -> Self:
        """Создает объект на основе таймстампов"""
        return cls(
            start=datetime.fromtimestamp(start, Settings.TIMEZONE),
            end=datetime.fromtimestamp(end, Settings.TIMEZONE)
        )
    
    @classmethod
    def from_iso(cls, start: str, end: str) -> Self:
        return cls(
            start=datetime.fromisoformat(start),
            end=datetime.fromisoformat(end)
        )

    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(start={repr(self.start)}, end={repr(self.end)})'

    def __contains__(self, other) -> bool:
        if isinstance(other, datetime):
            return self.start <= other <= self.end
        return self.start <= other.start and self.end >= other.end
    
    def __bool__(self) -> bool:
        return self.start < self.end
    
    def duration(self) -> timedelta:
        """Возвращает длительность интервала"""
        return self.end - self.start


class SpecialistSchedule:
    """Класс для работы с графиком и расписанием занятий специалиста"""

    def __init__(
        self, 
        specialist_id, 
        schedule, 
        appointments, 
        duration,
        now
    ):
        self.specialist_id = specialist_id
        self.schedule = schedule
        self.appointments = appointments
        self.duration = duration        # Время в минутах
        self.now = now
        self._last_find = None

    @property
    def last_find(self):
        """Ищет подходящее время для занятия"""
        if self.duration is None:
            return self._last_find
        if self._last_find is not None:
            return self._last_find
        schedule_intervals = self.create_schedule_intervals()
        appointments_intervals = self.create_appointments_intervals()
        for schedule_interval in schedule_intervals:
            if schedule_interval.end < self.now:
                continue
            if self.now in schedule_interval:
                schedule_interval.start = self.now
            for appointment_interval in appointments_intervals:
                if appointment_interval in schedule_interval:
                    schedule_interval.start = appointment_interval.end
        appointment_duration = timedelta(minutes=self.duration)
        for schedule_interval in schedule_intervals:
            if schedule_interval.duration() > appointment_duration:
                self._last_find = Interval(
                    start=schedule_interval.start,
                    end=schedule_interval.start + appointment_duration
                )
                break
        return self._last_find
    
    def create_schedule_intervals(self) -> list[Interval]:
        """Возвращает список интеравалов рабочего графика"""
        intervals = []
        for day in self.schedule:
            raw_intervals = day.get('ufCrm4Intervals', [])
            for raw_interval in raw_intervals:
                start, end = map(
                    lambda x: float(x) / 1000,
                    raw_interval.split(':')
                )
                intervals.append(Interval.from_timestamp(start, end))
        return intervals
    
    def create_appointments_intervals(self) -> list[Interval]:
        """Возвращает список интервалов занятий"""
        intervals = []
        for appointemnt in self.appointments:
            interval = Interval.from_iso(
                start=appointemnt.get('ufCrm3StartDate', ''),
                end=appointemnt.get('ufCrm3EndDate', '')
            )
            intervals.append(interval)
        return intervals
