import asyncio
import json
from datetime import datetime, timedelta

from src.utils import BatchBuilder
from src.logger import logger
from src.core import Settings, BXConstants, BitrixClient
from src.schemas.api import BXSpecialist
from src.schemas.appointplan import BXAppointment, BXSchedule


class Handler:

    def __init__(self, request: str) -> None:
        self.request = request
        self.request_data = {}
        self.start = datetime.now(Settings.TIMEZONE)
        self.specialists: dict[int, BXSpecialist] = {}
        self.schedules: dict[int, list[BXSchedule]] = {}
        self.appointments: dict[int, list[BXAppointment]] = {}
        self.users = [Settings.DEFAULT_USER]
        self.repetatives: list[BXAppointment] = []
    
    async def run(self):
        context = Context(self)
        await context.fill()
        specialist_id = self.select_specialist()
        self.create_repetatives(specialist_id)
        await self.send_message()
        return await self.send_appointments()
    
    def select_specialist(self) -> int:
        durations = {}
        zero_interval = timedelta(days=0)
        for spec_id, schedules in self.schedules.items():
            durations[spec_id] = zero_interval
            for schedule in schedules:
                durations[spec_id] += sum((i.duration for i in schedule.intervals), start=zero_interval)
        for spec_id, appointments in self.appointments.items():
            durations[spec_id] -= sum((a.interval.duration for a in appointments), start=zero_interval)
        return sorted(durations.items(), key=lambda x: x[1])[-1][0]
    
    def create_repetatives(self, spec_id: int):
        """Создает повторяющиеся занятия"""
        spec_schedules = self.schedules[spec_id]
        repetative_weekday = int(self.request_data.get('day', '0'))
        hour, minute = map(int, self.request_data['time'].split(':'))
        duration = timedelta(minutes=float(self.request_data.get('duration', '0')))
        for schedule in spec_schedules:
            for interval in schedule.intervals:
                if repetative_weekday != interval.start.weekday():
                    continue
                start = interval.start
                start = start.replace(hour=hour, minute=minute, second=0, microsecond=0)
                end = start + duration
                if start in interval and end in interval:
                    appointment = self.build_appointment(spec_id, start, end)
                    self.repetatives.append(appointment)
    
    def build_appointment(self, spec_id: int, start: datetime, end: datetime) -> BXAppointment:
        appointment = BXAppointment(
            id=-1,
            assignedById=spec_id,
            ufCrm3Code=None,
            ufCrm3Children=self.request_data['patient'],
            ufCrm3HistoryClient=self.request_data['patient'],
            ufCrm3StartDate=start,
            ufCrm3EndDate=end
        )
        appointment.code = self.request_data['code']
        return appointment
    
    async def send_message(self):
        """Посылает сообщение пользователю в битру"""
        if not self.repetatives:
            return
        batches = {}
        for index, user in enumerate(self.users):
            batch = BatchBuilder(
                'im.notify.personal.add',
                {'USER_ID': user, 'MESSAGE': "Занятия были расставлены"}
            )
            batches[index] = batch.build()
        await BitrixClient.call_batch(batches)
    
    async def send_appointments(self):
        """Посылает батч-запрос на расстановку занятий в битру."""
        for appointment in self.repetatives:
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
        logger.info('The repetatives were scheduled.')
        return self.repetatives


class Context:

    __slots__ = ('handler', 'data')

    def __init__(self, handler: Handler) -> None:
        self.handler = handler
        self.data: dict | None = None

    async def fill(self):
        self.data = json.loads(self.handler.request)
        self.handler.request_data.update(self.data)
        await self.fill_specialists()
        date_start = datetime.now(Settings.TIMEZONE) - timedelta(days=60)
        self.handler.start = date_start
        date_start_iso = date_start.isoformat()
        next_year = date_start + timedelta(days=365)
        next_year_iso = next_year.isoformat()
        await asyncio.gather(
            self.fill_schedules(date_start_iso, next_year_iso),
            self.fill_appointments(date_start_iso, next_year_iso)
        )

    async def fill_specialists(self):
        """Заполняет атрибут specialists специалистами по их ид"""
        code = self.data.get('code', None)
        if code is None:
            return
        specs = await BitrixClient.get_specialists_by_department((code, ))
        self.handler.specialists.clear()
        for s in specs:
            bxspec = BXSpecialist(**s)
            self.handler.specialists[bxspec.id] = bxspec
    
    async def fill_schedules(self, start: str, end: str):
        """Заполняет атрибут schedules объектами графиков по ид специалиста"""
        specs = tuple(self.handler.specialists)
        schedules = await BitrixClient.get_specialists_schedules(start, end, specs)
        self.handler.schedules.clear()
        for raw_schedule in schedules:
            schedule = BXSchedule(**raw_schedule)
            schedules_of_spec = self.handler.schedules.get(schedule.specialist, None)
            if schedules_of_spec is None:
                schedules_of_spec = self.handler.schedules[schedule.specialist] = []
            schedules_of_spec.append(schedule)

    async def fill_appointments(self, start: str, end: str):
        """Заполняет атрибут appointments объектами занятий специалистов по ид специлалиста"""
        specs = tuple(self.handler.specialists)
        appointments = await BitrixClient.get_specialists_appointments(start, end, specs)
        self.handler.appointments.clear()
        for raw_appointment in appointments:
            appointment = BXAppointment(**raw_appointment)
            appointment_of_spec = self.handler.appointments.get(appointment.specialist, None)
            if appointment_of_spec is None:
                appointment_of_spec = self.handler.appointments[appointment.specialist] = []
            appointment_of_spec.append(appointment)
