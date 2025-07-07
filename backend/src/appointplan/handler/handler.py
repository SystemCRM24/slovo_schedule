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
from .service import Department, Specialist, AppointmentValidator, DaySlots
from src.utils import BatchBuilder


class Handler:

    def __init__(self, request: str):
        self.request = request                          # Сырой запрос
        self.deal: Deal = None                          # Инфа по сделке
        self.users = [Settings.DEFAULT_USER]            # Cписок пользвателей, кому будет отправлены уведомления
        self.stages: list[Stage] = []                   # Стадии, занятия в которых нужно распланировать
        self.departments: dict[str, Department] = {}    # Подразделения по типу
        self.message = None                             # Сообщение, которое пошлем пользователю
        self.appointments: list[BXAppointment] = []     # Расставленные занятия

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
            self.appointments.clear()
        except Exception as e:
            self.message = str(e)
            stack = traceback.extract_stack()
            trace_format = traceback.format_exc()
            AEHM._log_app_exception(stack, trace_format)
            self.appointments.clear()
        asyncio.create_task(self.send_message())
        asyncio.create_task(self.send_comment())
        return await self.send_appointments()

    def plan_appointments(self, stage: Stage, app_set: AppointmentSet):
        """
        Непосредственно, сама работа обработчика.
        Логика поможет реализовать правило не больше 2х занятий в день
        """
        department = self.departments[app_set.type]
        set_qty = app_set.quantity
        start = stage.start
        validator = AppointmentValidator(self.appointments)
        while set_qty > 0:
            days = department.get_slots(start, app_set.duration)
            is_find = None
            for slots_of_day in days:
                if set_qty > 2:     # В рамках дня пытаемся найти время для 2х занятий
                    first, second = self.find_double(slots_of_day)
                    is_first_valid = is_second_valid = False
                    if first is not None:
                        is_first_valid = validator.check(first)
                        if is_first_valid:
                            set_qty -= 1
                            is_find = self.put_appointment(first)
                    if second is not None:
                        is_second_valid = validator.check(second)
                        if is_second_valid:
                            set_qty -= 1
                            is_find = self.put_appointment(second)
                    if is_first_valid or is_second_valid:
                        break
                appointment = self.find_one(slots_of_day, app_set)
                if validator.check(appointment):
                    set_qty -= 1
                    is_find = self.put_appointment(appointment)
                    break
            if is_find is None:
                start += app_set.duration
            else:
                start = is_find.end
            if stage.end < start:
                raise AppointplanException(f'Не найден свободный слот для занятия {app_set.type}.')

    def find_one(self, slots_of_day: list[DaySlots], app_set: AppointmentSet):
        for slot_of_day in slots_of_day:
            for interval in slot_of_day.intervals:
                if interval.duration >= app_set.duration:
                    appointment = BXAppointment(
                        id=-1,
                        assignedById=slot_of_day.specialist.id,
                        ufCrm3Code=None,
                        ufCrm3Children=self.deal.patient,
                        ufCrm3StartDate=interval.start,
                        ufCrm3EndDate=interval.start + app_set.duration,
                        ufCrm3HistoryClient=self.deal.patient  
                    )
                    appointment.code = app_set.type
                    return appointment

    def find_double(self, slots_of_day: list[DaySlots]):
        return None, None

    def put_appointment(self, appointment: BXAppointment):
        self.appointments.append(appointment)
        department = self.departments[appointment.code]
        department.rebuild_map_of_specialist(appointment.specialist)
        return appointment

    def build_appointment(self, slot: DaySlots, app_set: AppointmentSet, interval) -> BXAppointment:
        appointment = BXAppointment(
            id=-1,
            assignedById=slot.specialist.id,
            ufCrm3Code=None,
            ufCrm3Children=self.deal.patient,
            ufCrm3StartDate=interval.start,
            ufCrm3EndDate=interval.end,
            ufCrm3HistoryClient=self.deal.patient            
        )
        appointment.code = app_set.type
        return appointment

    async def send_message(self):
        """Посылает сообщение пользователю в битру"""
        batches = {}
        for index, user in enumerate(self.users):
            batch = BatchBuilder(
                'im.notify.personal.add',
                {'USER_ID': user, 'MESSAGE': self.message}
            )
            batches[index] = batch.build()
        await BitrixClient.call_batch(batches)
    
    async def send_appointments(self):
        """Посылает батч-запрос на расстановку занятий в битру."""
        for appointment in self.appointments:
            fields = {
                'assignedById': appointment.specialist,
                'ufCrm3Code': [BXConstants.appointment.lfv.idByCode.get(appointment.code)],
                'ufCrm3Children': appointment.patient,
                'ufCrm3StartDate': appointment.start.isoformat(),
                'ufCrm3EndDate': appointment.end.isoformat(),
                'ufCrm3HistoryClient': appointment.patient      
            }
            result = await BitrixClient.create_crm_item(
                BXConstants.appointment.entityTypeId,
                fields
            )
            appointment.id = result.get('id')
        logger.info('The appointments were scheduled.')
        return self.appointments

    async def send_comment(self):
        if not self.appointments:
            return
        specialists_lst, patients_lst = await asyncio.gather(
            BitrixClient.get_all_specialist(),
            BitrixClient.get_all_clients()
        )
        specialists = {int(s.get('ID', '0')): s for s in specialists_lst}
        patient = str(self.deal.patient)
        for c in patients_lst:
            if c.get('ID', '0') == patient:
                patient = c
                break
        patient_fio = patient.get('LAST_NAME', '') + ' ' + patient.get('NAME', '')[0]       # type:ignore
        template = "[*] {0} - {1}, {2}, {3}, {4} минут."

        def iterator():
            for app in self.appointments:
                specialist = specialists[app.specialist]
                spec_fio = specialist.get('LAST_NAME', '') + ' ' + specialist.get('NAME', '')[0]    # type:ignore
                date = app.start.strftime(r'%d.%m.%Y %H:%M')    #type:ignore
                duration = app.end - app.start                  #type:ignore
                duration = int(duration.total_seconds() // 60)  #type:ignore
                yield template.format(spec_fio, patient_fio, app.code, date, duration)
    
        comment = f'Добавлены занятия:\n[list=1]{'\n'.join(iterator())}[/list]'
        return await BitrixClient.add_comment_to_deal(self.deal.id, comment)


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
