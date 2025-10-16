from typing import Iterable
from fast_bitrix24 import BitrixAsync
from aiocache import cached

from .settings import Settings
from .bxconstants import BXConstants
from src.schemas.api import BXSpecialist
from src.utils import BatchBuilder


BITRIX = BitrixAsync(Settings.BITRIX_WEBHOOK, verbose=False)


class BitrixClient:
    BATCH_SIZE = 50

    # Методы для приложения
    @staticmethod
    async def get_crm_item_fields(entityTypeId: int) -> dict:
        """Получает значения полей элемента црм"""
        params = {"entityTypeId": entityTypeId}
        return await BITRIX.get_all('crm.item.fields', params)

    @staticmethod
    async def call_batch(cmd: dict) -> dict:
        """Делает батч запрос"""
        if len(cmd) <= BitrixClient.BATCH_SIZE:
            return await BITRIX.call_batch(params={'halt': 0, 'cmd': cmd})
        requests = []
        dct = {}
        for i, k in enumerate(cmd):
            if i > 0 and i % BitrixClient.BATCH_SIZE == 0:
                requests.append(dct)
                dct = {}
            dct[k] = cmd[k]
        if dct:
            requests.append(dct)
        list_result, dict_result = [], {}
        for request in requests:
            middle_result = await BITRIX.call_batch({'halt': 0, 'cmd': request})
            if isinstance(middle_result, list):
                list_result.extend(middle_result)
            if isinstance(middle_result, dict):
                dict_result |= middle_result
        return list_result if list_result else dict_result

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
    
    @staticmethod
    def get_comment_request_params(appointment_id) -> dict:
        return {
            "filter": {"ENTITY_TYPE": "DYNAMIC_1036", "ENTITY_ID": appointment_id},
            "order": {"ID": "DESC"}
        }

    # Методы для rollback'а занятий
    @staticmethod
    async def get_comments_list(appointment_id) -> list[dict]:
        """Получает список комментариев к занятию"""
        items = BitrixClient.get_comment_request_params(appointment_id)
        result: dict = await BITRIX.call('crm.timeline.comment.list', items, raw=True)
        return result.get('result', [])
    
    @staticmethod
    async def get_comments_from_appointments(apps):
        batches = {}
        builder = BatchBuilder('crm.timeline.comment.list')
        for i, id in enumerate(apps):
            builder.params = BitrixClient.get_comment_request_params(id)
            batches[i] = builder.build()
        return await BitrixClient.call_batch(batches)
    
    @staticmethod
    async def delete_comment(comment: dict):
        """Удаляет комментарий из таймлайна смарт-процесса"""
        # {'ID': '21374', 'ENTITY_ID': 1607, 'ENTITY_TYPE': 'dynamic_1036'}
        params = {
            'id': comment.get('ID'),
            'ownerId': comment.get('ENTITY_ID'),
            'ownerTypeId': 1036
        }
        return await BITRIX.call("crm.timeline.comment.delete", params)


    # Методы для фронта
    @staticmethod
    async def get_all_specialist() -> list[BXSpecialist]:
        params = {
            '@UF_DEPARTMENT': list(BXConstants.departments.keys()),
            'ACTIVE': 'Y',
            'SORT': 'UF_USR_1750081359137',
            'ORDER': 'asc'
        }
        result = await BITRIX.call('user.get', params, raw=True)
        return [BXSpecialist.model_validate(s) for s in result['result']]
    
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
    async def get_deal_info_universal(id: int) -> dict:
        items = {'entityTypeId': 2, 'id': id}
        response = await BITRIX.call('crm.item.get', items=items, raw=True)
        return response.get('result', {}).get('item', {})

    @staticmethod
    async def get_specialists_by_department(names: Iterable) -> list[dict[str, str]]:
        ids = [BXConstants.department_ids.get(n, '0') for n in names]
        params = {'@UF_DEPARTMENT': ids, 'ACTIVE': 'Y'}
        return await BITRIX.get_all('user.get', params)
    
    @staticmethod
    async def get_specialists_schedules(start, end, spec_ids) -> list[dict]:
        params = {
            "entityTypeId": BXConstants.schedule.entityTypeId,
            'filter': {
                f"@{BXConstants.schedule.uf.specialist}": list(spec_ids),
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
                f"@{BXConstants.appointment.uf.specialist}": list(spec_ids),
                f">={BXConstants.appointment.uf.start}": start,
                f"<={BXConstants.appointment.uf.end}": end,
            }
        }
        return await BITRIX.get_all("crm.item.list", params)
    
    @staticmethod
    async def fill_comment(*sp_ids):
        """Запускает бизнес-процесс для указанных элементов смарт-процесса - расписания"""
        for sp_id in sp_ids:
            await BitrixClient.run_business_porcess(60, sp_id)
    
    @staticmethod
    async def run_abonnement_control(*sp_ids):
        """Запускает бизнес-процесс для контроля списаний с абонемента."""
        for sp_id in sp_ids:
            await BitrixClient.run_business_porcess(57, sp_id)
    
    @staticmethod
    async def run_business_porcess(bp_id, sp_id):
        docs = [
            'crm',
            'Bitrix\\Crm\\Integration\\BizProc\\Document\\Dynamic',
            f'DYNAMIC_{BXConstants.appointment.entityTypeId}_{sp_id}'
        ]
        params = {'TEMPLATE_ID': bp_id, 'DOCUMENT_ID': docs}
        return await BITRIX.call('bizproc.workflow.start', params)

    @staticmethod
    async def add_comment_to_deal(deal_id: int, comment: str):
        """Добавляет коммантарий к сделке"""
        items = {
            'fields': {
                'ENTITY_ID': deal_id,
                'ENTITY_TYPE': 'deal',
                'COMMENT': comment
            }
        }
        return await BITRIX.call('crm.timeline.comment.add', items)
