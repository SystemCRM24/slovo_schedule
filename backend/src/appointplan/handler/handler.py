import traceback
import asyncio
import json
from datetime import datetime, timedelta

from src.core import Settings, BitrixClient, BXConstants
from src.logger import logger
from src.middleware import AppExceptionHandlerMiddleware as AEHM
from .service import AppointplanException
from src.schemas.appointplan import Stage, AppointmentSet, Deal
from src.schemas.api import BXSpecialist
from src.schemas.appointplan import BXSchedule, BXAppointment
from .service import Department, Specialist


class Handler:

    def __init__(self, request: str):
        self.request = request                          # Сырой запрос
        self.deal: Deal = None                          # Инфа по сделке
        self.users = [Settings.DEFAULT_USER]            # Cписок пользвателей, кому будет отправлены уведомления
        self.stages: list[Stage] = []                   # Стадии, занятия в которых нужно распланировать
        self.departments: dict[str, Department] = {}    # Подразделения по типу
        self.message = None                             # Сообщение, которое пошлем пользователю
        self.appointments = []                          # Расставленные занятия

    async def run(self):
        """Проставляем занятия и отправляем сообщение. Обернуто в транзакцию."""
        try:
            context = Context(self)
            await context.fill()
            for stage in self.stages:
                for app_set in stage.sets:
                    self.plan_appointments(stage, app_set)
            self.message = "Занятия были расставлены успешно."
        except AppointplanException as app_exc:
            self.message = str(app_exc)
            logger.error(self.message)
        except Exception as e:
            self.message = str(e)
            stack = traceback.extract_stack()
            trace_format = traceback.format_exc()
            AEHM._log_app_exception(stack, trace_format)
        asyncio.create_task(self.send_message())
        return await self.send_appointments()

    def plan_appointments(self, stage: Stage, app_set: AppointmentSet):
        """Непосредственно, сама работа обработчика"""
        # qty = app_set.quantity
        # department = self.departments[app_set.type]
        # while qty > 0:
        #     slot = self.find_slot(department, stage, app_set)
        #     if slot is None:
        #         raise AppointplanException(f'Не найден свободный слот для занятия {app_set.type}.')
        #     print(slot)
        #     qty -= 1
    
    def find_slot(self, department: Department, stage: Stage, app_set: AppointmentSet) -> BXAppointment | None:
        """Ищет и отдает занятие, которое подходит по времени и продолжительности."""
        set_duration = timedelta(minutes=app_set.duration)
        for slot in department.free_slots():
            is_inner = stage.start <= slot.interval.start and stage.end >= slot.interval.end
            appointment_end = slot.interval.start + set_duration
            correct_duration = slot.interval.end >= appointment_end
            if is_inner and correct_duration:
                appointment = BXAppointment(
                    id=-1,
                    assignedById=slot.specialist.id,
                    ufCrm3Code=None,
                    ufCrm3Children=self.deal.patient,
                    ufCrm3StartDate=slot.interval.start,
                    ufCrm3EndDate=slot.interval.end,
                    ufCrm3HistoryClient=self.deal.patient
                )
                appointment.code = app_set.type
                return appointment

    async def send_message(self):
        """Посылает сообщение пользователю в битру"""
        # logger.info('Message was sent')
        logger.warning('Метод отправки сообщений не написан.')
        logger.info(f"Сообщение: {self.message}")
    
    async def send_appointments(self):
        """Посылает батч-запрос на расстановку занятий в битру."""
        # logger.info('The appointments were scheduled.')
        logger.warning('Метод отправки занятий в битру не написан.')
        logger.info(f'Занятия для отправки:\n' + '\n'.join(self.appointments))


