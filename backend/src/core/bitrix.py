from fast_bitrix24 import BitrixAsync
from aiocache import cached

from .settings import Settings


BITRIX = BitrixAsync(Settings.BITRIX_WEBHOOK, verbose=False)


class BitrixClient:

    @staticmethod
    async def call_batch(cmd: dict) -> dict:
        """Делает батч запрос"""
        return await BITRIX.call_batch(params={'halt': 0, 'cmd': cmd})
    
    @staticmethod
    async def delete_crm_item(entityTypeId: int, id: int) -> bool:
        """Удаляет элемент смарт-процесса"""
        items = {"entityTypeId": entityTypeId, "id": id}
        response = await BITRIX.call("crm.item.delete", items)
        return True
    
    @staticmethod
    async def get_crm_item(entityTypeId: int, id: int) -> dict | None:
        """Получает элемент смарт-процесса."""
        items = {"entityTypeId": entityTypeId, "id": id}
        response = await BITRIX.call("crm.item.get", items)
        return response

    @staticmethod
    async def get_all_departments() -> dict[str, dict]:
        """Выдает список всех подразделений"""
        response: dict = await BITRIX.call('department.get', {}, raw=True)
        departments: list[dict] = response.get('result', [])
        return {d['ID']: d for d in departments}
