from typing import Iterable
from fast_bitrix24 import BitrixAsync
# from aiocache import cached

from .settings import Settings
from .bxconstants import BXConstants


BITRIX = BitrixAsync(Settings.BITRIX_WEBHOOK, verbose=False)


class BitrixClient:

    # Методы для приложения
    @staticmethod
    async def get_crm_item_fields(entityTypeId: int) -> dict:
        """Получает значения полей элемента црм"""
        params = {"entityTypeId": entityTypeId}
        return await BITRIX.get_all('crm.item.fields', params)

    @staticmethod
    async def call_batch(cmd: dict) -> dict:
        """Делает батч запрос"""
        return await BITRIX.call_batch(params={'halt': 0, 'cmd': cmd})


    # Методы для CRUD-функционала
    @staticmethod
    async def create_crm_item(entityTypeId: int, fields: dict) -> dict:
        items = {"entityTypeId": entityTypeId, "fields": fields}
        return await BITRIX.call('crm.item.add', items)
    
    @staticmethod
    async def delete_crm_item(entityTypeId: int, id: int) -> bool:
        """Удаляет элемент смарт-процесса"""
        items = {"entityTypeId": entityTypeId, "id": id}
        try:
            await BITRIX.call("crm.item.delete", items)
            return True
        except:
            return False
    
    @staticmethod
    async def get_crm_item(entityTypeId: int, id: int) -> dict | None:
        """Получает элемент смарт-процесса."""
        items = {"entityTypeId": entityTypeId, "id": id}
        return await BITRIX.call("crm.item.get", items)
    
    @staticmethod
    async def update_crm_item(entityTypeId: int, id: int, fields: dict) -> dict:
        items = {"entityTypeId": entityTypeId, "id": id, "fields": fields}
        return await BITRIX.call('crm.item.update', items)


    # Методы для фронта
    @staticmethod
    async def get_all_specialist() -> list[dict]:
        params = {
            '@UF_DEPARTMENT': list(BXConstants.departments.keys()),
            'ACTIVE': 'Y',
            'SORT': 'UF_USR_1750081359137',
            'ORDER': 'asc'
        }
        result = BITRIX.call('user.get', params, raw=True)
        return await result['result']
    
    @staticmethod
    async def get_all_clients() -> list[dict]:
        params = {
            "select": ["ID", "NAME", "LAST_NAME"],
            "filter": {"TYPE_ID": "CLIENT"},
        }
        return await BITRIX.get_all("crm.contact.list", params)
    
    @staticmethod
    async def get_all_appointments(start: str, end: str) -> list[dict]:
        params = {
            "entityTypeId": BXConstants.appointment.entityTypeId,
            "filter": {
                f">={BXConstants.appointment.uf.start}": start,
                f"<={BXConstants.appointment.uf.end}": end,
            }
        }
        return await BITRIX.get_all("crm.item.list", params)
    
    @staticmethod
    async def get_all_schedules(start: str, end: str) -> list[dict]:
        params = {
            "entityTypeId": BXConstants.schedule.entityTypeId,
            "filter": {
                f">={BXConstants.schedule.uf.date}": start,
                f"<={BXConstants.schedule.uf.date}": end,
            }
        }
        return await BITRIX.get_all("crm.item.list", params)

    
    # Методы для AppointPlan
    @staticmethod
    async def get_deal_info(id: int) -> dict:
        response = await BITRIX.call('crm.deal.get', {'id': id}, raw=True)
        return response.get('result')

    @staticmethod
    async def get_specialists_by_department(names: Iterable) -> list[dict]:
        ids = [BXConstants.department_ids.get(n, '0') for n in names]
        params = {'@UF_DEPARTMENT': ids, 'ACTIVE': 'Y'}
        return await BITRIX.get_all('user.get', params)
    
    @staticmethod
    async def get_specialists_schedules(start, end, spec_ids) -> list[dict]:
        params = {
            "entityTypeId": BXConstants.schedule.entityTypeId,
            'filter': {
                f"@{BXConstants.schedule.uf.specialist}": spec_ids,
                f">={BXConstants.schedule.uf.date}": start,
                f"<={BXConstants.schedule.uf.date}": end,
            }
        }
        return await BITRIX.get_all("crm.item.list", params)
    
    @staticmethod
    async def get_specialists_appointments(start, end, spec_ids) -> list[dict]:
        params = {
            "entityTypeId": BXConstants.appointment.entityTypeId,
            'filter': {
                f"@{BXConstants.appointment.uf.specialist}": spec_ids,
                f">={BXConstants.appointment.uf.start}": start,
                f"<={BXConstants.appointment.uf.end}": end,
            }
        }
        return await BITRIX.get_all("crm.item.list", params)
