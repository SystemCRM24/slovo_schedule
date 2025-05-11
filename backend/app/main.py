from datetime import datetime

from .utils import BatchBuilder
from .settings import settings, UserFields
from . import bitrix


class SpecialistSchedule:
    """Класс для работы с графиком и расписанием занятий специалиста"""

    def __init__(self, specialist_id, schedules, appointments):
        self.specialist_id = specialist_id
        self.schedules = schedules,
        self.appointments = appointments
        self.last_find = None

    def find(self, duration: int):
        """Ищет подходящее время для занятия"""



class Handler:
    """Обрабатывает то, что нужно обработать"""

    def __init__(self, deal_id: str, user_id: str):
        self.deal_id = deal_id
        self.user_id = user_id
        self.date = datetime.now(settings.TIMEZONE)

    async def run(self) -> str:
        """Запускает процесс постановки приема"""
        code_items = await self.get_listfield_values()
        deal = await bitrix.get_deal_info(self.deal_id)
        code = code_items.get(deal.get(UserFields.code, ''))
        specs = await bitrix.get_specialist_from_code(code)
        schedules = await self.get_specs_schedules(specs)
        for schedule in schedules:
            schedule.find(0)
        schedules.sort(key=lambda s: s.last_find)
        print(schedules)

    async def get_listfield_values(self) -> dict:
        """Возвращает словарь, где ключи - id полей, а значения - значения"""
        fields = await bitrix.get_deal_field_values()
        codes = fields.get(UserFields.code, {}).get('items', [])
        return {c.get('ID', None): c.get('VALUE', None) for c in codes}

    async def get_specs_schedules(self, specs: list) -> list[SpecialistSchedule]:
        """Получает рабочие графики и расписания приемов специалистов"""
        cmd = {}
        date_start = self.date.replace(hour=0, minute=0, second=0, microsecond=0)
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
                }
            }
            cmd[index] = batch.build()
            batch.params = {
                'entityTypeId': 1036,       # Для получения расписания занятий
                'filter': {
                    '>=ufCrm3StartDate': date_start_iso,
                    'assignedById': spec_id                    
                }
            }
            cmd[index + 1] = batch.build()
        response: list = await bitrix.call_batch(cmd)
        result = []
        for i in range(0, len(response), 2):
            specialist = specs[i // 2]
            spec_id = specialist.get('ID', '0')
            result.append(SpecialistSchedule(
                spec_id,
                schedules=response[i]['items'],
                appointments=response[i+1]['items']
            ))
        return result
