from typing import Generator
from datetime import date, timedelta, datetime

from src.schemas.api import BXSpecialist
from src.schemas.appointplan import BXSchedule, BXAppointment
from src.utils import Interval


class AppointplanException(Exception):
    """
    Класс для исключений, которые будут рейзится во время расстановки занятий.
    Реализует транзакционность.
    """
    pass


class DaySlots:
    """Описывает свободный временной слот"""

    __slots__ = ('date', 'specialist', 'intervals')

    def __init__(self, date: date, specialist: BXSpecialist, intervals: list[Interval]):
        self.date = date
        self.specialist = specialist
        self.intervals = intervals
    
    def __str__(self):
        return f'{self.__class__.__name__}({self.date})'
    
    def __repr__(self):
        return str(self)

    def find(self, duration: timedelta) -> Interval | None:
        """Возвращает интервал, если он больше длительности или None"""
        for interval in self.intervals:
            if interval.duration > duration:
                return interval


class Department:
    
    def __init__(self):
        self.specialists: list[Specialist] = []
    
    def get_slots(self, start: datetime, set_duration: timedelta) -> list[DaySlots]:
        """Выдает свободный слот"""
        start_date = start.date()
        dates = set()
        for specialist in self.specialists:
            for slot_date in specialist.map.keys():
                if slot_date >= start_date:
                    dates.add(slot_date)
        dates = sorted(dates)
        for slot_date in dates:
            slots = []
            for specialist in self.specialists:
                intervals = specialist.map.get(slot_date, None)
                if intervals is None:
                    continue
                slot = DaySlots(slot_date, specialist.info, [])
                for interval in intervals:
                    if interval.end < start:
                        continue
                    slot_start = start if start > interval.start else interval.start
                    slot_end = slot_start + set_duration
                    while slot_end < interval.end:
                        slot.intervals.append(Interval(slot_start, slot_end))
                        slot_start = slot_end
                        slot_end = slot_start + set_duration
                slots.append(slot)
            yield slots

    def rebuild_map_of_specialist(self, id: int):
        for spec in self.specialists:
            if spec.info.id == id:
                spec.rebuild_map()


class Specialist:
    
    def __init__(self, info: BXSpecialist):
        self.info = info
        self.schedules: list[BXSchedule] = []
        self.appointments: list[BXAppointment] = []
        self.map = {}
    
    def rebuild_map(self):
        """Создает карту (словарь) из свободных промежутков по дням"""
        self.map.clear()
        for schedule in self.schedules:
            for interval in schedule.intervals:
                interval_date = interval.start.date()
                intervals = self.map.get(interval_date, None)
                if intervals is None:
                    intervals = self.map[interval_date] = []
                intervals.append(interval)
        for appointment in self.appointments:
            appointment_date = appointment.start.date()
            schedule_intervals = self.map.get(appointment_date, None)
            if schedule_intervals is None:
                continue
            appointment_interval = appointment.interval
            is_intersected = False
            for index, interval in enumerate(schedule_intervals):
                if interval.is_intersecting(appointment_interval):
                    is_intersected = True
                    break
            if not is_intersected:
                continue
            left, right = interval.difference(appointment_interval)
            left_exist = False
            if left is not None:
                left_exist = True
                schedule_intervals[index] = left
            if right is not None:
                if not left_exist:
                    schedule_intervals[index] = right
                else:
                    schedule_intervals.insert(index + 1, right)


class AppointmentValidator:
    """Валидирует возможное занятие"""

    __slots__ = ('other', 'appointment')

    def __init__(self, other: list[BXAppointment]):
        self.other = other
        self.appointment: BXAppointment = None

    def check(self, appointment: BXAppointment) -> bool:
        """Валидация занятия"""
        self.appointment = appointment
        return all(self._validate())
    
    def _validate(self) -> Generator[bool]:
        """Непосредственно, валидирует занятия."""
        # Если список пустой, то можно сразу True возвращать для всего. Сравнивать не с чем
        if len(self.other) == 0:
            return True
        if self.appointment is None:
            return False
        yield self.check_type_limit()
        yield self.check_day_limit()
        yield self.check_same_time()
        yield self.check_break_duration()

    def check_type_limit(self) -> bool:
        dct = {self.appointment.start.date(): {self.appointment.code: 1}}
        for appointment in self.other:
            appointment_date = appointment.start.date()
            date_record = dct.get(appointment_date, None)
            if date_record is None:
                date_record = dct[appointment_date] = {}
            count = date_record.get(appointment.code, None)
            if count is None:
                count = date_record[appointment.code] = 0
            count += 1
            if count == 3:
                return False
            date_record[appointment.code] = count
        return True

    def check_day_limit(self) -> bool:
        """Не больше 6 занятий в 1 день"""
        dct = {self.appointment.start.date(): 1}
        for appointment in self.other:
            appointment_date = appointment.start.date()
            count = dct.get(appointment_date, None)
            if count is None:
                count = dct[appointment_date] = 0
            count += 1
            if count == 7:
                return False
        return True
    
    def check_same_time(self) -> bool:
        """Проверяет, не попадают ли занятия на одно время."""
        for appointment in self.other:
            if appointment.interval.is_intersecting(self.appointment.interval):
                return False
        return True

    def check_break_duration(self) -> bool:
        """Проверяет занятия на длительность перерыва"""
        last = self.other[-1]
        if last.end.date() != self.appointment.end.date():
            return True
        break_duration = self.appointment.start - last.end
        return break_duration < timedelta(minutes=45)
        