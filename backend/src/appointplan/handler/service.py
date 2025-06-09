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


class Department:
    
    def __init__(self):
        self.specialists: list[Specialist] = []
    
    def free_slots(self) -> Generator[BXAppointment]:
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
        self.schedules_intervals: list[Interval] = []
        self.appointments: list[BXAppointment] = []

    def get_schedule_intervals(self):
        """Вытаскивает интервалы из скхедулес и сортирует их"""
        for schedule in self.schedules:
            self.schedules_intervals.extend(schedule.intervals)

    def free_slots(self) -> Generator[BXAppointment]:
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
                        yield self.create_appointment(interval)
            # Если не был пересечен, то можно отдать интервал графика
            if not was_intersected:
                yield self.create_appointment(s_interval)

    def create_appointment(self, interval: Interval) -> BXAppointment:
        """Создает занятие по интервалу"""
        return BXAppointment(
            id=-1,
            assignedById=self.info.id,
            ufCrm3Code=None,
            ufCrm3Children=None,
            ufCrm3StartDate=interval.start,
            ufCrm3EndDate=interval.end,
            ufCrm3HistoryClient=None
        )
