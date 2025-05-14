from datetime import datetime

from app.settings import Settings
from app.schemas import RequestShema
from app import bitrix

from .specialist import Specialist


class Handler:
    """Обрабатывает то, что нужно обработать"""

    def __init__(self, data: RequestShema):
        self.initial_time = datetime.now(Settings.TIMEZONE)
        self.data = data
        self.specialists = self.create_specialists()
    
    def create_specialists(self) -> tuple[Specialist]:
        return tuple(Specialist(self.initial_time, d.type, d.quantity, d.duration) for d in self.data.data)

    async def run(self) -> str:
        """Запускает процесс постановки приема"""
        await self.update_specialists_info()
        # code_items = await self.get_listfield_values()
        # deal = await bitrix.get_deal_info(self.deal_id)
        # code = code_items.get(deal.get(UserFields.code, ''))
        # duration = self.get_appointment_duration(deal)
        # specs = await bitrix.get_specialist_from_code(code)
        # schedules = await self.get_specs_schedules(specs, duration)
        # sorted_schedules = sorted(
        #     filter(lambda s: s.last_find != None, schedules),
        #     key=lambda s: s.last_find
        # )
        # if not sorted_schedules:
        #     return
        # first = sorted_schedules[0]
        # await self.create_appointment(deal, first)
    
    async def update_specialists_info(self):
        """Обновляет инфу для возможных специалистов"""
        departments = await bitrix.get_all_departments()
        batches = tuple(s.get_specialists_info_batch(departments) for s in self.specialists)
        cmd = {index: value for index, value in enumerate(batches)}
        response = await bitrix.call_batch(cmd)
        for index, specs in enumerate(self.specialists):
            specs.possible_specs = response[index]
    
    # async def update_specialists_schedules(self):
        

    # async def get_listfield_values(self) -> dict:
    #     """Возвращает словарь, где ключи - id полей, а значения - значения"""
    #     fields = await bitrix.get_deal_field_values()
    #     codes = fields.get(UserFields.code, {}).get('items', [])
    #     return {c.get('ID', None): c.get('VALUE', None) for c in codes}

    # async def get_specs_schedules(self, specs: list, duration: int | None) -> list[Specialist]:
    #     """Получает рабочие графики и расписания приемов специалистов"""
    #     cmd = {}
    #     date_start = self.initial_time.replace(hour=0, minute=0, second=0, microsecond=0)
    #     date_start_iso = date_start.isoformat()
    #     for index, specialist in enumerate(specs):
    #         index *= 2
    #         spec_id = specialist.get('ID', '0')
    #         batch = BatchBuilder('crm.item.list')
    #         batch.params = {
    #             'entityTypeId': 1042,       # для получения графика работы специалиста
    #             'filter': {
    #                 '>=ufCrm4Date': date_start_iso,
    #                 'assignedById': spec_id
    #             },
    #             'order': {'ufCrm4Date': 'ASC'}
    #         }
    #         cmd[index] = batch.build()
    #         batch.params = {
    #             'entityTypeId': 1036,       # Для получения расписания занятий
    #             'filter': {
    #                 '>=ufCrm3StartDate': date_start_iso,
    #                 'assignedById': spec_id                    
    #             },
    #             'order': {'ufCrm3StartDate': 'ASC'}
    #         }
    #         cmd[index + 1] = batch.build()
    #     response: list = await bitrix.call_batch(cmd)
    #     result = []
    #     for i in range(0, len(response), 2):
    #         specialist = specs[i // 2]
    #         spec_id = specialist.get('ID', '0')
    #         result.append(Specialist(
    #             spec_id,
    #             schedule=response[i]['items'],
    #             appointments=response[i+1]['items'],
    #             duration=duration,
    #             now=self.initial_time
    #         ))
    #     return result

    # @staticmethod
    # def get_appointment_duration(deal: dict) -> int | None:
    #     """Получает из сделки продолжительность приема"""
    #     duration = deal.get('UF_CRM_1746625717138', '')
    #     try:
    #         return int(duration)
    #     except:
    #         return None

    # async def create_appointment(self, deal: dict, schedule: Specialist):
    #     """Создает занятие"""
    #     result = await bitrix.create_appointment({
    #         'ASSIGNED_BY_ID': schedule.specialist_id,
    #         'ufCrm3Children': 170,
    #         'ufCrm3StartDate': schedule.last_find.start.isoformat(),
    #         'ufCrm3EndDate': schedule.last_find.end.isoformat(),
    #         'ufCrm3Code': '55',
    #         'ufCrm3Status': 50
    #     })
    #     return result.get('item', None)
