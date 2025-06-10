from typing import Generator

from src.schemas.api import BXSpecialist
from src.schemas.appointplan import BXSchedule, BXAppointment
from src.utils import Interval


class AppointplanException(Exception):
    """
    Класс для исключений, которые будут рейзится во время расстановки занятий.
    Реализует транзакционность.
    """
    pass


class Slot:
    """Описывает свободный временной слот"""

    __slots__ = ('specialist', 'interval')

    def __init__(self, specialist: BXSpecialist, interval: Interval):
        self.specialist = specialist
        self.interval = interval


class Department:
    
    def __init__(self):
        self.specialists: list[Specialist] = []
    
    def free_slots(self) -> Generator[Slot]:
        """Выдает свободный слот"""
        for specialist in self.specialists:
            yield from specialist.free_slots()
    
    def sort_specialists_appointments(self):
        """Сортирует занятия специалистов по возрастанию времени."""
        for specialist in self.specialists:
            specialist.appointments.sort(lambda x: x.start)


class Specialist:
    
    def __init__(self, info: BXSpecialist):
        self.info = info
        self.schedules: list[BXSchedule] = []
        self.appointments: list[BXAppointment] = []
        self.map = {}
    
    def rebuild_map(self):
        """Создает карту (словарь) из свободных промежутков по дням"""
        print('\n --------', self.info)
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

    def free_slots(self) -> Generator[Slot]:
        """Выдает свободный слот"""
        for s_interval in self.schedules_intervals:
            was_intersected = False
            for appointment in self.appointments:
                a_interval = appointment.interval
                # Для оптимизации. Ха-ха-ха, кто бы говорил про оптимизацию скриптов в спецсистеме
                if not s_interval.is_intersecting(a_interval):           
                    continue       
                # Если был пересечен, то выдаем части, оставшиеся от разности интервалов.
                was_intersected = True
                result_intervals = s_interval.difference(a_interval)
                for interval in result_intervals:
                    if interval is not None:
                        yield Slot(self.info, interval)
            # Если не был пересечен, то можно отдать интервал графика
            if not was_intersected:
                yield Slot(self.info, s_interval)


class AppointmentValidator:
    """Валидирует возможное занятие"""

    __slots__ = ('other', 'appointment')

    def __init__(self, other: list[BXAppointment], appointment: BXAppointment):
        self.other = other
        self.appointment = appointment

    def is_valid(self) -> bool:
        """Валидация занятия"""
        return all(self._validate())
    
    def _validate(self) -> Generator[bool]:
        """Непосредственно, валидирует занятия."""
        # Если список пустой, то можно сразу True возвращать для всего. Сравнивать не с чем
        if len(self.appointments) == 0:
            return True
        # Проверка на типы занятия
        yield self.check_type_limit()
    
    def check_same_time(self) -> bool:
        """Поставить занятие в пересекающиеся временные интервалы мы не можем"""
        current_interval = self.appointment.interval
        for appointment in self.other:
            if current_interval.is_intersecting(appointment.interval):
                return False

    def check_type_limit(self) -> bool:
        """Не больше 2х занятий одного типа в 1 день"""
        if len(self.other) < 2:         # Если не с чем сравнивать
            return True
        prelast, last = self.ohter[-2:]
        if self.appointment.code != last.code:
            return True


        last_date = last.start.date()
        current_date = self.appointment.start.date()
        if current_date != last_date:
            return True


        prelast_date = prelast.start.date()
        if prelast.start.date() != last.start.date():
            return True
        # Если коды отличаются то можно вернуть True сразу.
        if prelast.code != last.code:
            return True
        return False

    def check_day_limit(self) -> bool:
        """Не больше 6 занятий в 1 день"""
