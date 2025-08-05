import asyncio
from datetime import datetime, timedelta

from src.utils import BatchBuilder
from src.core import Settings, BXConstants, BitrixClient
from src.schemas.repetative import RequestSchema
from src.schemas.appointplan import BXSchedule
from src.schemas.api import BXClient


class Handler:

    def __init__(self, request: str) -> None:
        self.request = request
        self.data: RequestSchema = None                             # type:ignore
        self.patient = BXClient(ID=Settings.DEFAULT_USER, NAME='СпецСистема', LAST_NAME="Интегратор")   # type:ignore
        self.schedules: list[BXSchedule] = []
        self.users = [Settings.DEFAULT_USER]
        self.repetatives: list[dict] = []
        self.messages = []
    
    async def run(self):
        context = Context(self)
        try:
            await context.fill()
            self.create_repetatives()
        except Exception as e:
            self.repetatives.clear()
            self.messages.append(str(e))
        t = asyncio.create_task(self.send_message())
        asyncio.create_task(self.send_comment())
        return await self.send_appointments()

    def create_repetatives(self):
        """Создает повторяющиеся занятия"""
        repetative_qty = self.data.qty
        hour, minute = self.data.time
        for schedule in self.schedules:
            for interval in schedule.intervals:
                if interval.start.weekday() != self.data.weekday:
                    continue
                start = interval.start.replace(hour=hour, minute=minute, second=0, microsecond=0)
                end = start + timedelta(minutes=self.data.duration)
                if start in interval and end in interval:
                    appointment = self.build_appointment(start, end)
                    self.repetatives.append(appointment)
                    repetative_qty -= 1
        if repetative_qty > 0 or repetative_qty == -1:
            self.messages.append(f'{repetative_qty} занятий не было проставлено в расписание.')
    
    def build_appointment(self, start: datetime, end: datetime) -> dict:
        code = BXConstants.appointment.lfv.idByCode.get(self.data.code, None)
        return {
            'assignedById': self.data.specialist_id,
            'ufCrm3Code': [code],
            'ufCrm3StartDate': start.isoformat(),
            'ufCrm3EndDate': end.isoformat(),
            'ufCrm3Children': self.patient.id,
            'ufCrm3Dealid': str(self.data.deal_id),
            'ufCrm3Status': 2150
        }
    
    async def send_message(self):
        """Посылает сообщение пользователю в битру"""
        for appointment in self.repetatives:
            self.messages.append(f'Занятие запланировано: {appointment.get('ufCrm3StartDate', '')}')
        message = '\n'.join(self.messages)
        batches = {}
        for index, user in enumerate(self.users):
            batch = BatchBuilder(
                'im.notify.personal.add',
                {'USER_ID': user, 'MESSAGE': message}
            )
            batches[index] = batch.build()
        await BitrixClient.call_batch(batches)
    
    async def send_appointments(self):
        """Посылает батч-запрос на расстановку занятий в битру."""
        batches = {}
        for index, appointment in enumerate(self.repetatives):
            batch = BatchBuilder(
                'crm.item.add',
                {'entityTypeId': BXConstants.appointment.entityTypeId, 'fields': appointment}
            )
            batches[index] = batch.build()
        return await BitrixClient.call_batch(batches)
    
    async def send_comment(self):
        """Создает коммент к сделке"""
        if not self.repetatives:
            return
        specialists = await BitrixClient.get_all_specialist()
        specialist = str(self.data.specialist_id)
        for spec in specialists:
            if spec.get('ID', '0') == specialist:
                specialist = spec
                break
        spec_fio = specialist.get('LAST_NAME', '') + ' ' + specialist.get('NAME', '')[0]    # type:ignore
        template = f"[*] {spec_fio} - {self.patient.full_name}, {self.data.code}, " + "{0}, {1} минут."

        def iterator():
            for app in self.repetatives:
                date = datetime.fromisoformat(app.get('ufCrm3StartDate', ''))
                duration = datetime.fromisoformat(app.get('ufCrm3EndDate', '')) - date
                date = date.strftime(r'%d.%m.%Y %H:%M')         #type:ignore
                duration = int(duration.total_seconds() // 60)  #type:ignore
                yield template.format(date, duration)
    
        comment = f'Добавлены занятия:\n[list=1]{'\n'.join(iterator())}[/list]'
        return await BitrixClient.add_comment_to_deal(self.data.deal_id, comment)


class Context:

    __slots__ = ('handler', )

    def __init__(self, handler: Handler) -> None:
        self.handler = handler

    async def fill(self):
        self.handler.data = RequestSchema.model_validate_json(self.handler.request)
        start = self.handler.data.start_date.replace(hour=0, minute=0)
        start_iso = start.isoformat()
        end = start + timedelta(days=365*10)
        end_iso = end.isoformat()
        await asyncio.gather(
            self.fill_schedules(start_iso, end_iso),
            self.fill_patient()
        )
        self.handler.users.append(self.handler.data.user_id)
    
    async def fill_schedules(self, start: str, end: str):
        """Заполняет атрибут schedules объектами графиков по ид специалиста"""
        specs = (self.handler.data.specialist_id, )
        schedules = await BitrixClient.get_specialists_schedules(start, end, specs)
        self.handler.schedules.clear()
        for raw_schedule in schedules:
            schedule = BXSchedule.model_validate(raw_schedule)
            self.handler.schedules.append(schedule)
        self.handler.schedules.sort(key=lambda s: s.date)   # type:ignore

    async def fill_patient(self):
        """Получает из сделки информацию по пациенту"""
        deal = await BitrixClient.get_deal_info(self.handler.data.deal_id)
        clients = await BitrixClient.get_all_clients()
        patient = deal.get('CONTACT_ID', None)
        if patient:
            for client in clients:
                if client.get('ID', None) == patient:
                    self.handler.patient = BXClient.model_validate(client)
                    return
        raise Exception('В сделке не установлен клиент или у клиента неподходящий тип')