class Context:
    """Определяет контекст выполнения для обработчика"""

    __slots__ = ('handler', 'data')

    stage_names = ('first_stage', 'second_stage')

    def __init__(self, handler: Handler):
        self.handler = handler
        self.data: dict = None

    async def fill(self):
        self.data = json.loads(self.handler.request)
        self.fill_user_id()
        self.fill_stages()
        await asyncio.gather(self.fill_deal_info(), self.fill_departments_info())
            
    def fill_user_id(self):
        """Заполняет обработчик инфой о пользвателе, которому нужно отправить сообщение."""
        user_id = self.data.get('user_id', None)
        if user_id:
            self.handler.users.append(user_id)

    def fill_stages(self):
        """Заполняет обработчик стадиями. Фильтрует их и занятия внутри."""
        try:
            start = datetime.fromisoformat(self.data.get('start_date', None))
        except ValueError:
            logger.warning("Failed to retrieve start_date from the request. Using tommorrow's date instead.")
            start = datetime.now(Settings.TIMEZONE) + timedelta(days=1)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        for stage_name in self.stage_names:
            raw_stage: dict = self.data.get(stage_name, None)
            if raw_stage is None:
                continue
            stage = Stage.from_raw(start, raw_stage)
            if stage.is_empty():
                continue
            if not stage.is_valid():
                raise AppointplanException(f"Данные по {stage_name} заполнены некорректно.")
            self.handler.stages.append(stage)
            start = stage.end
    
    async def fill_deal_info(self):
        """Заполняет обработчик инфой о сделке, из которой поступил запрос."""
        deal_id = self.data.get('deal_id', None)
        deal = await BitrixClient.get_deal_info(deal_id)
        self.handler.deal = Deal(**deal)

    async def fill_departments_info(self):
        """Заполняет обработчик информации о подразделениях, специалистах, их графике работы и рассписании."""
        start = end = None
        types = set()
        for stage in self.handler.stages:
            if start is None or stage.start < start:
                start = stage.start
            if end is None or stage.end > end:
                end = stage.end
            for app_set in stage.sets:
                types.add(app_set.type)
        specialists = await self.get_specialist_info(types)
        schedules, appointments = await self.get_specialsts_schedules(start, end, specialists)
        self.build_departments(types, specialists, schedules, appointments)

    async def get_specialist_info(self, types: set) -> list[BXSpecialist]:
        """Получает инфу о специалистах"""
        types = types.copy()
        bx_specialists = await BitrixClient.get_specialists_by_department(types)
        specialists = []
        for spec in bx_specialists:
            bxspec = BXSpecialist(**spec)
            specialists.append(bxspec)
            types -= set(bxspec.departments)  # вычитаем из множества другое множество на месте
        if len(types) > 0:
            raise AppointplanException(f'Не найден специалист для подразделений {types}.')
        return specialists
    
    @staticmethod
    async def get_specialsts_schedules(start, end, specialists) -> tuple[list, list]:
        """Получает и возвращает графики и расписания специалистов"""
        start_iso, end_iso = start.isoformat(), end.isoformat()
        specialists_ids = [s.id for s in specialists]
        schedules, appointments = await asyncio.gather(
            BitrixClient.get_specialists_schedules(start_iso, end_iso, specialists_ids),
            BitrixClient.get_specialists_appointments(start_iso, end_iso, specialists_ids)
        )
        schedules = [BXSchedule(**s) for s in schedules]
        appointments = [BXAppointment(**a) for a in appointments]
        return schedules, appointments

    def build_departments(
        self,
        departments: set[str],
        specialists: list[BXSpecialist],
        schedules: list[BXSchedule],
        appointments: list[BXAppointment]
    ):
        """Собирает департаменты из специалистов, распределяет по ним графики и занятия."""
        for department_type in departments:
            self.handler.departments[department_type] = Department()
        specialists_by_id: dict[int, Specialist] = {}
        for bxspec in specialists:
            spec = specialists_by_id[spec.info.id] = Specialist(bxspec)
            for department_type in spec.info.departments:
                if department_type in self.handler.departments:
                    self.handler.departments[department_type].specialists.append(spec)
        for schedule in schedules:
            if schedule.is_valid():
                spec = specialists_by_id.get(schedule.specialist, None)
                if spec is not None:
                    spec.schedules.append(schedule)
        for appointment in appointments:
            if appointment.is_valid():
                spec = specialists_by_id.get(appointment.specialist, None)
                if spec is not None:
                    spec.appointments.append(appointment)
        # Заполним интервалами тут
        for specialist in specialists_by_id.values():
            specialist.rebuild_map()
