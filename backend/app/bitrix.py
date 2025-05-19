from fast_bitrix24 import BitrixAsync
from aiocache import cached

from .settings import Settings


BITRIX = BitrixAsync(Settings.BITRIX_WEBHOOK, verbose=False)


async def call_batch(cmd: dict) -> dict:
    """Делает батч запрос"""
    return await BITRIX.call_batch(params={'halt': 0, 'cmd': cmd})


departments_cache = cached(ttl=60 * 60 * 4, namespace='departments')
@departments_cache
async def get_all_departments() -> dict[str, dict]:
    """Выдает список всех подразделений"""
    response: dict = await BITRIX.call('department.get', {}, raw=True)
    departments: list[dict] = response.get('result', [])
    return {d['ID']: d for d in departments}



# async def get_deal_info(deal_id: str) -> dict:
#     """Получает информацию о сделке"""
#     response: dict = await BITRIX.call('crm.deal.get', {'id': deal_id}, raw=True)
#     return response.get('result', {})



# async def get_specialist_from_code(code: str) -> list:
#     """Получает всех специалистов по указанному коду"""
#     department_id: str = await get_department_id_by_code(code)
#     params = {
#         'filter': {
#             'ACTIVE': True,
#             'UF_DEPARTMENT': department_id
#         }
#     }
#     response = await BITRIX.call('user.get', params, raw=True)
#     return response.get('result', [])


# async def get_department_id_by_code(code: str) -> str:
#     """Отдает все подразделения"""
#     response: dict = await BITRIX.call('department.get', {}, raw=True)
#     departments: list[dict] = response.get('result', {})
#     department_id = None
#     for department in departments:
#         if department['NAME'] == code:
#             department_id = department['ID']
#             break
#     return department_id


# async def get_deal_field_values() -> dict:
#     """Получает значения полей"""
#     response = await BITRIX.call('crm.deal.fields', raw=True)
#     return response.get('result', {})


# async def create_appointment(fields: dict):
#     response = await BITRIX.call(
#         'crm.item.add',
#         {'entityTypeId': 1036, 'fields': fields},
#         raw=True
#     )
#     return response.get('result', None)



