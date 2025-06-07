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
            'ACTIVE': 'Y'
        }
        return await BITRIX.get_all('user.get', params)
    
    @staticmethod
    async def get_all_clients() -> list[dict]:
        params = {
            "select": ["ID", "NAME", "LAST_NAME"],
            "filter": {"TYPE_ID": "CLIENT"},
        }
        return await BITRIX.get_all("crm.contact.list", params)

    @staticmethod
    async def get_all_departments() -> dict[str, dict]:
        """Выдает список всех подразделений"""
        response: dict = await BITRIX.call('department.get', {}, raw=True)
        departments: list[dict] = response.get('result', [])
        return {d['ID']: d for d in departments}
