from datetime import datetime, timedelta
from typing import Self

from .utils import BatchBuilder
from .settings import settings, UserFields
from . import bitrix


class Interval:
    __slots__ = ('start', 'end')

    @classmethod
    def from_timestamp(cls, start: float, end: float) -> Self:
        """Создает объект на основе таймстампов"""
        return cls(
            start=datetime.fromtimestamp(start, settings.TIMEZONE),
            end=datetime.fromtimestamp(end, settings.TIMEZONE)
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


class Handler:
    """Обрабатывает то, что нужно обработать"""

    def __init__(self, deal_id: str, user_id: str):
        self.deal_id = deal_id
        self.user_id = user_id
        self.initial_time = datetime.now(settings.TIMEZONE)

    async def run(self) -> str:
        """Запускает процесс постановки приема"""
        code_items = await self.get_listfield_values()
        deal = await bitrix.get_deal_info(self.deal_id)
        code = code_items.get(deal.get(UserFields.code, ''))
        duration = self.get_appointment_duration(deal)
        specs = await bitrix.get_specialist_from_code(code)
        schedules = await self.get_specs_schedules(specs, duration)
        sorted_schedules = sorted(
            filter(lambda s: s.last_find != None, schedules),
            key=lambda s: s.last_find
        )
        if not sorted_schedules:
            return
        first = sorted_schedules[0]
        await self.create_appointment(deal, first)

    async def get_listfield_values(self) -> dict:
        """Возвращает словарь, где ключи - id полей, а значения - значения"""
        fields = await bitrix.get_deal_field_values()
        codes = fields.get(UserFields.code, {}).get('items', [])
        return {c.get('ID', None): c.get('VALUE', None) for c in codes}

    async def get_specs_schedules(self, specs: list, duration: int | None) -> list[SpecialistSchedule]:
        """Получает рабочие графики и расписания приемов специалистов"""
        cmd = {}
        date_start = self.initial_time.replace(hour=0, minute=0, second=0, microsecond=0)
        date_start_iso = date_start.isoformat()
        for index, specialist in enumerate(specs):
            index *= 2
            spec_id = specialist.get('ID', '0')
            batch = BatchBuilder('crm.item.list')
            batch.params = {
                'entityTypeId': 1042,       # для получения графика работы специалиста
                'filter': {
                    '>=ufCrm4Date': date_start_iso,
                    'assignedById': spec_id
                },
                'order': {'ufCrm4Date': 'ASC'}
            }
            cmd[index] = batch.build()
            batch.params = {
                'entityTypeId': 1036,       # Для получения расписания занятий
                'filter': {
                    '>=ufCrm3StartDate': date_start_iso,
                    'assignedById': spec_id                    
                },
                'order': {'ufCrm3StartDate': 'ASC'}
            }
            cmd[index + 1] = batch.build()
        response: list = await bitrix.call_batch(cmd)
        result = []
        for i in range(0, len(response), 2):
            specialist = specs[i // 2]
            spec_id = specialist.get('ID', '0')
            result.append(SpecialistSchedule(
                spec_id,
                schedule=response[i]['items'],
                appointments=response[i+1]['items'],
                duration=duration,
                now=self.initial_time
            ))
        return result

    @staticmethod
    def get_appointment_duration(deal: dict) -> int | None:
        """Получает из сделки продолжительность приема"""
        duration = deal.get('UF_CRM_1746625717138', '')
        try:
            return int(duration)
        except:
            return None

    async def create_appointment(self, deal: dict, schedule: SpecialistSchedule):
        """Создает занятие"""
        result = await bitrix.create_appointment({
            'ASSIGNED_BY_ID': schedule.specialist_id,
            'ufCrm3Children': 170,
            'ufCrm3StartDate': schedule.last_find.start.isoformat(),
            'ufCrm3EndDate': schedule.last_find.end.isoformat(),
            'ufCrm3Code': '55',
            'ufCrm3Status': 50
        })
        return result.get('item', None)
