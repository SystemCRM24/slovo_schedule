from src.schemas.api import BXSpecialist, BXSchedule, BXAppointment


class AppointplanException(Exception):
    """
    Класс для исключений, которые будут рейзится во время расстановки занятий.
    Реализует транзакционность.
    """
    pass


class Department:
    
    def __init__(self):
        self.specialists: list[BXSpecialist] = []


class Specialist:
    
    def __init__(self, info: BXSpecialist):
        self.info = info
        self.schedules: list[BXSchedule] = []
        self.appointments: list[BXAppointment] = []
