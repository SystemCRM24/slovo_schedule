from fast_bitrix24 import BitrixAsync
import aiocache

from .settings import settings


BITRIX = BitrixAsync(settings.BITRIX_WEBHOOK)


async def get_deal_info(deal_id: str) -> dict:
    """Получает информацию о сделке"""
    response: dict = await BITRIX.call('crm.deal.get', {'id': deal_id}, raw=True)
    return response.get('result', {})


async def get_specialist_from_code(code: str):
    """Получает всех специалистов по указанному коду"""
    department_id: str = await get_department_id_by_code(code)
    params = {
        'filter': {
            'ACTIVE': True,
            'UF_DEPARTMENT': department_id
        }
    }
    response = await BITRIX.call('user.get', params, raw=True)
    print(response)


departments_cache = aiocache.cached(ttl=60 * 60 * 4, namespace='departments')

@departments_cache
async def get_department_id_by_code(code: str) -> str:
    """Отдает все подразделения"""
    response: dict = await BITRIX.call('department.get', {}, raw=True)
    departments: list[dict] = response.get('result', {})
    department_id = None
    for department in departments:
        if department['NAME'] == code:
            department_id = department['ID']
            break
    return department_id
